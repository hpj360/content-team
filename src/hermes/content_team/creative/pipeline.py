"""创作循环编排：小说 → 剧本 → 分镜 → 导演。

设计要点（与 hermes Loop Engineering 理念一致，但完全落在 content_team
子包内，不修改 hermes core）：

- **builder/checker 分离**：写的不验、验的不写。builder 负责产出，checker
  独立检查，且检查项可机器验证（如实体是否落库、必填字段是否非空）。
- **目标定义 + 停止规则**：每阶段最多 ``max_rounds`` 轮，checker 通过才进入
  下一阶段，否则重试；轮次耗尽则停止并交回未解决项。
- **依赖注入**：``CreativePipeline`` 的 builder/checker 均可替换，默认实现
  基于数据库实体生成骨架产出，便于在无 LLM 环境下测试，也便于后续接入
  LLM builder。
"""
from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from hermes.content_team.creative.gates import (
    REVIEW_PASS_SCORE,
    SEGMENT_MAX_SECONDS,
    SHOT_MAX_SECONDS,
    SHOT_MIN_SECONDS,
    GateReport,
    gate_directing,
    gate_novel,
    gate_script,
    gate_storyboard,
    validate_shot_durations,
)
from hermes.content_team.creative.reviewer import (
    collect_directing,
    collect_novel,
    collect_script,
    collect_storyboard,
    review_creation,
)
from hermes.content_team.models.creative import (
    CameraMovement,
    CreationRun,
    CreationRunStatus,
    CreationStage,
    DirectingPlan,
    DirectingRole,
    Novel,
    NovelChapter,
    RevisionOutcome,
    Script,
    ScriptType,
    Shot,
    ShotSize,
    StoryState,
    Storyboard,
)
from hermes.content_team.creative.cost import (
    UsageTracker,
    reset_tracker,
    set_tracker,
)
from hermes.content_team.creative.deai import apply_de_ai_pass
from hermes.content_team.creative.judges import make_checklist_critic
from hermes.content_team.creative.planners import (
    RETRIEVAL_KEY,
    compose_planners,
    make_beat_sheet_planner,
    make_knowledge_planner,
    make_retrieval_planner,
    render_retrieval_block,
)
from hermes.content_team.creative.revision import CreativeReviser, RevisionBackend
from hermes.content_team.creative.style_fingerprint import extract_fingerprint
from hermes.content_team.models.topic import Topic

# 阶段默认顺序
DEFAULT_STAGES: tuple[CreationStage, ...] = (
    CreationStage.NOVEL,
    CreationStage.SCRIPT,
    CreationStage.STORYBOARD,
    CreationStage.DIRECTING,
)

