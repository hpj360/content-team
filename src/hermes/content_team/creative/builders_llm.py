"""LLM 草稿生成器（创作者视角 Round 8 · A2'，注入点实现）。

定位「陪写」而非「代写」：LLM 只产出草稿文本，持久化、质检、去 AI 味出口
门仍由本项目的 builder/checker/reviser 三层负责。作者保留每一处否决权。

`make_llm_drafter(client, skills_root=...)` 返回 ``StageDrafter``：
- 载入该 stage 的 SKILL.md + 关键 references 作为 system prompt；
- user 负载含：选题、上游产物、A1 检索命中、文风指纹；
- 通过 workbench ``LlmClient.chat_json`` 调用（阻塞 → 线程下放）；
- 响应契约 ``{"title": str, "body": str}``；异常/非法 → 返回 {}（降级模板）。
"""
from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from hermes.content_team.creative.gates import AI_CLICHE_TOKENS
from hermes.content_team.creative.planners import RETRIEVAL_KEY
from hermes.content_team.creative.style_fingerprint import (
    fingerprint_to_prompt,
    StyleFingerprint,
)
from hermes.content_team.models.creative import CreationStage

StageDrafter = Callable[[CreationStage, dict[str, Any]], Awaitable[dict[str, Any]]]

# stage → 技能目录（提示词来源）
_SKILL_BY_STAGE = {
    CreationStage.NOVEL: "novel-writing",
    CreationStage.SCRIPT: "script-writing",
    CreationStage.STORYBOARD: "storyboarding",
    CreationStage.DIRECTING: "directing",
}

# stage → 优先加载的 reference（按需深化，其余不加载以控 token）
_REFERENCE_BY_STAGE = {
    CreationStage.NOVEL: "web-fiction-craft.md",
    CreationStage.SCRIPT: "short-drama-playbook.md",
    CreationStage.STORYBOARD: "storyboard-method.md",
    CreationStage.DIRECTING: "directing-craft.md",
}

_DEFAULT_SKILLS_ROOT = Path(__file__).resolve().parents[4] / "skills"

# 输出契约（追加在 SKILL.md 之后，优先级最高，避免模型照搬文档里的示例 schema）
_OUTPUT_CONTRACT = (
    "\n\n---\n\n"
    "## 输出契约（最高优先级，覆盖上文示例）\n"
    "你只输出一个 JSON 对象，且只含两个字段：\n"
    '{"title": "本段标题", "body": "完整正文纯文本"}\n'
    "- body 必须是可直接使用的正文纯文本（剧本要包含场次标题、动作与台词）；\n"
    "- 不要输出 scenes/characters/logline 等其它结构；不要输出解释或 markdown 围栏。"
)


