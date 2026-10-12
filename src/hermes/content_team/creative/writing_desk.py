"""写作台（创作者视角 Round 10 · B2）。

按**创作者语言**重组数据（而非工程维度的 structure/compliance 分）：
今天写到哪、下一章要交代什么、哪些伏笔要爆、有哪些连续性警告、最近审查
给了什么建议。服务于"不知道今天写什么"这一日常痛点。
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hermes.content_team.creative.gates import (
    gate_foreshadowing_lifecycle,
    gate_story_state,
)
from hermes.content_team.models.creative import (
    CreationRun,
    Novel,
    NovelChapter,
    StoryState,
)


async def build_writing_desk(
    db: AsyncSession, novel_id: Any
) -> dict[str, Any] | None:
    """组装某本小说的写作台视图；小说不存在返回 None。"""
    novel = await db.get(Novel, novel_id)
    if novel is None:
        return None

    chapter_result = await db.execute(
        select(NovelChapter)
        .where(NovelChapter.novel_id == novel_id)
        .order_by(NovelChapter.chapter_number.asc())
    )
    chapters = list(chapter_result.scalars().all())
    total_words = sum(c.word_count or 0 for c in chapters)

    state_result = await db.execute(
        select(StoryState).where(StoryState.novel_id == novel_id)
    )
    state = state_result.scalars().first()

    warnings: list[dict[str, Any]] = []
    pending_foreshadowing: list[dict[str, Any]] = []
    context_card: dict[str, Any] = {}

    if state is not None:
        context_card = dict(state.tracking or {})
        for item in state.foreshadowing or []:
            if str(item.get("status") or "") != "resolved":
                pending_foreshadowing.append(
                    {
                        "id": item.get("id"),
                        "content": item.get("content"),
                        "planned_resolution": item.get("planned_resolution"),
                        "status": item.get("status"),
                    }
                )
        # 连续性警告：复用审查门（状态 schema + 伏笔生命周期）
        for report in (
            gate_story_state(
                {
                    "tracking": state.tracking,
                    "characters": state.characters,
                    "foreshadowing": state.foreshadowing,
                    "goals": state.goals,
                }
            ),
            gate_foreshadowing_lifecycle(
                {
                    "foreshadowing": state.foreshadowing or [],
                    "chapter_bodies": [
                        {"chapter_number": c.chapter_number, "body": c.body}
                        for c in chapters
                    ],
                }
            ),
        ):
            for issue in report.issues:
                warnings.append(
                    {
                        "code": issue.code,
                        "severity": issue.severity,
                        "message": issue.message,
                    }
                )

    run_result = await db.execute(
        select(CreationRun)
        .where(CreationRun.topic_id == novel.topic_id)
        .order_by(CreationRun.created_at.desc())
        .limit(1)
    )
    latest_run = run_result.scalars().first()
    recent_review: dict[str, Any] | None = None
    if latest_run is not None and latest_run.review:
        recent_review = {
            "run_id": str(latest_run.id),
            "score": latest_run.review_score,
            "status": latest_run.status.value if latest_run.status else None,
            "stage_issues": latest_run.review.get("stage_issues") or {},
        }

    next_chapter = (chapters[-1].chapter_number + 1) if chapters else 1
    next_actions: list[str] = [f"写第{next_chapter}章"]
    if pending_foreshadowing:
        next_actions.append(
            f"处理 {len(pending_foreshadowing)} 条待回收伏笔"
        )
    error_warnings = [w for w in warnings if w["severity"] == "error"]
    if error_warnings:
        next_actions.append(f"修复 {len(error_warnings)} 条连续性错误")

    # R22：语料伏笔计划 ↔ 状态卡对账（按题名/简介命中语料案例）
    from hermes.content_team.creative.corpus import (
        foreshadowing_plan_for,
        reconcile_foreshadowing,
    )

    plan_text = f"{novel.title} {novel.synopsis or ''} {novel.genre or ''}"
    corpus_plan = foreshadowing_plan_for(plan_text, limit=2)
    reconciliation = (
        reconcile_foreshadowing(corpus_plan, state.foreshadowing or [])
        if corpus_plan
        else None
    )
    if reconciliation and reconciliation.get("missing"):
        next_actions.append(
            f"登记 {len(reconciliation['missing'])} 条语料伏笔计划"
        )

    return {
        "novel": {
            "id": str(novel.id),
            "title": novel.title,
            "status": novel.status.value if novel.status else None,
        },
        "progress": {
            "chapters": len(chapters),
            "total_words": total_words,
            "target_word_count": novel.target_word_count or 0,
            "next_chapter": next_chapter,
        },
        "context_card": context_card,
        "pending_foreshadowing": pending_foreshadowing,
        "continuity_warnings": warnings,
        "corpus_foreshadowing": reconciliation,
        "recent_review": recent_review,
        "next_actions": next_actions,
    }
