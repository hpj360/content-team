"""创作能力 API：小说 / 剧本 / 分镜 / 导演方案 CRUD + 创作循环编排。"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hermes.content_team.api.publish import PublishTaskResponse
from hermes.content_team.creative.pipeline import run_creation
from hermes.content_team.creative.reporting import render_run_report
from hermes.content_team.db import get_db
from hermes.content_team.models.publish import PublishTask
from hermes.content_team.models.creative import (
    CameraMovement,
    CreationRun,
    CreationRunStatus,
    CreationStage,
    DirectingPlan,
    DirectingRole,
    DirectingStatus,
    Novel,
    NovelChapter,
    NovelStatus,
    Script,
    ScriptStatus,
    ScriptType,
    Shot,
    ShotSize,
    StoryState,
    Storyboard,
    StoryboardStatus,
)

novels_router = APIRouter()
scripts_router = APIRouter()
storyboards_router = APIRouter()
directing_router = APIRouter()
creation_router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class NovelCreate(BaseModel):
    """创建小说请求体。"""

    title: str = Field(..., min_length=1, max_length=255)
    topic_id: UUID | None = None
    content_id: UUID | None = None
    genre: str = ""
    logline: str = ""
    synopsis: str = ""
    status: NovelStatus = NovelStatus.PLANNING
    target_word_count: int = Field(default=0, ge=0)
    author_id: UUID | None = None


class NovelUpdate(BaseModel):
    """更新小说请求体，所有字段可选。"""

    title: str | None = Field(None, min_length=1, max_length=255)
    genre: str | None = None
    logline: str | None = None
    synopsis: str | None = None
    status: NovelStatus | None = None
    target_word_count: int | None = Field(None, ge=0)
    word_count: int | None = Field(None, ge=0)


class NovelResponse(BaseModel):
    """小说响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    topic_id: UUID | None = None
    content_id: UUID | None = None
    title: str
    genre: str
    logline: str
    synopsis: str
    status: NovelStatus
    target_word_count: int
    word_count: int
    style_fingerprint: dict[str, Any] | None = None
    author_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ChapterCreate(BaseModel):
    """创建章节请求体。"""

    title: str = Field(default="", max_length=255)
    body: str = ""
    status: str = "draft"


class ChapterUpdate(BaseModel):
    """更新章节请求体，所有字段可选。"""

    title: str | None = Field(None, max_length=255)
    body: str | None = None
    status: str | None = None


class ChapterResponse(BaseModel):
    """章节响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    novel_id: UUID
    chapter_number: int
    title: str
    body: str
    word_count: int
    status: str
    created_at: datetime
    updated_at: datetime


class ScriptCreate(BaseModel):
    """创建剧本请求体。"""

    title: str = Field(..., min_length=1, max_length=255)
    topic_id: UUID | None = None
    content_id: UUID | None = None
    novel_id: UUID | None = None
    script_type: ScriptType = ScriptType.MICRO
    logline: str = ""
    body: str = ""
    status: ScriptStatus = ScriptStatus.DRAFT
    author_id: UUID | None = None


class ScriptUpdate(BaseModel):
    """更新剧本请求体，所有字段可选。"""

    title: str | None = Field(None, min_length=1, max_length=255)
    script_type: ScriptType | None = None
    logline: str | None = None
    body: str | None = None
    status: ScriptStatus | None = None


class ScriptResponse(BaseModel):
    """剧本响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    topic_id: UUID | None = None
    content_id: UUID | None = None
    novel_id: UUID | None = None
    title: str
    script_type: ScriptType
    logline: str
    body: str
    status: ScriptStatus
    author_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class StoryboardCreate(BaseModel):
    """创建分镜请求体。"""

    title: str = Field(..., min_length=1, max_length=255)
    script_id: UUID | None = None
    status: StoryboardStatus = StoryboardStatus.DRAFT


class StoryboardUpdate(BaseModel):
    """更新分镜请求体，所有字段可选。"""

    title: str | None = Field(None, min_length=1, max_length=255)
    status: StoryboardStatus | None = None


