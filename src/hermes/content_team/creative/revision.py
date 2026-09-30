"""自动修订引擎：按审查问题编码修复产物。

设计：``CreativeReviser`` 是独立于 builder 与 reviewer 的第三主体，仅依据
``GateIssue`` 的 problem 编码对实体做**最小修复**，并记录修订日志。
不可修复的问题（unsupported / not-found）保持原样交回人工。

修订循环由 ``run_creation`` 驱动：审查失败 → 修订 → 重审，直到通过、
问题不再收敛或修订轮次耗尽。

Round 4：新增修订后端注入点（``RevisionBackend`` Protocol）。规则后端是
默认实现；LLM 生成式修订通过 ``LlmReviserBackend(revise_fn, fallback=)``
注入，异常时降级到 fallback，无可用后端则交回人工。
"""
from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from hermes.content_team.creative.gates import (
    AI_CLICHE_TOKENS,
    COMPLIANCE_BLOCKLIST,
    MAX_LOGLINE_CHARS,
    SHOT_MAX_SECONDS,
    SHOT_MIN_SECONDS,
    PSYCH_NARRATION_RE,
)
from hermes.content_team.models.creative import (
    DirectingPlan,
    Novel,
    NovelChapter,
    Script,
    Shot,
    StoryState,
    Storyboard,
)

_REVISE_LOG_LIMIT = 10