# builder: (stage, context) -> output dict
StageBuilder = Callable[
    [CreationStage, dict[str, Any]], Awaitable[dict[str, Any]]
]
# checker: (stage, output, context) -> (passed, feedback)
StageChecker = Callable[
    [CreationStage, dict[str, Any], dict[str, Any]],
    Awaitable[tuple[bool, str]],
]
# planner: (stage, context) -> plan dict（合并进本轮 builder 上下文，仅当轮生效）
StagePlanner = Callable[[CreationStage, dict[str, Any]], Awaitable[dict[str, Any]]]
# critic: (stage, output, context) -> advisory notes（建议性，不做门禁）
StageCritic = Callable[
    [CreationStage, dict[str, Any], dict[str, Any]],
    Awaitable[list[str]],
]
# drafter: (stage, context) -> {title, body} LLM 草稿（A2' 陪写注入）
StageDrafter = Callable[[CreationStage, dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass
class StageRoles:
    """阶段内角色注入点（Round 6/8，对齐多 Agent 分工）：

    - ``planner``：写前规划，输出合并进 builder 上下文（如题材/风格/约束）。
    - ``critic``：写后评议，输出建议清单，**不参与门禁**（checker 才是门）。
    - ``drafter``：LLM 草稿（A2'「陪写」）——输出 `{title, body}` 供 builder
      用作正文，持久化与质检仍由三层负责；缺省/失败时降级模板。
    """

    planner: StagePlanner | None = None
    critic: StageCritic | None = None
    drafter: StageDrafter | None = None

    @classmethod
    def default_writer(cls, builder: StageBuilder) -> StageRoles:
        """只有 writer 的默认角色组（等价于不注入）。"""
        return cls()

# 分镜时长门常量与 ``validate_shot_durations`` 已迁至 gates.py，此处 re-export
# 以保持向后兼容（外部与测试仍可从 pipeline 导入）。
__all__ = [
    "SEGMENT_MAX_SECONDS",
    "SHOT_MAX_SECONDS",
    "SHOT_MIN_SECONDS",
    "CreativePipeline",
    "PipelineResult",
    "StageBuilder",
    "StageChecker",
    "StagePlanner",
    "StageCritic",
    "StageDrafter",
    "StageRoles",
    "StageRound",
    "build_default_pipeline",
    "default_builder",
    "default_checker",
    "run_creation",
    "validate_shot_durations",
]


@dataclass
class StageRound:
    """单个阶段某一轮的执行结果。"""

    stage: CreationStage
    round_number: int
    output: dict[str, Any]
    passed: bool
    feedback: str = ""
    critic_notes: list[str] = field(default_factory=list)
    plan: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "round": self.round_number,
            "passed": self.passed,
            "feedback": self.feedback,
            "output": self.output,
            "critic_notes": self.critic_notes,
            "plan": self.plan,
        }


@dataclass
class PipelineResult:
    """整条创作管线的执行结果。"""

    success: bool
    stopped_reason: str
    rounds: int
    current_stage: Optional[CreationStage]
    stage_results: list[StageRound] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)


class CreativePipeline:
    """builder/checker 分离的分阶段创作管线（可选 planner/critic 注入）。"""

    def __init__(
        self,
        builder: StageBuilder,
        checker: StageChecker,
        *,
        stages: tuple[CreationStage, ...] = DEFAULT_STAGES,
        max_rounds: int = 3,
        roles: StageRoles | None = None,
    ) -> None:
        self.builder = builder
        self.checker = checker
        self.stages = stages
        self.max_rounds = max_rounds
        self.roles = roles or StageRoles()

    async def run(
        self, context: dict[str, Any] | None = None
    ) -> PipelineResult:
        """依次执行各阶段，返回整体结果。"""
        ctx = dict(context or {})
        artifacts: dict[str, Any] = {}
        stage_results: list[StageRound] = []
        rounds = 0

        for stage in self.stages:
            passed = False
            feedback = ""
            for round_number in range(1, self.max_rounds + 1):
                rounds += 1
                merged = {**ctx, **artifacts}

                plan: dict[str, Any] = {}
                if self.roles.planner is not None:
                    plan = await self.roles.planner(stage, merged) or {}
                    merged = {**merged, **plan}

                draft: dict[str, Any] = {}
                if self.roles.drafter is not None:
                    draft = await self.roles.drafter(stage, merged) or {}
                    if draft:
                        merged = {**merged, "draft": draft}

                output = await self.builder(stage, merged)

                critic_notes: list[str] = []
                if self.roles.critic is not None:
                    critic_notes = (
                        await self.roles.critic(stage, output, merged) or []
                    )

                ok, feedback = await self.checker(stage, output, merged)
                stage_results.append(
                    StageRound(
                        stage, round_number, output, ok, feedback,
                        critic_notes=critic_notes, plan=plan,
                    )
                )
                if ok:
                    artifacts.update(output)
                    passed = True
                    break
            if not passed:
                reason = (
                    f"stage {stage.value} failed after "
                    f"{self.max_rounds} rounds: {feedback}"
                )
                return PipelineResult(
                    success=False,
                    stopped_reason=reason,
                    rounds=rounds,
                    current_stage=stage,
                    stage_results=stage_results,
                    artifacts=artifacts,
                )

        return PipelineResult(
            success=True,
            stopped_reason="all stages passed",
            rounds=rounds,
            current_stage=None,
            stage_results=stage_results,
            artifacts=artifacts,
        )


# ---------------------------------------------------------------------------
# 默认 builder / checker（基于数据库实体，机器可验证）
# ---------------------------------------------------------------------------