def _load_skill_prompt(stage: CreationStage, skills_root: Path) -> str:
    """载入 SKILL.md（+ 一份 reference）作为 system prompt。"""
    skill_name = _SKILL_BY_STAGE.get(stage)
    if not skill_name:
        return ""
    base = skills_root / skill_name
    parts: list[str] = []
    skill_md = base / "SKILL.md"
    if skill_md.is_file():
        parts.append(skill_md.read_text(encoding="utf-8"))
    ref = _REFERENCE_BY_STAGE.get(stage)
    if ref:
        ref_path = base / "references" / ref
        if ref_path.is_file():
            parts.append(ref_path.read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(parts)


def _build_user_payload(
    stage: CreationStage, ctx: dict[str, Any]
) -> dict[str, Any]:
    """组装生成请求：只放必需字段，控制 token。"""
    topic = ctx.get("topic")
    payload: dict[str, Any] = {
        "stage": stage.value,
        "topic": {
            "title": str(getattr(topic, "title", "") or ""),
            "description": str(getattr(topic, "description", "") or ""),
        },
        "constraints": {
            "no_ai_cliche": list(AI_CLICHE_TOKENS),
            "output_schema": {"title": "str", "body": "str"},
        },
    }
    if stage is not CreationStage.NOVEL:
        payload["novel_title"] = ctx.get("novel_title") or ctx.get("script_title")
        payload["upstream"] = {
            k: v
            for k, v in ctx.items()
            if k.endswith("_id") and isinstance(v, (str, uuid.UUID))
        }
    hits = ctx.get(RETRIEVAL_KEY)
    if hits:
        payload["retrieval"] = [
            {"title": h.get("title"), "snippet": h.get("snippet")} for h in hits
        ]
    fp_raw = ctx.get("style_fingerprint")
    if isinstance(fp_raw, dict):
        fp = StyleFingerprint(**{
            k: v for k, v in fp_raw.items() if k in StyleFingerprint.__dataclass_fields__
        })
        prompt = fingerprint_to_prompt(fp)
        if prompt:
            payload["style_fingerprint"] = prompt
    return payload


def make_llm_drafter(
    client: Any,
    *,
    skills_root: Path | None = None,
) -> StageDrafter:
    """构造 LLM 草稿生成器（可注入 fake client 测试）。"""
    root = skills_root or _DEFAULT_SKILLS_ROOT

    async def drafter(
        stage: CreationStage, ctx: dict[str, Any]
    ) -> dict[str, Any]:
        from hermes.workbench.llm import LlmMessage

        system = _load_skill_prompt(stage, root)
        if not system:
            return {}
        messages = [
            LlmMessage(role="system", content=system + _OUTPUT_CONTRACT),
            LlmMessage(
                role="user",
                content=json.dumps(
                    _build_user_payload(stage, ctx), ensure_ascii=False
                ),
            ),
        ]
        try:
            data = await asyncio.to_thread(_chat_json_bounded, client, messages)
        except Exception:  # noqa: BLE001
            return {}
        return normalize_draft(data)

    return drafter


def normalize_draft(data: Any) -> dict[str, Any]:
    """把模型返回的多种 schema 归一化为 ``{title, body}``（生产稳健性）。

    兼容：
      1. 契约直出 ``{"title","body"}``；
      2. SKILL.md 文档式 ``{"scenes":[{slugline,action,dialogues}]}`` → 渲染正文；
      3. ``{"text"|"content"}`` 纯文本 → 直取。
    其余（或正文为空）返回 {}（触发模板降级）。
    """
    if not isinstance(data, dict):
        return {}
    title = str(data.get("title") or "").strip()
    body = str(data.get("body") or "").strip()
    if body:
        return {"title": title, "body": body, "drafter": "llm"}

    scenes = data.get("scenes")
    if isinstance(scenes, list) and scenes:
        rendered = _render_scenes(scenes)
        if rendered:
            return {
                "title": title or str(data.get("logline") or "").strip(),
                "body": rendered,
                "drafter": "llm",
                "adapted": "scenes",
            }

    text = str(data.get("text") or data.get("content") or "").strip()
    if text:
        return {"title": title, "body": text, "drafter": "llm", "adapted": "text"}
    return {}


def _render_scenes(scenes: list[Any]) -> str:
    """把文档式 scenes 结构渲染为场次文本（含人物/台词）。"""
    blocks: list[str] = []
    for idx, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            continue
        number = scene.get("scene_number") or idx
        slugline = str(scene.get("slugline") or "").strip() or "内景／日"
        purpose = str(scene.get("purpose") or "").strip()
        action = str(scene.get("action") or "").strip()
        lines = [f"第{number}场　{slugline}"]
        if purpose:
            lines.append(f"（{purpose}）")
        if action:
            lines.append("")
            lines.append(action)
        for dialogue in scene.get("dialogues") or []:
            if not isinstance(dialogue, dict):
                continue
            character = str(dialogue.get("character") or "").strip()
            line = str(dialogue.get("line") or "").strip()
            if character or line:
                lines.append("")
                lines.append(character)
                lines.append(line)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _chat_json_bounded(client: Any, messages: list[Any]) -> dict[str, Any]:
    """稳健调用（显式 max_tokens + 截断修复 + 扩容重试），失败返回 {}。"""
    from hermes.content_team.creative.llm_io import chat_json_safe

    return chat_json_safe(client, messages, max_tokens=2048, retries=3)


def make_script_drafter(
    client: Any, *, skills_root: Path | None = None
) -> StageDrafter:
    """便捷：仅对 SCRIPT 阶段启用 LLM 草稿（其余阶段走模板）。"""
    inner = make_llm_drafter(client, skills_root=skills_root)

    async def drafter(
        stage: CreationStage, ctx: dict[str, Any]
    ) -> dict[str, Any]:
        if stage is not CreationStage.SCRIPT:
            return {}
        return await inner(stage, ctx)

    return drafter


__all__ = [
    "StageDrafter",
    "make_llm_drafter",
    "make_script_drafter",
    "_build_user_payload",
    "_load_skill_prompt",
]
