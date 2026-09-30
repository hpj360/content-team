"""LLM-as-judge 评议器（创作者视角 Round 11 · A3）。

与 `gates`（确定性断言，门禁）互补：judge 只看**语义质量**（钩子强度、场景
价值转折、台词个性、节奏），产出**建议**而非门禁——避免主观指标被古德哈特化。

rubric 取自媒体技能文档的验收要点；judge 结果通过 ``StageCritic`` 注入，
记入 ``stage_results[].critic_notes``，由人工/编导消化。
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from hermes.content_team.models.creative import CreationStage

# stage → rubric（取自 showrunning/acceptance-checklists 的语义项）
RUBRICS: dict[CreationStage, list[str]] = {
    CreationStage.NOVEL: [
        "前 500 字是否同时出现主角与冲突/卖点",
        "本卷是否形成完整的欠—还情绪闭环",
        "章尾钩子是否让人产生追读冲动",
    ],
    CreationStage.SCRIPT: [
        "每场是否发生价值转折（进场价值≠出场价值）",
        "台词是否性格化、是否藏住潜台词",
        "对手是否有明确动机与威胁",
    ],
    CreationStage.STORYBOARD: [
        "每镜是否能回答「观众此刻比一秒前多懂了什么」",
        "景别递进与运镜是否服务情绪，而非装饰",
        "是否有越轴/跳切风险",
    ],
    CreationStage.DIRECTING: [
        "风格是否真的改变了镜头（机制层面，而非贴标签）",
        "表演指导是否为可执行的外部动作",
        "节奏策略是否覆盖情绪曲线",
    ],
}

_JUDGE_SYSTEM = (
    "你是创作质量评议员（非门禁）。针对给定 rubric 逐条评议，"
    '返回 JSON：{"notes": ["…"], "score": 0-100, "verdict": "PASS|REVISE"}。'
    "只输出 JSON，不要复述原文。"
)


def make_llm_judge(
    client: Any,
    *,
    rubrics: dict[CreationStage, list[str]] | None = None,
    max_notes: int = 8,
):
    """构造 judge（形如 StageCritic）：(stage, output, ctx) -> list[str] 建议。"""
    table = RUBRICS if rubrics is None else rubrics

    async def judge(
        stage: CreationStage, output: dict[str, Any], ctx: dict[str, Any]
    ) -> list[str]:
        from hermes.workbench.llm import LlmMessage

        rubric = table.get(stage)
        if not rubric:
            return []
        # 评议必须看到**内容**：优先产物 preview，其次草稿/正文
        content = str(output.get("preview") or "").strip()
        if not content:
            draft = ctx.get("draft") or {}
            content = str(draft.get("body") or "").strip()
        if not content:
            body = output.get("script_body") or output.get("chapter_body")
            content = str(body or "").strip()
        payload = {
            "stage": stage.value,
            "rubric": rubric,
            "content": content[:1500] or "（未提供正文）",
        }
        messages = [
            LlmMessage(role="system", content=_JUDGE_SYSTEM),
            LlmMessage(
                role="user",
                content=json.dumps(payload, ensure_ascii=False),
            ),
        ]
        try:
            data = await asyncio.to_thread(_judge_call, client, messages)
        except Exception:  # noqa: BLE001
            return []
        if not isinstance(data, dict):
            return []
        notes = data.get("notes")
        if not isinstance(notes, list):
            return []
        clean = [str(n).strip() for n in notes if str(n).strip()]
        score = data.get("score")
        verdict = data.get("verdict")
        if score is not None or verdict:
            clean.append(f"[judge] score={score} verdict={verdict}")
        return clean[:max_notes]

    return judge


def judge_report(notes: list[str]) -> dict[str, Any]:
    """把 judge 建议整理为报告片段（供 artifacts 留痕）。"""
    return {"judge_notes": list(notes), "count": len(notes)}


# ---------------------------------------------------------------------------
# 默认清单评议器（R17）：规则版 critic，零成本，产出可执行建议（不门禁）
# ---------------------------------------------------------------------------

_DIALOGUE_RE = re.compile(r"^\[?[^，。！？\n]{1,12}\]?$", re.MULTILINE)


def make_checklist_critic(max_notes: int = 5):
    """默认 critic：按可测量指标给出写作建议（不门禁）。

    - 对话行占比过低 → 建议增加对话推进；
    - 场景数偏少 → 建议拆场；
    - 平均句长过长 → 建议短句提速；
    - 缺少钩子词 → 建议强化章尾钩子。
    """

    async def critic(
        stage: CreationStage, output: dict[str, Any], ctx: dict[str, Any]
    ) -> list[str]:
        content = str(output.get("preview") or "").strip()
        if not content:
            draft = ctx.get("draft") or {}
            content = str(draft.get("body") or "").strip()
        if not content:
            return []

        notes: list[str] = []

        lines = [ln for ln in content.splitlines() if ln.strip()]
        dialogue_lines = len(_DIALOGUE_RE.findall("\n".join(lines)))
        dialogue_ratio = dialogue_lines / max(1, len(lines))
        if dialogue_ratio < 0.2:
            notes.append(
                f"[critic] 对话行占比 {dialogue_ratio:.0%} 偏低，建议增加对话推进"
            )

        sentences = [
            s for s in re.split(r"[。！？!?…]+", content) if s.strip()
        ]
        avg_len = (sum(len(s) for s in sentences) / len(sentences)) if sentences else 0
        if avg_len > 40:
            notes.append(f"[critic] 平均句长 {avg_len:.0f} 字偏长，建议短句提速")

        scenes = len(
            [ln for ln in lines if ln.strip().startswith(("第", "INT.", "EXT.", "内景", "外景"))]
        )
        if scenes and scenes < 3:
            notes.append(f"[critic] 场景数 {scenes} 偏少，建议按节拍拆场")

        if not any(token in content for token in ("？", "……", "!", "！")):
            notes.append("[critic] 未见悬念/钩子标志（问号、省略号），建议强化章尾钩子")

        return notes[:max_notes]

    return critic


def _judge_call(client: Any, messages: list[Any]) -> dict[str, Any]:
    """稳健调用（实网联调产出：显式 max_tokens + 截断修复）。"""
    from hermes.content_team.creative.llm_io import chat_json_safe

    return chat_json_safe(client, messages, max_tokens=1024, retries=2, role="judge")