class StoryboardResponse(BaseModel):
    """分镜响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    script_id: UUID | None = None
    title: str
    status: StoryboardStatus
    created_at: datetime
    updated_at: datetime


class ShotCreate(BaseModel):
    """创建镜头请求体。"""

    shot_number: int = Field(..., ge=1)
    shot_size: ShotSize = ShotSize.MEDIUM
    camera_movement: CameraMovement = CameraMovement.STATIC
    description: str = ""
    dialogue: str = ""
    sound: str = ""
    duration_seconds: float = Field(default=0.0, ge=0.0)
    notes: str = ""


class ShotUpdate(BaseModel):
    """更新镜头请求体，所有字段可选。"""

    shot_number: int | None = Field(None, ge=1)
    shot_size: ShotSize | None = None
    camera_movement: CameraMovement | None = None
    description: str | None = None
    dialogue: str | None = None
    sound: str | None = None
    duration_seconds: float | None = Field(None, ge=0.0)
    notes: str | None = None


class ShotResponse(BaseModel):
    """镜头响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    storyboard_id: UUID
    shot_number: int
    shot_size: ShotSize
    camera_movement: CameraMovement
    description: str
    dialogue: str
    sound: str
    duration_seconds: float
    notes: str
    created_at: datetime
    updated_at: datetime


class DirectingCreate(BaseModel):
    """创建导演/编导方案请求体。"""

    title: str = Field(..., min_length=1, max_length=255)
    script_id: UUID | None = None
    storyboard_id: UUID | None = None
    role: DirectingRole = DirectingRole.DIRECTOR
    style: str = ""
    tone: str = ""
    pacing: str = ""
    visual_reference: str = ""
    director_notes: str = ""
    status: DirectingStatus = DirectingStatus.DRAFT


class DirectingUpdate(BaseModel):
    """更新导演/编导方案请求体，所有字段可选。"""

    title: str | None = Field(None, min_length=1, max_length=255)
    role: DirectingRole | None = None
    style: str | None = None
    tone: str | None = None
    pacing: str | None = None
    visual_reference: str | None = None
    director_notes: str | None = None
    status: DirectingStatus | None = None


class DirectingResponse(BaseModel):
    """导演/编导方案响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    script_id: UUID | None = None
    storyboard_id: UUID | None = None
    role: DirectingRole
    title: str
    style: str
    tone: str
    pacing: str
    visual_reference: str
    director_notes: str
    status: DirectingStatus
    created_at: datetime
    updated_at: datetime


class CreationRunRequest(BaseModel):
    """发起创作循环请求体。"""

    topic_id: UUID
    max_rounds: int = Field(default=3, ge=1, le=10)
    stages: list[CreationStage] | None = None
    options: dict[str, Any] = Field(default_factory=dict)
    review: bool = True
    auto_revise: bool = True
    max_revise_rounds: int = Field(default=2, ge=0, le=5)
    budget_tokens: int | None = Field(default=None, ge=0)


class CreationRunResponse(BaseModel):
    """创作循环运行响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    topic_id: UUID | None = None
    stages: list[str]
    current_stage: CreationStage | None = None
    status: CreationRunStatus
    max_rounds: int
    rounds: int
    stage_results: list[dict[str, Any]]
    artifacts: dict[str, Any]
    review: dict[str, Any] | None = None
    review_score: float | None = None
    revise_rounds: int = 0
    revision_outcome: str | None = None
    revise_log: list[dict[str, Any]] = Field(default_factory=list)
    llm_usage: dict[str, Any] = Field(default_factory=dict)
    token_total: int = 0
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# 小说路由
# ---------------------------------------------------------------------------


@novels_router.post("", response_model=NovelResponse, status_code=201)
async def create_novel(
    payload: NovelCreate, db: AsyncSession = Depends(get_db)
) -> Novel:
    """创建小说。"""
    novel = Novel(**payload.model_dump())
    db.add(novel)
    await db.commit()
    await db.refresh(novel)
    return novel