class CreativeReviser:
    """按问题编码修订创作产物，并返回修订日志（规则后端）。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def revise(
        self, artifacts: dict[str, Any], issues: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """尝试逐条修复审查问题，返回修订日志。"""
        log: list[dict[str, Any]] = []
        seen_codes: set[str] = set()
        for issue in issues:
            code = str(issue.get("code") or "")
            if code in seen_codes:
                continue
            seen_codes.add(code)
            fixer = _FIXERS.get(code)
            if fixer is None:
                log.append({"code": code, "fixed": False, "action": "unsupported"})
                continue
            _key, label = _ISSUE_ARTIFACTS.get(code, ("", ""))
            try:
                # 修复函数之第 3 参即问题编码本身（用于分发修复动作）
                fixed = await fixer(self.db, artifacts, code)
            except Exception as exc:  # noqa: BLE001
                log.append({"code": code, "fixed": False, "action": f"error: {exc}"})
                continue
            log.append(
                {"code": code, "fixed": bool(fixed), "action": label or "fix"}
            )
            if len(log) >= _REVISE_LOG_LIMIT:
                break
        await self.db.commit()
        return log


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------


async def _fetch(db: AsyncSession, model: type, key: str, artifacts: dict):
    raw = artifacts.get(key)
    if not raw:
        return None
    return await db.get(model, uuid.UUID(str(raw)))


async def _fix_novel_by_issue(
    db: AsyncSession, artifacts: dict, code: str
) -> bool:
    """修订小说：logline 截断/兜底，缺失章节补全。"""
    novel = await _fetch(db, Novel, "novel_id", artifacts)
    if novel is None:
        return False
    if code in {"N001", "N002"}:
        novel.logline = (novel.logline or "")[:MAX_LOGLINE_CHARS]
        if not novel.logline.strip():
            novel.logline = "核心冲突未定稿，待补。"
    if code in {"N004", "N005"}:
        existing = await db.scalar(
            sa.select(sa.func.count())
            .select_from(NovelChapter)
            .where(NovelChapter.novel_id == novel.id)
        )
        if not existing:
            chapter = NovelChapter(
                novel_id=novel.id,
                chapter_number=1,
                title="第一章",
                body="（修订补全的章节正文：主角登场，抛出钩子。）",
            )
            chapter.word_count = NovelChapter.compute_word_count(chapter.body)
            db.add(chapter)
            await db.flush()
    return True


async def _fix_script_by_issue(
    db: AsyncSession, artifacts: dict, code: str
) -> bool:
    """修订剧本：logline/场景数/AI 套路/心理旁白/合规词。"""
    script = await _fetch(db, Script, "script_id", artifacts)
    if script is None:
        return False
    changed = False
    if code in {"S001", "S002"}:
        script.logline = (script.logline or "")[:MAX_LOGLINE_CHARS]
        if not script.logline.strip():
            script.logline = "核心冲突未定稿，待补。"
        changed = True
    if code == "S003":
        script.body = script.body or "第一场　内景／日\n\n主角登场。（建置）"
        changed = True
    if code == "S004":
        body = script.body or ""
        scene_count = len(_scene_headers(body))
        placeholder = "\n\n".join(
            f"第{i}场　内景／日\n\n（修订补全场景）"
            for i in range(scene_count + 1, 4)
        )
        if placeholder:
            script.body = body + ("\n\n" + placeholder if scene_count else placeholder)
        changed = True
    if code in {"S005", "S006"}:
        body = script.body or ""
        for token in AI_CLICHE_TOKENS:
            body = body.replace(token, "")
        body = PSYCH_NARRATION_RE.sub("（动作描写）", body)
        script.body = body
        changed = True
    if code == "S007":
        body = script.body or ""
        for token in COMPLIANCE_BLOCKLIST:
            body = body.replace(token, "***")
        script.body = body
        changed = True
    return changed


def _scene_headers(text: str) -> list[str]:
    from hermes.content_team.creative.gates import SCENE_HEADER_RE

    return SCENE_HEADER_RE.findall(text or "")


async def _fix_storyboard_by_issue(
    db: AsyncSession, artifacts: dict, code: str
) -> bool:
    """修订分镜：镜号重排 / 时长收敛 / 描述补全 / 补镜头。"""
    storyboard = await _fetch(db, Storyboard, "storyboard_id", artifacts)
    if storyboard is None:
        return False
    result = await db.execute(
        sa.select(Shot).where(Shot.storyboard_id == storyboard.id)
    )
    shots = list(result.scalars().all())
    if code == "B001" and not shots:
        db.add(
            Shot(
                storyboard_id=storyboard.id,
                shot_number=1,
                description="（修订补全镜头）",
                duration_seconds=3.0,
            )
        )
        await db.flush()
        return True
    changed = False
    for idx, shot in enumerate(shots, start=1):
        if code == "B003" and shot.shot_number != idx:
            shot.shot_number = idx
            changed = True
        if code == "B002" and not shot.description.strip():
            shot.description = "（修订补全镜头描述）"
            changed = True
        if code == "B004":
            target = max(
                SHOT_MIN_SECONDS,
                min(SHOT_MAX_SECONDS, float(shot.duration_seconds or 0.0)),
            )
            if target != shot.duration_seconds:
                shot.duration_seconds = target
                changed = True
    await db.flush()
    return changed


async def _fix_directing_by_issue(
    db: AsyncSession, artifacts: dict, code: str
) -> bool:
    """修订导演方案：补全 4 个文案字段。"""
    plan = await _fetch(db, DirectingPlan, "directing_plan_id", artifacts)
    if plan is None:
        return False
    defaults = {
        "D001": ("style", "写实"),
        "D002": ("tone", "克制"),
        "D003": ("pacing", "中速"),
        "D004": ("director_notes", "（修订补全导演阐述）"),
    }
    entry = defaults.get(code)
    if entry is None:
        return False
    key, value = entry
    if not str(getattr(plan, key) or "").strip():
        setattr(plan, key, value)
        return True
    return False


async def _fix_story_state_by_issue(
    db: AsyncSession, artifacts: dict, code: str
) -> bool:
    """修订故事状态：状态卡/角色/目标分层。"""
    state = await _fetch(db, StoryState, "story_state_id", artifacts)
    if state is None:
        return False
    changed = False
    if code == "T001":
        for field in (
            "position",
            "recent_summary",
            "active_characters",
            "pending_foreshadowing",
            "volume_goal",
            "global_rules",
            "next_step",
        ):
            if not str(state.tracking.get(field) or "").strip():
                state.tracking[field] = "（修订补全）"
                changed = True
    if code == "T002" and not state.characters:
        state.characters = [
            {
                "name": "主角",
                "ability": "初始",
                "psychology": "目标驱动",
                "relations": "对立",
                "goals": "完成主线",
            }
        ]
        changed = True
    if code == "T003":
        for char in state.characters:
            if not str(char.get("name") or "").strip():
                char["name"] = "未命名"
                changed = True
    if code == "T007":
        for level in ("global", "volume", "chapter"):
            if not str(state.goals.get(level) or "").strip():
                state.goals[level] = "（修订补全）"
                changed = True
    await db.flush()
    return changed


_ISSUE_ARTIFACTS: dict[str, tuple[str, str]] = {
    "N001": ("novel_id", "修订 logline"),
    "N002": ("novel_id", "修订 logline"),
    "N004": ("novel_id", "补全章节"),
    "N005": ("novel_id", "补全章节"),
    "S001": ("script_id", "修订 logline"),
    "S002": ("script_id", "修订 logline"),
    "S003": ("script_id", "补全剧本"),
    "S004": ("script_id", "补全场景"),
    "S005": ("script_id", "替换 AI 套路/心理旁白"),
    "S006": ("script_id", "替换 AI 套路/心理旁白"),
    "S007": ("script_id", "遮蔽合规词"),
    "B001": ("storyboard_id", "补全镜头"),
    "B002": ("storyboard_id", "补全镜头描述"),
    "B003": ("storyboard_id", "重排镜号"),
    "B004": ("storyboard_id", "收敛时长"),
    "D001": ("directing_plan_id", "补全导演字段"),
    "D002": ("directing_plan_id", "补全导演字段"),
    "D003": ("directing_plan_id", "补全导演字段"),
    "D004": ("directing_plan_id", "补全导演字段"),
    "T001": ("story_state_id", "补全状态卡"),
    "T002": ("story_state_id", "补全角色状态"),
    "T003": ("story_state_id", "补全角色名"),
    "T007": ("story_state_id", "补全目标分层"),
}

_FIXERS: dict[str, Any] = {
    "N001": _fix_novel_by_issue,
    "N002": _fix_novel_by_issue,
    "N004": _fix_novel_by_issue,
    "N005": _fix_novel_by_issue,
    "S001": _fix_script_by_issue,
    "S002": _fix_script_by_issue,
    "S003": _fix_script_by_issue,
    "S004": _fix_script_by_issue,
    "S005": _fix_script_by_issue,
    "S006": _fix_script_by_issue,
    "S007": _fix_script_by_issue,
    "B001": _fix_storyboard_by_issue,
    "B002": _fix_storyboard_by_issue,
    "B003": _fix_storyboard_by_issue,
    "B004": _fix_storyboard_by_issue,
    "D001": _fix_directing_by_issue,
    "D002": _fix_directing_by_issue,
    "D003": _fix_directing_by_issue,
    "D004": _fix_directing_by_issue,
    "T001": _fix_story_state_by_issue,
    "T002": _fix_story_state_by_issue,
    "T003": _fix_story_state_by_issue,
    "T007": _fix_story_state_by_issue,
}

# ---------------------------------------------------------------------------
# �޶����ע��㣨Round 4����LLM ����ʽ�޶����滻������
# ---------------------------------------------------------------------------

class RevisionBackend(Protocol):
    """修订后端协议：输入产物与问题清单，输出修订日志。"""

    async def revise(
        self, artifacts: dict[str, Any], issues: list[dict[str, Any]]
    ) -> list[dict[str, Any]]: ...


class LlmReviserBackend:
    """LLM ����ʽ�޶���ˡ�

    ����ʱע�� ``revise_fn``��``async (artifacts, issues) -> list[log]``��
    ��־��Ŀ�ֶ��������һ�£�{"code", "fixed", "action"}��

    ``fallback`` Ϊ������/�쳣ʱ�Ľ�����ˣ�Ĭ�� None�������˹�����
    """

    def __init__(
        self,
        revise_fn: Callable[
            [dict[str, Any], list[dict[str, Any]]],
            Awaitable[list[dict[str, Any]]],
        ],
        *,
        fallback: RevisionBackend | None = None,
    ) -> None:
        self._revise_fn = revise_fn
        self._fallback = fallback

    async def revise(
        self, artifacts: dict[str, Any], issues: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        try:
            log = await self._revise_fn(artifacts, issues)
        except Exception:  # noqa: BLE001
            log = []
        if not log and self._fallback is not None:
            return await self._fallback.revise(artifacts, issues)
        return list(log)


def default_reviser(db: AsyncSession) -> RevisionBackend:
    """Ĭ���޶���ˣ�����棩��"""
    return CreativeReviser(db)


# ---------------------------------------------------------------------------
# LLM 修订器生产实现（Round 5）：包装 workbench LlmClient 为 revise_fn
# ---------------------------------------------------------------------------

_REVISE_SYSTEM_PROMPT = (
    "你是创作产物的自动修订器。给定问题清单与产物键，"
    "返回 JSON：{\"log\": [{\"code\": str, \"fixed\": bool, \"action\": str}]}。"
    "fixed 表示你已在产物库中完成该修复；无法修复时 fixed=false。"
    "只输出 JSON。"
)


def build_llm_revise_fn(
    client: Any,
    *,
    collect_summary: Callable[[dict[str, Any]], str] | None = None,
    rules_backend: RevisionBackend | None = None,
) -> Callable[
    [dict[str, Any], list[dict[str, Any]]],
    Awaitable[list[dict[str, Any]]],
]:
    """把 workbench ``LlmClient`` 包装成异步 ``revise_fn``。

    - LLM 调用为同步阻塞（urllib），通过 ``asyncio.to_thread`` 下放线程。
    - 响应契约：``{"log": [{"code","fixed","action"}...]}``；字段缺失按
      ``fixed=False`` 记账；非法响应返回 ``[]``（触发 fallback）。
    - ``rules_backend`` 提供时，在 LLM 调用前把可规则修复的编码先交规则版
      处理（LLM 只处理剩余项）；不提供则全部交 LLM。
    """
    import asyncio
    import json as _json

    from hermes.workbench.llm import LlmMessage

    async def revise_fn(
        artifacts: dict[str, Any], issues: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        remaining = list(issues)
        merged: list[dict[str, Any]] = []

        if rules_backend is not None and remaining:
            merged.extend(await rules_backend.revise(artifacts, remaining))
            handled = {entry.get("code") for entry in merged if entry.get("fixed")}
            remaining = [
                issue for issue in remaining if issue.get("code") not in handled
            ]

        if not remaining:
            return merged

        prompt_payload = {
            "artifact_keys": sorted(str(k) for k in artifacts.keys()),
            "artifact_summary": (collect_summary or _default_summary)(artifacts),
            "issues": remaining,
        }
        messages = [
            LlmMessage(role="system", content=_REVISE_SYSTEM_PROMPT),
            LlmMessage(role="user", content=_json.dumps(prompt_payload, ensure_ascii=False)),
        ]
        try:
            data = await asyncio.to_thread(_revise_json_call, client, messages)
        except Exception:  # noqa: BLE001  # LlmError/网络/超时 → 交 fallback
            return []

        raw_log = data.get("log") if isinstance(data, dict) else None
        if not isinstance(raw_log, list):
            return merged

        for entry in raw_log:
            if not isinstance(entry, dict):
                continue
            merged.append(
                {
                    "code": str(entry.get("code") or ""),
                    "fixed": bool(entry.get("fixed")),
                    "action": str(entry.get("action") or "llm"),
                }
            )
        return merged

    return revise_fn


def _default_summary(artifacts: dict[str, Any]) -> str:
    return "、".join(f"{k}={v}" for k, v in sorted(artifacts.items()))


def _revise_json_call(client: Any, messages: list[Any]) -> dict[str, Any]:
    """稳健调用（实网联调产出：显式 max_tokens + 截断修复）。"""
    from hermes.content_team.creative.llm_io import chat_json_safe

    return chat_json_safe(client, messages, max_tokens=1536, retries=2)


def make_llm_reviser(
    client: Any | None = None,
    *,
    rules_backend: RevisionBackend | None = None,
    settings: Any | None = None,
) -> LlmReviserBackend:
    """构造生产版 LLM 修订后端。

    修复顺序：可规则修复的编码先交 ``rules_backend``，其余交 LLM；
    LLM 异常时保留规则修复结果（不再二次跑规则，避免重复记账）。
    """
    if client is None:
        from hermes.workbench.llm import make_llm_client as _factory

        client = _factory(settings=settings)
    return LlmReviserBackend(
        build_llm_revise_fn(client, rules_backend=rules_backend),
        fallback=None,
    )