async def _build_novel(
    stage: CreationStage, ctx: dict[str, Any]
) -> dict[str, Any]:
    """NOVEL 阶段：基于选题生成小说骨架、首章与连续性状态。"""
    db: AsyncSession = ctx["db"]
    topic: Topic = ctx["topic"]
    novel = Novel(
        topic_id=topic.id,
        title=f"{topic.title}（小说）",
        genre=ctx.get("genre") or "",
        logline=topic.description[:200],
        synopsis=topic.description,
        target_word_count=int(ctx.get("target_word_count") or 0),
        style_fingerprint=ctx.get("style_fingerprint") or None,
    )
    db.add(novel)
    await db.flush()

    draft_title = str((ctx.get("draft") or {}).get("title") or "第一章")
    chapter_body, deai_rules = _novel_chapter_body(topic, ctx)
    chapter = NovelChapter(
        novel_id=novel.id,
        chapter_number=1,
        title=draft_title,
        body=chapter_body,
    )
    chapter.word_count = NovelChapter.compute_word_count(chapter.body)
    db.add(chapter)
    await db.flush()

    state = StoryState(
        novel_id=novel.id,
        tracking={
            "position": "第1章",
            "recent_summary": chapter.body[:120],
            "active_characters": "主角",
            "pending_foreshadowing": "无",
            "volume_goal": f"完成「{topic.title}」首卷",
            "global_rules": "遵守世界观与平台合规红线",
            "next_step": "推进第二章",
        },
        characters=[
            {
                "name": "主角",
                "ability": "初始设定",
                "psychology": "目标驱动",
                "relations": "与对手对立",
                "goals": "实现核心目标",
            }
        ],
        foreshadowing=_foreshadowing_seed(ctx),
        goals={
            "global": "保持人设与世界观一致",
            "volume": f"完成「{topic.title}」首卷冲突闭环",
            "chapter": "完成第一章并把钩子抛给第二章",
        },
    )
    db.add(state)
    await db.flush()
    return {
        "novel_id": str(novel.id),
        "novel_title": novel.title,
        "story_state_id": str(state.id),
        "de_ai_rules": deai_rules,
        "preview": chapter.body[:400],
    }


def _script_body_with_retrieval(
    novel: Novel, ctx: dict[str, Any]
) -> tuple[str, list[str]]:
    """剧本骨架正文 + 去 AI 味规则；优先 LLM 草稿（A2'），否则模板 + 一致性参考（A1）。"""
    draft = ctx.get("draft") or {}
    draft_body = str(draft.get("body") or "").strip()
    if draft_body:
        clean, rules = apply_de_ai_pass(draft_body)
        return clean, rules

    body = (
        f"主题：{novel.logline}\n\n"
        "第一场　内景／日\n\n"
        "主角登场，交代处境与目标。（建置）\n\n"
        "第二场　内景／夜\n\n"
        "对手施压，冲突升级。（对抗）\n\n"
        "第三场　外景／夜\n\n"
        "主角做出抉择，局势反转。（转折）"
    )
    block = render_retrieval_block(ctx.get(RETRIEVAL_KEY) or [])
    if block:
        body = f"{body}\n\n{block}"
    return body, []


async def _resolve_style_fingerprint(
    db: AsyncSession, context: dict[str, Any]
) -> None:
    """解析文风指纹：现场样本优先，否则复用（options.novel_id）已有小说指纹。

    结果写入 ``context['style_fingerprint']``（供 drafter 注入 prompt）。
    """
    samples = context.pop("style_samples", None)
    if samples:
        fingerprint = extract_fingerprint(list(samples))
        if fingerprint.sample_chars > 0:
            context["style_fingerprint"] = fingerprint.to_dict()
        return
    novel_id = context.get("novel_id")
    if not novel_id:
        return
    novel = await db.get(Novel, uuid.UUID(str(novel_id)))
    if novel is not None and novel.style_fingerprint:
        context["style_fingerprint"] = dict(novel.style_fingerprint)


