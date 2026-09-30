"""创作审查器：与 builder 隔离的独立质量审查（蒸馏融合）。

设计原则（与头部来源对齐）：

- **审查主体独立**：审查器只接收产物 ID，重新从数据库读取事实，不接触
  builder 的内部状态；等价于"不同上下文/不同角色执行审查"。
- **判定可机器验证**：所有结论来自 ``gates`` 的纯函数断言，不是自评。
- **留痕可追溯**：输出逐阶段问题清单 + 维度得分 + 总分 + 裁定。
- **门控强制**：总分低于 ``REVIEW_PASS_SCORE`` 时裁定为不通过。

来源融合：分镜分级/时长硬门（短剧/分镜套件）、剧本合规与去 AI 味（短剧 +
去 AI 味 skill）、小说状态契约（网文 skill）、导演出口门（电影导演 skill）。
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from hermes.content_team.creative.gates import (
    REVIEW_PASS_SCORE,
    GateReport,
    gate_directing,
    gate_foreshadowing_lifecycle,
    gate_novel,
    gate_script,
    gate_story_state,
    gate_storyboard,
    score_reports,
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


# ---------------------------------------------------------------------------
# DB -> 规范化 dict 采集器（审查器与 checker 共用）
# ---------------------------------------------------------------------------


async def collect_novel(db: AsyncSession, novel_id: uuid.UUID) -> Optional[dict]:
    """采集小说事实（含章节）为规范化 dict。"""
    novel = await db.get(Novel, novel_id)
    if novel is None:
        return None
    result = await db.execute(
        sa.select(NovelChapter)
        .where(NovelChapter.novel_id == novel.id)
        .order_by(NovelChapter.chapter_number.asc())
    )
    chapters = list(result.scalars().all())
    return {
        "title": novel.title,
        "logline": novel.logline,
        "chapters": [
            {"body": c.body, "word_count": c.word_count} for c in chapters
        ],
    }


async def collect_script(db: AsyncSession, script_id: uuid.UUID) -> Optional[dict]:
    """采集剧本事实为规范化 dict。"""
    script = await db.get(Script, script_id)
    if script is None:
        return None
    return {"logline": script.logline, "body": script.body}


async def collect_storyboard(
    db: AsyncSession, storyboard_id: uuid.UUID
) -> Optional[dict]:
    """采集分镜事实（含镜头）为规范化 dict。"""
    storyboard = await db.get(Storyboard, storyboard_id)
    if storyboard is None:
        return None
    result = await db.execute(
        sa.select(Shot)
        .where(Shot.storyboard_id == storyboard.id)
        .order_by(Shot.shot_number.asc())
    )
    shots = list(result.scalars().all())
    return {
        "shots": [
            {
                "shot_number": s.shot_number,
                "description": s.description,
                "shot_size": s.shot_size.value if s.shot_size else None,
                "camera_movement": (
                    s.camera_movement.value if s.camera_movement else None
                ),
                "duration_seconds": s.duration_seconds,
            }
            for s in shots
        ]
    }


async def collect_directing(
    db: AsyncSession, plan_id: uuid.UUID
) -> Optional[dict]:
    """采集导演方案事实为规范化 dict。"""
    plan = await db.get(DirectingPlan, plan_id)
    if plan is None:
        return None
    return {
        "style": plan.style,
        "tone": plan.tone,
        "pacing": plan.pacing,
        "director_notes": plan.director_notes,
    }


async def collect_story_state(
    db: AsyncSession, state_id: uuid.UUID
) -> Optional[dict]:
    """采集故事状态为规范化 dict（schema 校验用）。"""
    state = await db.get(StoryState, state_id)
    if state is None:
        return None
    return {
        "tracking": state.tracking,
        "characters": state.characters,
        "foreshadowing": state.foreshadowing,
        "goals": state.goals,
    }


async def collect_foreshadowing_lifecycle(
    db: AsyncSession,
    state_id: uuid.UUID,
    *,
    novel_id: Optional[uuid.UUID] = None,
) -> Optional[dict]:
    """采集"正文 ↔ 伏笔状态卡"跨表事实。

    必须同时存在 StoryState 与 Novel（含章节正文）才返回规范数据；
    缺任一侧则返回 None（审查器跳过该门）。
    """
    state = await db.get(StoryState, state_id)
    if state is None:
        return None
    novel_id = novel_id or state.novel_id
    if novel_id is None:
        return None
    result = await db.execute(
        sa.select(NovelChapter)
        .where(NovelChapter.novel_id == novel_id)
        .order_by(NovelChapter.chapter_number.asc())
    )
    chapters = list(result.scalars().all())
    return {
        "foreshadowing": list(state.foreshadowing or []),
        "chapter_bodies": [
            {"chapter_number": c.chapter_number, "body": c.body} for c in chapters
        ],
    }


_COLLECTORS = {
    "NOVEL": ("novel_id", collect_novel),
    "SCRIPT": ("script_id", collect_script),
    "STORYBOARD": ("storyboard_id", collect_storyboard),
    "DIRECTING": ("directing_plan_id", collect_directing),
    "STORY_STATE": ("story_state_id", collect_story_state),
}


# ---------------------------------------------------------------------------
# 审查报告
# ---------------------------------------------------------------------------


@dataclass
class ReviewReport:
    """一次创作审查的完整结果。"""

    score: float
    passed: bool
    dimensions: dict[str, float] = field(default_factory=dict)
    stage_issues: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    error_count: int = 0
    warning_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 2),
            "passed": self.passed,
            "dimensions": {k: round(v, 2) for k, v in self.dimensions.items()},
            "stage_issues": self.stage_issues,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
        }


class CreativeReviewer:
    """独立审查器：只依赖产物 ID 与数据库事实。"""

    def __init__(
        self, db: AsyncSession, *, pass_score: float = REVIEW_PASS_SCORE
    ) -> None:
        self.db = db
        self.pass_score = pass_score

    async def review(self, artifacts: dict[str, Any]) -> ReviewReport:
        """审查一组产物，返回评分报告。"""
        reports: list[GateReport] = []
        stage_issues: dict[str, list[dict[str, Any]]] = {}

        for stage, (key, collector) in _COLLECTORS.items():
            raw_id = artifacts.get(key)
            if not raw_id:
                continue
            data = await collector(self.db, uuid.UUID(str(raw_id)))
            if data is None:
                continue
            report = _GATE_BY_STAGE[stage](data)
            reports.append(report)
            if report.issues:
                stage_issues[stage] = [
                    {
                        "code": i.code,
                        "message": i.message,
                        "severity": i.severity,
                        "dimension": i.dimension,
                    }
                    for i in report.issues
                ]

        # 伏笔生命周期门：需要 novel_id 与 story_state_id 双佐证
        lifecycle_report = await self._review_foreshadowing_lifecycle(artifacts)
        if lifecycle_report is not None:
            reports.append(lifecycle_report)
            if lifecycle_report.issues:
                stage_issues[lifecycle_report.stage] = [
                    {
                        "code": i.code,
                        "message": i.message,
                        "severity": i.severity,
                        "dimension": i.dimension,
                    }
                    for i in lifecycle_report.issues
                ]

        total, dimensions = score_reports(reports)
        error_count = sum(len(r.errors) for r in reports)
        warning_count = sum(len(r.warnings) for r in reports)
        return ReviewReport(
            score=total,
            # 硬门：存在任一 error 即不通过；否则需总分达标
            passed=error_count == 0 and total >= self.pass_score,
            dimensions=dimensions,
            stage_issues=stage_issues,
            error_count=error_count,
            warning_count=warning_count,
        )

    async def _review_foreshadowing_lifecycle(
        self, artifacts: dict[str, Any]
    ) -> Optional[GateReport]:
        """跨表门：仅当正文与状态卡两侧同时存在时审查。"""
        state_raw = artifacts.get("story_state_id")
        if not state_raw:
            return None
        data = await collect_foreshadowing_lifecycle(
            self.db, uuid.UUID(str(state_raw))
        )
        if data is None:
            return None
        return gate_foreshadowing_lifecycle(data)


_GATE_BY_STAGE = {
    "NOVEL": gate_novel,
    "SCRIPT": gate_script,
    "STORYBOARD": gate_storyboard,
    "DIRECTING": gate_directing,
    "STORY_STATE": gate_story_state,
}


async def review_creation(
    db: AsyncSession, artifacts: dict[str, Any]
) -> ReviewReport:
    """便捷入口：对一组创作产物执行独立审查。"""
    return await CreativeReviewer(db).review(artifacts)