@novels_router.get("", response_model=list[NovelResponse])
async def list_novels(
    status: NovelStatus | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[Novel]:
    """列出所有小说，支持按状态过滤。"""
    stmt = select(Novel)
    if status is not None:
        stmt = stmt.where(Novel.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@novels_router.get("/{novel_id}", response_model=NovelResponse)
async def get_novel(
    novel_id: UUID, db: AsyncSession = Depends(get_db)
) -> Novel:
    """获取单个小说。"""
    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    return novel


@novels_router.put("/{novel_id}", response_model=NovelResponse)
async def update_novel(
    novel_id: UUID,
    payload: NovelUpdate,
    db: AsyncSession = Depends(get_db),
) -> Novel:
    """更新小说。"""
    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(novel, key, value)
    await db.commit()
    await db.refresh(novel)
    return novel


@novels_router.delete("/{novel_id}", status_code=204)
async def delete_novel(
    novel_id: UUID, db: AsyncSession = Depends(get_db)
) -> None:
    """删除小说（级联删除章节）。"""
    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    await db.delete(novel)
    await db.commit()


@novels_router.post(
    "/{novel_id}/chapters", response_model=ChapterResponse, status_code=201
)
async def create_chapter(
    novel_id: UUID,
    payload: ChapterCreate,
    db: AsyncSession = Depends(get_db),
) -> NovelChapter:
    """为小说新增章节，章节号自动递增，字数自动统计。"""
    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")

    max_stmt = select(NovelChapter.chapter_number).where(
        NovelChapter.novel_id == novel_id
    )
    result = await db.execute(max_stmt)
    current = max(result.scalars().all(), default=0)
    chapter = NovelChapter(
        novel_id=novel_id,
        chapter_number=current + 1,
        title=payload.title,
        body=payload.body,
        status=payload.status,
        word_count=NovelChapter.compute_word_count(payload.body),
    )
    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)
    return chapter


@novels_router.get("/{novel_id}/chapters", response_model=list[ChapterResponse])
async def list_chapters(
    novel_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[NovelChapter]:
    """列出小说的所有章节，按章节号升序。"""
    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    stmt = (
        select(NovelChapter)
        .where(NovelChapter.novel_id == novel_id)
        .order_by(NovelChapter.chapter_number.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@novels_router.put(
    "/{novel_id}/chapters/{chapter_id}", response_model=ChapterResponse
)
async def update_chapter(
    novel_id: UUID,
    chapter_id: UUID,
    payload: ChapterUpdate,
    db: AsyncSession = Depends(get_db),
) -> NovelChapter:
    """更新章节，正文变更时自动重算字数。"""
    chapter = await db.get(NovelChapter, chapter_id)
    if chapter is None or chapter.novel_id != novel_id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(chapter, key, value)
    if "body" in data:
        chapter.word_count = NovelChapter.compute_word_count(chapter.body)
    await db.commit()
    await db.refresh(chapter)
    return chapter


@novels_router.delete(
    "/{novel_id}/chapters/{chapter_id}", status_code=204
)
async def delete_chapter(
    novel_id: UUID,
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除章节。"""
    chapter = await db.get(NovelChapter, chapter_id)
    if chapter is None or chapter.novel_id != novel_id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    await db.delete(chapter)
    await db.commit()


# ---------------------------------------------------------------------------
# 剧本路由
# ---------------------------------------------------------------------------


@scripts_router.post("", response_model=ScriptResponse, status_code=201)
async def create_script(
    payload: ScriptCreate, db: AsyncSession = Depends(get_db)
) -> Script:
    """创建剧本。"""
    script = Script(**payload.model_dump())
    db.add(script)
    await db.commit()
    await db.refresh(script)
    return script


@scripts_router.get("", response_model=list[ScriptResponse])
async def list_scripts(
    status: ScriptStatus | None = None,
    script_type: ScriptType | None = None,
    topic_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[Script]:
    """列出剧本，支持按状态/类型/选题过滤。"""
    stmt = select(Script)
    if status is not None:
        stmt = stmt.where(Script.status == status)
    if script_type is not None:
        stmt = stmt.where(Script.script_type == script_type)
    if topic_id is not None:
        stmt = stmt.where(Script.topic_id == topic_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@scripts_router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: UUID, db: AsyncSession = Depends(get_db)
) -> Script:
    """获取单个剧本。"""
    script = await db.get(Script, script_id)
    if script is None:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@scripts_router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: UUID,
    payload: ScriptUpdate,
    db: AsyncSession = Depends(get_db),
) -> Script:
    """更新剧本。"""
    script = await db.get(Script, script_id)
    if script is None:
        raise HTTPException(status_code=404, detail="Script not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(script, key, value)
    await db.commit()
    await db.refresh(script)
    return script


@scripts_router.delete("/{script_id}", status_code=204)
async def delete_script(
    script_id: UUID, db: AsyncSession = Depends(get_db)
) -> None:
    """删除剧本（级联删除分镜）。"""
    script = await db.get(Script, script_id)
    if script is None:
        raise HTTPException(status_code=404, detail="Script not found")
    await db.delete(script)
    await db.commit()


# ---------------------------------------------------------------------------
# 分镜路由
# ---------------------------------------------------------------------------


@storyboards_router.post("", response_model=StoryboardResponse, status_code=201)
async def create_storyboard(
    payload: StoryboardCreate, db: AsyncSession = Depends(get_db)
) -> Storyboard:
    """创建分镜。"""
    storyboard = Storyboard(**payload.model_dump())
    db.add(storyboard)
    await db.commit()
    await db.refresh(storyboard)
    return storyboard


@storyboards_router.get("", response_model=list[StoryboardResponse])
async def list_storyboards(
    script_id: UUID | None = None,
    status: StoryboardStatus | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[Storyboard]:
    """列出分镜，支持按剧本/状态过滤。"""
    stmt = select(Storyboard)
    if script_id is not None:
        stmt = stmt.where(Storyboard.script_id == script_id)
    if status is not None:
        stmt = stmt.where(Storyboard.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@storyboards_router.get("/{storyboard_id}", response_model=StoryboardResponse)
async def get_storyboard(
    storyboard_id: UUID, db: AsyncSession = Depends(get_db)
) -> Storyboard:
    """获取单个分镜。"""
    storyboard = await db.get(Storyboard, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="Storyboard not found")
    return storyboard


@storyboards_router.put("/{storyboard_id}", response_model=StoryboardResponse)
async def update_storyboard(
    storyboard_id: UUID,
    payload: StoryboardUpdate,
    db: AsyncSession = Depends(get_db),
) -> Storyboard:
    """更新分镜。"""
    storyboard = await db.get(Storyboard, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="Storyboard not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(storyboard, key, value)
    await db.commit()
    await db.refresh(storyboard)
    return storyboard


@storyboards_router.delete("/{storyboard_id}", status_code=204)
async def delete_storyboard(
    storyboard_id: UUID, db: AsyncSession = Depends(get_db)
) -> None:
    """删除分镜（级联删除镜头）。"""
    storyboard = await db.get(Storyboard, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="Storyboard not found")
    await db.delete(storyboard)
    await db.commit()


@storyboards_router.post(
    "/{storyboard_id}/shots", response_model=ShotResponse, status_code=201
)
async def create_shot(
    storyboard_id: UUID,
    payload: ShotCreate,
    db: AsyncSession = Depends(get_db),
) -> Shot:
    """为分镜新增镜头。"""
    storyboard = await db.get(Storyboard, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="Storyboard not found")
    shot = Shot(storyboard_id=storyboard_id, **payload.model_dump())
    db.add(shot)
    await db.commit()
    await db.refresh(shot)
    return shot


@storyboards_router.get(
    "/{storyboard_id}/shots", response_model=list[ShotResponse]
)
async def list_shots(
    storyboard_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[Shot]:
    """列出分镜的所有镜头，按镜头号升序。"""
    storyboard = await db.get(Storyboard, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="Storyboard not found")
    stmt = (
        select(Shot)
        .where(Shot.storyboard_id == storyboard_id)
        .order_by(Shot.shot_number.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@storyboards_router.put(
    "/{storyboard_id}/shots/{shot_id}", response_model=ShotResponse
)
async def update_shot(
    storyboard_id: UUID,
    shot_id: UUID,
    payload: ShotUpdate,
    db: AsyncSession = Depends(get_db),
) -> Shot:
    """更新镜头。"""
    shot = await db.get(Shot, shot_id)
    if shot is None or shot.storyboard_id != storyboard_id:
        raise HTTPException(status_code=404, detail="Shot not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(shot, key, value)
    await db.commit()
    await db.refresh(shot)
    return shot


@storyboards_router.delete(
    "/{storyboard_id}/shots/{shot_id}", status_code=204
)
async def delete_shot(
    storyboard_id: UUID,
    shot_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除镜头。"""
    shot = await db.get(Shot, shot_id)
    if shot is None or shot.storyboard_id != storyboard_id:
        raise HTTPException(status_code=404, detail="Shot not found")
    await db.delete(shot)
    await db.commit()


# ---------------------------------------------------------------------------
# 导演 / 编导方案路由
# ---------------------------------------------------------------------------


@directing_router.post("", response_model=DirectingResponse, status_code=201)
async def create_directing_plan(
    payload: DirectingCreate, db: AsyncSession = Depends(get_db)
) -> DirectingPlan:
    """创建导演/编导方案。"""
    plan = DirectingPlan(**payload.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@directing_router.get("", response_model=list[DirectingResponse])
async def list_directing_plans(
    script_id: UUID | None = None,
    role: DirectingRole | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[DirectingPlan]:
    """列出导演/编导方案，支持按剧本/角色过滤。"""
    stmt = select(DirectingPlan)
    if script_id is not None:
        stmt = stmt.where(DirectingPlan.script_id == script_id)
    if role is not None:
        stmt = stmt.where(DirectingPlan.role == role)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@directing_router.get("/{plan_id}", response_model=DirectingResponse)
async def get_directing_plan(
    plan_id: UUID, db: AsyncSession = Depends(get_db)
) -> DirectingPlan:
    """获取单个导演/编导方案。"""
    plan = await db.get(DirectingPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Directing plan not found")
    return plan


@directing_router.put("/{plan_id}", response_model=DirectingResponse)
async def update_directing_plan(
    plan_id: UUID,
    payload: DirectingUpdate,
    db: AsyncSession = Depends(get_db),
) -> DirectingPlan:
    """更新导演/编导方案。"""
    plan = await db.get(DirectingPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Directing plan not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    await db.commit()
    await db.refresh(plan)
    return plan


@directing_router.delete("/{plan_id}", status_code=204)
async def delete_directing_plan(
    plan_id: UUID, db: AsyncSession = Depends(get_db)
) -> None:
    """删除导演/编导方案。"""
    plan = await db.get(DirectingPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Directing plan not found")
    await db.delete(plan)
    await db.commit()


# ---------------------------------------------------------------------------
# 创作循环路由
# ---------------------------------------------------------------------------


@creation_router.post(
    "/runs", response_model=CreationRunResponse, status_code=201
)
async def start_creation_run(
    payload: CreationRunRequest,
    db: AsyncSession = Depends(get_db),
) -> CreationRun:
    """发起一次创作管线：小说 → 剧本 → 分镜 → 导演。"""
    kwargs: dict[str, Any] = {
        "max_rounds": payload.max_rounds,
        "options": payload.options,
        "review": payload.review,
        "auto_revise": payload.auto_revise,
        "max_revise_rounds": payload.max_revise_rounds,
        "budget_tokens": payload.budget_tokens,
    }
    if payload.stages:
        kwargs["stages"] = tuple(payload.stages)
    try:
        run = await run_creation(db, payload.topic_id, **kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return run


@creation_router.get("/runs", response_model=list[CreationRunResponse])
async def list_creation_runs(
    topic_id: UUID | None = None,
    status: CreationRunStatus | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[CreationRun]:
    """列出创作循环运行记录。"""
    stmt = select(CreationRun)
    if topic_id is not None:
        stmt = stmt.where(CreationRun.topic_id == topic_id)
    if status is not None:
        stmt = stmt.where(CreationRun.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


class CreationStatsResponse(BaseModel):
    """审查质量统计响应体。"""

    total_runs: int
    by_status: dict[str, int]
    avg_review_score: float | None = None
    avg_dimensions: dict[str, float] = Field(default_factory=dict)
    revision_outcomes: dict[str, int] = Field(default_factory=dict)
    trend: list[dict[str, Any]] = Field(default_factory=list)


@creation_router.get("/runs/stats", response_model=CreationStatsResponse)
async def creation_run_stats(
    db: AsyncSession = Depends(get_db),
) -> CreationStatsResponse:
    """创作审查质量统计（状态分布、平均分、维度均值、修订结果与趋势）。"""
    result = await db.execute(select(CreationRun))
    runs = list(result.scalars().all())

    by_status: dict[str, int] = {}
    revision_outcomes: dict[str, int] = {}
    scores = [r.review_score for r in runs if r.review_score is not None]
    dimension_sums: dict[str, list[float]] = {}
    for run in runs:
        status_key = run.status.value if run.status else "UNKNOWN"
        by_status[status_key] = by_status.get(status_key, 0) + 1
        outcome = run.revision_outcome.value if run.revision_outcome else "NONE"
        revision_outcomes[outcome] = revision_outcomes.get(outcome, 0) + 1
        review = run.review or {}
        for name, value in (review.get("dimensions") or {}).items():
            dimension_sums.setdefault(name, []).append(float(value))

    avg_dimensions = {
        name: round(sum(values) / len(values), 2)
        for name, values in dimension_sums.items()
        if values
    }

    trend: list[dict[str, Any]] = [
        {
            "run_id": str(run.id),
            "status": run.status.value if run.status else None,
            "review_score": run.review_score,
            "revise_rounds": run.revise_rounds,
            "created_at": run.created_at.isoformat(),
        }
        for run in runs[-10:]
    ]

    return CreationStatsResponse(
        total_runs=len(runs),
        by_status=by_status,
        avg_review_score=(
            round(sum(scores) / len(scores), 2) if scores else None
        ),
        avg_dimensions=avg_dimensions,
        revision_outcomes=revision_outcomes,
        trend=trend,
    )


@creation_router.get("/runs/{run_id}", response_model=CreationRunResponse)
async def get_creation_run(
    run_id: UUID, db: AsyncSession = Depends(get_db)
) -> CreationRun:
    """获取单个创作循环运行记录。"""
    run = await db.get(CreationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Creation run not found")
    return run


@creation_router.get("/runs/{run_id}/report")
async def get_creation_run_report(
    run_id: UUID,
    format: str = "markdown",
    db: AsyncSession = Depends(get_db),
) -> Response:
    """导出审查报告：``format=markdown``（默认）或 ``format=json``。"""
    run = await db.get(CreationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Creation run not found")

    if format == "json":
        payload = {
            "run_id": str(run.id),
            "status": run.status.value if run.status else None,
            "review_score": run.review_score,
            "review": run.review,
            "revision_outcome": (
                run.revision_outcome.value if run.revision_outcome else None
            ),
            "revise_rounds": run.revise_rounds,
            "revise_log": run.revise_log,
        }
        return Response(
            content=json.dumps(payload, ensure_ascii=False, indent=2),
            media_type="application/json; charset=utf-8",
        )

    return Response(
        content=render_run_report(run),
        media_type="text/markdown; charset=utf-8",
    )


# ---------------------------------------------------------------------------
# 故事状态（连续性权威）查询
# ---------------------------------------------------------------------------

class StoryStateResponse(BaseModel):
    """故事状态响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    novel_id: UUID
    tracking: dict[str, Any]
    characters: list[dict[str, Any]]
    foreshadowing: list[dict[str, Any]]
    goals: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@novels_router.get(
    "/{novel_id}/story-state", response_model=StoryStateResponse
)
async def get_novel_story_state(
    novel_id: UUID, db: AsyncSession = Depends(get_db)
) -> StoryState:
    """获取小说的连续性状态（唯一结构化权威状态）。"""
    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    result = await db.execute(
        select(StoryState).where(StoryState.novel_id == novel_id)
    )
    state = result.scalars().first()
    if state is None:
        raise HTTPException(status_code=404, detail="Story state not found")
    return state


class StorySearchHit(BaseModel):
    """检索命中项。"""

    source: str
    ref_id: str
    title: str
    snippet: str
    score: float


@novels_router.get(
    "/{novel_id}/story-state/search", response_model=list[StorySearchHit]
)
async def search_novel_story(
    novel_id: UUID,
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(default=5, ge=1, le=20),
    source: str | None = Query(None, pattern="^(chapter|state|foreshadowing)$"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """全文检索小说章节/状态卡/伏笔（BM25，中文子串可命中）。

    每次调用先重建该书的投影（幂等，规模 1–5 人团队足够）。
    """
    from hermes.content_team.creative.state_store import (
        StoryIndex,
        StoryIndexUnavailable,
    )

    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    index = StoryIndex(db)
    try:
        return await index.search(novel_id, q, limit=limit, source=source)
    except StoryIndexUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ---------------------------------------------------------------------------
# 多平台导出（B3）：番茄/起点 TXT、EPUB、红果短剧剧本
# ---------------------------------------------------------------------------


@novels_router.get("/{novel_id}/export")
async def export_novel(
    novel_id: UUID,
    format: str = Query("txt", pattern="^(txt|epub)$"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """导出小说：``format=txt``（分章 TXT）或 ``format=epub``。"""
    from hermes.content_team.creative.exporters import (
        export_novel_epub,
        export_novel_txt,
    )

    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    result = await db.execute(
        select(NovelChapter)
        .where(NovelChapter.novel_id == novel_id)
        .order_by(NovelChapter.chapter_number.asc())
    )
    chapters = [
        {"number": c.chapter_number, "title": c.title, "body": c.body}
        for c in result.scalars().all()
    ]

    if format == "epub":
        payload = export_novel_epub(novel.title, chapters)
        return Response(
            content=payload,
            media_type="application/epub+zip",
            headers={
                "Content-Disposition": f'attachment; filename="novel-{novel_id}.epub"'
            },
        )
    text = export_novel_txt(novel.title, chapters)
    return Response(
        content=text,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="novel-{novel_id}.txt"'
        },
    )


@scripts_router.get("/{script_id}/export")
async def export_script(
    script_id: UUID,
    format: str = Query("redfruit", pattern="^(redfruit|screenplay)$"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """导出剧本：``format=redfruit``（红果短剧格式）或 ``screenplay``（标准稿）。"""
    from hermes.content_team.creative.exporters import export_short_drama_script

    script = await db.get(Script, script_id)
    if script is None:
        raise HTTPException(status_code=404, detail="Script not found")

    shots: list[dict[str, Any]] = []
    sb_result = await db.execute(
        select(Storyboard).where(Storyboard.script_id == script_id)
    )
    for storyboard in sb_result.scalars().all():
        shot_result = await db.execute(
            select(Shot)
            .where(Shot.storyboard_id == storyboard.id)
            .order_by(Shot.shot_number.asc())
        )
        for shot in shot_result.scalars().all():
            shots.append(
                {
                    "shot_number": shot.shot_number,
                    "shot_size": shot.shot_size.value if shot.shot_size else "",
                    "camera_movement": (
                        shot.camera_movement.value if shot.camera_movement else ""
                    ),
                    "description": shot.description,
                }
            )

    text = export_short_drama_script(
        script.title, script.body, logline=script.logline, shots=shots or None
    )
    return Response(
        content=text,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="script-{script_id}.txt"'
        },
    )


# ---------------------------------------------------------------------------
# 写作台（B2）与创作→发布桥（B1）
# ---------------------------------------------------------------------------


class WritingDeskResponse(BaseModel):
    """写作台视图（创作者语言）。"""

    novel: dict[str, Any]
    progress: dict[str, Any]
    context_card: dict[str, Any]
    pending_foreshadowing: list[dict[str, Any]]
    continuity_warnings: list[dict[str, Any]]
    corpus_foreshadowing: dict[str, Any] | None = None
    recent_review: dict[str, Any] | None = None
    next_actions: list[str] = Field(default_factory=list)


@novels_router.get("/{novel_id}/writing-desk", response_model=WritingDeskResponse)
async def get_writing_desk(
    novel_id: UUID, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """写作台：今天写到哪、下一章交代什么、哪些伏笔要爆、连续性警告。"""
    from hermes.content_team.creative.writing_desk import build_writing_desk

    desk = await build_writing_desk(db, novel_id)
    if desk is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    return desk


class PublishRunRequest(BaseModel):
    """创作运行发布请求体。"""

    platform_account_ids: list[UUID] = Field(..., min_length=1)
    scheduled_at: datetime | None = None


@creation_router.post("/runs/{run_id}/publish", response_model=list[PublishTaskResponse])
async def publish_creation_run_endpoint(
    run_id: UUID,
    payload: PublishRunRequest,
    db: AsyncSession = Depends(get_db),
) -> list[PublishTask]:
    """把创作运行产物组装为内容并分发到平台（人工触发，不自动发布）。"""
    from hermes.content_team.creative.bridge import publish_creation_run

    try:
        tasks = await publish_creation_run(
            db,
            run_id,
            payload.platform_account_ids,
            scheduled_at=payload.scheduled_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return tasks


# ---------------------------------------------------------------------------
# 文风指纹（R15）与内容模板（R18）
# ---------------------------------------------------------------------------


class StyleFingerprintPut(BaseModel):
    """写入文风指纹请求体。"""

    samples: list[str] = Field(..., min_length=1)


@novels_router.put("/{novel_id}/style-fingerprint", response_model=NovelResponse)
async def set_novel_style_fingerprint(
    novel_id: UUID,
    payload: StyleFingerprintPut,
    db: AsyncSession = Depends(get_db),
) -> Novel:
    """从作者旧稿样本提取并持久化文风指纹（后续 run 可复用）。"""
    from hermes.content_team.creative.style_fingerprint import extract_fingerprint

    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    fingerprint = extract_fingerprint(payload.samples)
    if fingerprint.sample_chars <= 0:
        raise HTTPException(status_code=400, detail="样本为空，无法提取指纹")
    novel.style_fingerprint = fingerprint.to_dict()
    await db.commit()
    await db.refresh(novel)
    return novel


class TemplateResponse(BaseModel):
    """模板响应体。"""

    id: str
    name: str
    category: str
    description: str
    body: str
    variables: list[str]


class TemplateRenderRequest(BaseModel):
    """模板渲染请求体。"""

    variables: dict[str, Any] = Field(default_factory=dict)


templates_router = APIRouter()


@templates_router.get("/templates", response_model=list[TemplateResponse])
async def list_content_templates() -> list[dict[str, Any]]:
    """列出可用写作模板（内置 + content-creation/ 文档）。"""
    from hermes.content_team.creative.templates import list_templates

    return [t.to_dict() for t in list_templates()]


@templates_router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_content_template(template_id: str) -> dict[str, Any]:
    """获取单个模板。"""
    from hermes.content_team.creative.templates import get_template

    template = get_template(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.to_dict()


@templates_router.post("/templates/{template_id}/render")
async def render_content_template(
    template_id: str, payload: TemplateRenderRequest
) -> dict[str, Any]:
    """按变量渲染模板（缺省变量保留占位符）。"""
    from hermes.content_team.creative.templates import render_template

    rendered = render_template(template_id, payload.variables)
    if rendered is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"id": template_id, "rendered": rendered}


# ---------------------------------------------------------------------------
# 平台规则与时效性（R19）
# ---------------------------------------------------------------------------


@templates_router.get("/platform-rules")
async def get_platform_rules() -> dict[str, Any]:
    """平台规则快照 + 新鲜度检查（stale=True 表示需复核）。"""
    from hermes.content_team.creative.content_freshness import (
        check_freshness,
        load_platform_rules,
    )

    data = load_platform_rules()
    return {"rules": data, "freshness": check_freshness().to_dict()}


# ---------------------------------------------------------------------------
# 语料库（R19 续）
# ---------------------------------------------------------------------------


@templates_router.get("/corpus")
async def list_corpus(
    genre: str | None = Query(None),
    tag: str | None = Query(None),
    form: str | None = Query(None),
) -> dict[str, Any]:
    """列出语料案例（可按题材/技法标签/形态筛选）。"""
    from hermes.content_team.creative.corpus import find_cases, load_corpus_index

    cases = find_cases(genre=genre, tag=tag, form=form)
    return {
        "total": len(load_corpus_index()),
        "matched": len(cases),
        "cases": [c.to_dict() for c in cases],
    }


@templates_router.get("/corpus/{case_id}")
async def get_corpus_case(case_id: str) -> dict[str, Any]:
    """获取单个语料案例条目。"""
    from hermes.content_team.creative.corpus import get_case

    case = get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Corpus case not found")
    return case.to_dict()