def _foreshadowing_seed(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    """R22：从语料伏笔计划 seed StoryState.foreshadowing（需显式开启）。

    仅当 ``options.seed_foreshadowing=True`` 且规划器给出了
    ``foreshadowing_seed`` 时落库；默认关闭，避免自动种子未兑现导致门禁误报。
    """
    if not ctx.get("seed_foreshadowing"):
        return []
    seed = ctx.get("foreshadowing_seed") or []
    out: list[dict[str, Any]] = []
    for item in seed:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "id": str(item.get("id") or ""),
                "content": str(item.get("content") or ""),
                "planted_at": str(item.get("planted_at") or "第1章"),
                "planned_resolution": str(item.get("planned_resolution") or ""),
                "status": str(item.get("status") or "planted"),
                "keyword": str(item.get("keyword") or ""),
                "source_case": str(item.get("source_case") or ""),
            }
        )
    return out


def _novel_chapter_body(topic: Topic, ctx: dict[str, Any]) -> tuple[str, list[str]]:
    """首章正文 + 去 AI 味规则；优先 LLM 草稿（A2'），否则大纲模板。"""
    draft = ctx.get("draft") or {}
    draft_body = str(draft.get("body") or "").strip()
    if draft_body:
        clean, rules = apply_de_ai_pass(draft_body)
        return clean, rules
    return f"大纲：{topic.description}\n\n（正文占位，待写作阶段填充）", []


async def _build_script(
    stage: CreationStage, ctx: dict[str, Any]
) -> dict[str, Any]:
    """SCRIPT 阶段：基于小说生成剧本骨架，并注入一致性参考（A1）。"""
    db: AsyncSession = ctx["db"]
    novel: Novel = await db.get(Novel, uuid.UUID(ctx["novel_id"]))
    assert novel is not None  # checker 已保证上游产出存在
    script_body, deai_rules = _script_body_with_retrieval(novel, ctx)
    script = Script(
        topic_id=novel.topic_id,
        novel_id=novel.id,
        title=f"{novel.title}·剧本",
        script_type=ScriptType(ctx.get("script_type") or ScriptType.MICRO.value),
        logline=novel.logline,
        body=script_body,
    )
    db.add(script)
    await db.flush()
    return {
        "script_id": str(script.id),
        "script_title": script.title,
        "de_ai_rules": deai_rules,
        "preview": script.body[:400],
    }


async def _build_storyboard(
    stage: CreationStage, ctx: dict[str, Any]
) -> dict[str, Any]:
    """STORYBOARD 阶段：基于剧本生成分镜与模板镜头。"""
    db: AsyncSession = ctx["db"]
    script: Script = await db.get(Script, uuid.UUID(ctx["script_id"]))
    assert script is not None
    storyboard = Storyboard(script_id=script.id, title=f"{script.title}·分镜")
    db.add(storyboard)
    await db.flush()

    template = [
        (ShotSize.WIDE, CameraMovement.DOLLY, "建置镜头：交代环境与人物关系"),
        (ShotSize.MEDIUM, CameraMovement.STATIC, "对话镜头：推进冲突"),
        (ShotSize.CLOSE, CameraMovement.ZOOM, "情绪镜头：放大关键情绪"),
    ]
    for number, (size, movement, desc) in enumerate(template, start=1):
        db.add(
            Shot(
                storyboard_id=storyboard.id,
                shot_number=number,
                shot_size=size,
                camera_movement=movement,
                description=desc,
                duration_seconds=3.0,
            )
        )
    await db.flush()
    return {
        "storyboard_id": str(storyboard.id),
        "shot_count": len(template),
    }


async def _build_directing(
    stage: CreationStage, ctx: dict[str, Any]
) -> dict[str, Any]:
    """DIRECTING 阶段：基于剧本与分镜生成导演阐述。"""
    db: AsyncSession = ctx["db"]
    plan = DirectingPlan(
        script_id=uuid.UUID(ctx["script_id"]),
        storyboard_id=uuid.UUID(ctx["storyboard_id"]),
        role=DirectingRole(ctx.get("directing_role") or DirectingRole.DIRECTOR.value),
        title=f"{ctx.get('script_title', '剧本')}·导演阐述",
        style=ctx.get("style") or "写实",
        tone=ctx.get("tone") or "克制",
        pacing=ctx.get("pacing") or "中速，情绪节点留白",
        visual_reference=ctx.get("visual_reference") or "",
        director_notes="（导演调度与表演指导占位）",
    )
    db.add(plan)
    await db.flush()
    return {"directing_plan_id": str(plan.id)}


async def _evaluate_gate(
    collector: Callable[..., Awaitable[Optional[dict]]],
    gate: Callable[[dict], GateReport],
    db: AsyncSession,
    raw_id: str | None,
    label: str,
) -> tuple[bool, str]:
    """采集事实 → 运行质量门 → 返回 (是否通过, 反馈)。

    checker 与 reviewer 共用同一套质量门（``gates``），确保判定一致。
    """
    if not raw_id:
        return False, f"缺少 {label} ID"
    data = await collector(db, uuid.UUID(str(raw_id)))
    if data is None:
        return False, f"{label}未落库"
    report = gate(data)
    if not report.passed:
        return False, "; ".join(report.error_messages())
    return True, ""


async def _check_novel(
    stage: CreationStage, output: dict[str, Any], ctx: dict[str, Any]
) -> tuple[bool, str]:
    """NOVEL 检查：委托 ``gate_novel``（logline/标题/章节/字数）。"""
    return await _evaluate_gate(
        collect_novel, gate_novel, ctx["db"], output.get("novel_id"), "小说"
    )


async def _check_script(
    stage: CreationStage, output: dict[str, Any], ctx: dict[str, Any]
) -> tuple[bool, str]:
    """SCRIPT 检查：委托 ``gate_script``（logline/场景数/合规/去 AI 味）。"""
    return await _evaluate_gate(
        collect_script, gate_script, ctx["db"], output.get("script_id"), "剧本"
    )


async def _check_storyboard(
    stage: CreationStage, output: dict[str, Any], ctx: dict[str, Any]
) -> tuple[bool, str]:
    """STORYBOARD 检查：委托 ``gate_storyboard``（镜头/时长/连续性）。"""
    return await _evaluate_gate(
        collect_storyboard,
        gate_storyboard,
        ctx["db"],
        output.get("storyboard_id"),
        "分镜",
    )


async def _check_directing(
    stage: CreationStage, output: dict[str, Any], ctx: dict[str, Any]
) -> tuple[bool, str]:
    """DIRECTING 检查：委托 ``gate_directing``（风格/基调/节奏/阐述）。"""
    return await _evaluate_gate(
        collect_directing,
        gate_directing,
        ctx["db"],
        output.get("directing_plan_id"),
        "导演方案",
    )


_BUILDERS = {
    CreationStage.NOVEL: _build_novel,
    CreationStage.SCRIPT: _build_script,
    CreationStage.STORYBOARD: _build_storyboard,
    CreationStage.DIRECTING: _build_directing,
}

_CHECKERS = {
    CreationStage.NOVEL: _check_novel,
    CreationStage.SCRIPT: _check_script,
    CreationStage.STORYBOARD: _check_storyboard,
    CreationStage.DIRECTING: _check_directing,
}


def default_builder(stage: CreationStage, ctx: dict[str, Any]) -> Awaitable[dict[str, Any]]:
    """默认 builder：按阶段分派到数据库实体生成函数。"""
    return _BUILDERS[stage](stage, ctx)


def default_checker(
    stage: CreationStage, output: dict[str, Any], ctx: dict[str, Any]
) -> Awaitable[tuple[bool, str]]:
    """默认 checker：按阶段分派到机器可验证的检查函数。"""
    return _CHECKERS[stage](stage, output, ctx)


def build_default_pipeline(
    *, max_rounds: int = 3
) -> CreativePipeline:
    """构造基于默认 builder/checker 的创作管线。"""
    return CreativePipeline(
        builder=default_builder,
        checker=default_checker,
        max_rounds=max_rounds,
    )


async def run_creation(
    db: AsyncSession,
    topic_id: uuid.UUID,
    *,
    max_rounds: int = 3,
    stages: tuple[CreationStage, ...] = DEFAULT_STAGES,
    options: dict[str, Any] | None = None,
    review: bool = True,
    auto_revise: bool = True,
    max_revise_rounds: int = 2,
    reviser: RevisionBackend | None = None,
    roles: StageRoles | None = None,
    retrieval: bool = True,
    memory: Any | None = None,
    budget_tokens: int | None = None,
    default_roles: bool = True,
    corpus_injection: bool = True,
    knowledge_injection: bool = True,
) -> CreationRun:
    """执行创作管线并在提供 ``memory`` 时记账（C1 · 跨 run 学习地基）。

    成本治理（R16）：``budget_tokens`` 限制本次运行的 LLM token 总预算，
    超限自动降级（LLM 角色返回空 → 模板兜底），用量落 ``run.llm_usage``。
    """
    tracker = UsageTracker(budget_tokens=budget_tokens)
    token = set_tracker(tracker)
    try:
        run = await _execute_creation(
            db,
            topic_id,
            max_rounds=max_rounds,
            stages=stages,
            options=options,
            review=review,
            auto_revise=auto_revise,
            max_revise_rounds=max_revise_rounds,
            reviser=reviser,
            roles=roles,
            retrieval=retrieval,
            default_roles=default_roles,
            corpus_injection=corpus_injection,
            knowledge_injection=knowledge_injection,
        )
    finally:
        reset_tracker(token)

    run.llm_usage = tracker.to_dict()
    run.token_total = tracker.total_tokens
    await db.commit()
    await db.refresh(run)

    if memory is not None:
        _record_creation_memory(memory, run)
    return run


def _record_creation_memory(memory: Any, run: CreationRun) -> None:
    """best-effort 记账：失败不影响创作结果。"""
    try:
        from hermes.content_team.memory import (
            record_creation_run,
            record_review_result,
        )

        record_creation_run(
            run_id=str(run.id),
            topic_id=str(run.topic_id),
            title="",
            status=run.status.value if run.status else "UNKNOWN",
            stages=list(run.stages or []),
            review_score=run.review_score,
            service=memory,
        )
        review = run.review or {}
        if review:
            record_review_result(
                run_id=str(run.id),
                topic_id=str(run.topic_id),
                passed=bool(review.get("passed")),
                score=float(review.get("score") or 0.0),
                error_count=int(review.get("error_count") or 0),
                warning_count=int(review.get("warning_count") or 0),
                stage_issues=review.get("stage_issues") or {},
                service=memory,
            )
    except Exception:  # noqa: BLE001
        return


async def _execute_creation(
    db: AsyncSession,
    topic_id: uuid.UUID,
    *,
    max_rounds: int = 3,
    stages: tuple[CreationStage, ...] = DEFAULT_STAGES,
    options: dict[str, Any] | None = None,
    review: bool = True,
    auto_revise: bool = True,
    max_revise_rounds: int = 2,
    reviser: RevisionBackend | None = None,
    roles: StageRoles | None = None,
    retrieval: bool = True,
    default_roles: bool = True,
    corpus_injection: bool = True,
    knowledge_injection: bool = True,
) -> CreationRun:
    """执行一次创作管线并落库为 ``CreationRun``。

    - 管线失败 → ``FAILED``（异常）或 ``STOPPED``（轮次耗尽）。
    - 独立审查通过 → ``SUCCEEDED``。
    - 审查未通过且 ``auto_revise=True`` → 按问题编码自动修订后再审，
      问题未收敛或轮次耗尽则 ``STOPPED``，否则 ``NEEDS_REVISION`` 交回人工。
    """
    topic = await db.get(Topic, topic_id)
    if topic is None:
        raise ValueError("Topic not found")

    run = CreationRun(
        topic_id=topic.id,
        stages=[stage.value for stage in stages],
        current_stage=stages[0] if stages else None,
        status=CreationRunStatus.RUNNING,
        max_rounds=max_rounds,
        revision_outcome=RevisionOutcome.NONE,
    )
    db.add(run)
    await db.flush()

    context: dict[str, Any] = {"db": db, "topic": topic}
    context.update(options or {})

    # A2'：文风指纹（options.style_samples 现场提取；否则从 options.novel_id 复用）
    await _resolve_style_fingerprint(db, context)

    # 默认角色组：节奏规划（R17）+ 一致性检索（A1）+ 清单评议（R17）
    effective_roles = roles
    if effective_roles is None and default_roles:
        planner_fns = [make_beat_sheet_planner(include_corpus=corpus_injection)]
        if retrieval:
            planner_fns.append(make_retrieval_planner(db))
        if knowledge_injection:
            planner_fns.append(make_knowledge_planner())
        effective_roles = StageRoles(
            planner=compose_planners(*planner_fns),
            critic=make_checklist_critic(),
        )

    pipeline = CreativePipeline(
        builder=default_builder,
        checker=default_checker,
        stages=stages,
        max_rounds=max_rounds,
        roles=effective_roles,
    )
    try:
        result = await pipeline.run(context)
    except Exception as exc:  # noqa: BLE001
        run.status = CreationRunStatus.FAILED
        run.error_message = str(exc)
        await db.commit()
        await db.refresh(run)
        return run

    run.rounds = result.rounds
    run.current_stage = result.current_stage
    run.stage_results = [item.to_dict() for item in result.stage_results]
    run.artifacts = result.artifacts
    # A2'：记录文风指纹与去 AI 味留痕（从各阶段 output 聚合）
    if context.get("style_fingerprint"):
        run.artifacts["style_fingerprint"] = context["style_fingerprint"]
    rules = sorted(
        {
            rule
            for item in result.stage_results
            for rule in (item.output.get("de_ai_rules") or [])
        }
    )
    if rules:
        run.artifacts["de_ai_rules"] = rules

    if not result.success:
        run.status = CreationRunStatus.STOPPED
        run.error_message = result.stopped_reason
        await db.commit()
        await db.refresh(run)
        return run

    run.status = CreationRunStatus.SUCCEEDED

    if not (review and result.artifacts):
        await db.commit()
        await db.refresh(run)
        return run

    # 独立审查 → 自动修订 → 重审 循环（主体隔离：审查器只读产物 ID）
    backend = reviser if reviser is not None else CreativeReviser(db)
    revise_log: list[dict[str, Any]] = []
    previous_score: Optional[float] = None

    while True:
        report = await review_creation(db, result.artifacts)
        run.review = report.to_dict()
        run.review_score = report.score

        if report.passed:
            run.status = CreationRunStatus.SUCCEEDED
            run.error_message = None
            if run.revise_rounds > 0:
                run.revision_outcome = RevisionOutcome.FIXED
            break

        if not auto_revise:
            run.status = CreationRunStatus.NEEDS_REVISION
            run.error_message = (
                f"审查未通过：总分 {report.score:.1f} < {REVIEW_PASS_SCORE:.0f}"
            )
            break
        if run.revise_rounds >= max_revise_rounds:
            run.revision_outcome = RevisionOutcome.EXHAUSTED
            run.status = CreationRunStatus.NEEDS_REVISION
            run.error_message = (
                f"修订轮次耗尽：总分 {report.score:.1f} < {REVIEW_PASS_SCORE:.0f}"
            )
            break

        issues: list[dict[str, Any]] = [
            entry for stage_issue in report.stage_issues.values()
            for entry in stage_issue
        ]
        revised = await backend.revise(result.artifacts, issues)
        revise_log.extend(revised)
        run.revise_log = revise_log
        run.revise_rounds += 1

        if not any(entry.get("fixed") for entry in revised):
            run.revision_outcome = RevisionOutcome.UNCHANGED
            run.status = CreationRunStatus.NEEDS_REVISION
            run.error_message = f"审查问题修订无实质变化：总分 {report.score:.1f}"
            break
        if previous_score is not None and report.score <= previous_score:
            run.revision_outcome = RevisionOutcome.UNCHANGED
            run.status = CreationRunStatus.NEEDS_REVISION
            run.error_message = f"审查问题未收敛：总分 {report.score:.1f}"
            break
        previous_score = report.score

    await db.commit()
    await db.refresh(run)
    return run
