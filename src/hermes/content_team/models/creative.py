"""创作领域数据模型：小说、剧本、分镜、导演/编导方案与创作循环。

这些实体构成"小说 → 剧本 → 分镜 → 导演"的创作管线，均可通过外键关联
到既有 ``Topic`` / ``Content``，从而接入选题与发布体系。
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hermes.content_team.db import GUID, Base


class NovelStatus(str, enum.Enum):
    """小说状态枚举。"""

    PLANNING = "PLANNING"
    DRAFTING = "DRAFTING"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class ScriptType(str, enum.Enum):
    """剧本类型枚举。"""

    FEATURE = "FEATURE"          # 电影 / 长片
    SHORT_DRAMA = "SHORT_DRAMA"  # 短剧
    MICRO = "MICRO"              # 微短剧 / 短视频脚本
    STAGE = "STAGE"              # 舞台剧
    VARIETY = "VARIETY"          # 综艺 / 栏目


class ScriptStatus(str, enum.Enum):
    """剧本状态枚举。"""

    DRAFT = "DRAFT"
    REVISING = "REVISING"
    FINAL = "FINAL"
    ARCHIVED = "ARCHIVED"


class StoryboardStatus(str, enum.Enum):
    """分镜状态枚举。"""

    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    ARCHIVED = "ARCHIVED"


class ShotSize(str, enum.Enum):
    """景别枚举。"""

    EXTREME_WIDE = "EXTREME_WIDE"    # 大远景
    WIDE = "WIDE"                    # 远景
    FULL = "FULL"                    # 全景
    MEDIUM = "MEDIUM"                # 中景
    MEDIUM_CLOSE = "MEDIUM_CLOSE"    # 中近景
    CLOSE = "CLOSE"                  # 近景
    EXTREME_CLOSE = "EXTREME_CLOSE"  # 特写


class CameraMovement(str, enum.Enum):
    """运镜方式枚举。"""

    STATIC = "STATIC"        # 固定
    PAN = "PAN"              # 摇镜
    TILT = "TILT"            # 俯仰
    DOLLY = "DOLLY"          # 推拉
    TRACKING = "TRACKING"    # 跟移
    ZOOM = "ZOOM"            # 变焦
    CRANE = "CRANE"          # 升降
    HANDHELD = "HANDHELD"    # 手持


class DirectingRole(str, enum.Enum):
    """导演/编导方案定位。"""

    SHOWRUNNER = "SHOWRUNNER"  # 编导
    DIRECTOR = "DIRECTOR"      # 导演


class DirectingStatus(str, enum.Enum):
    """导演/编导方案状态枚举。"""

    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    ARCHIVED = "ARCHIVED"


class CreationStage(str, enum.Enum):
    """创作管线阶段。"""

    NOVEL = "NOVEL"
    SCRIPT = "SCRIPT"
    STORYBOARD = "STORYBOARD"
    DIRECTING = "DIRECTING"


class CreationRunStatus(str, enum.Enum):
    """创作循环运行状态枚举。"""

    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    NEEDS_REVISION = "NEEDS_REVISION"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class RevisionOutcome(str, enum.Enum):
    """自动修订结果枚举。"""

    NONE = "NONE"
    FIXED = "FIXED"          # 修订后审查通过
    UNCHANGED = "UNCHANGED"  # 修订未改变问题
    EXHAUSTED = "EXHAUSTED"  # 修订轮次耗尽，仍失败


def _utcnow() -> datetime:
    """返回带时区的当前 UTC 时间。"""
    return datetime.now(timezone.utc)


class Novel(Base):
    """小说模型。"""

    __tablename__ = "novels"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.ForeignKey("topics.id"), nullable=True
    )
    content_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.ForeignKey("contents.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    genre: Mapped[str] = mapped_column(sa.String(100), nullable=False, default="")
    logline: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    synopsis: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    status: Mapped[NovelStatus] = mapped_column(
        sa.Enum(NovelStatus), nullable=False, default=NovelStatus.PLANNING
    )
    target_word_count: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=0
    )
    word_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    chapters: Mapped[list[NovelChapter]] = relationship(
        back_populates="novel", cascade="all, delete-orphan"
    )


class NovelChapter(Base):
    """小说章节模型。"""

    __tablename__ = "novel_chapters"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    novel_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("novels.id"), nullable=False
    )
    chapter_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False, default="")
    body: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    word_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        sa.String(50), nullable=False, default="draft"
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    novel: Mapped[Novel] = relationship(back_populates="chapters")

    @staticmethod
    def compute_word_count(body: str) -> int:
        """统计正文有效字数（去除空白字符）。"""
        return len("".join(body.split()))


class Script(Base):
    """剧本模型。"""

    __tablename__ = "scripts"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.ForeignKey("topics.id"), nullable=True
    )
    content_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.ForeignKey("contents.id"), nullable=True
    )
    novel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.ForeignKey("novels.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    script_type: Mapped[ScriptType] = mapped_column(
        sa.Enum(ScriptType), nullable=False, default=ScriptType.MICRO
    )
    logline: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    body: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    status: Mapped[ScriptStatus] = mapped_column(
        sa.Enum(ScriptStatus), nullable=False, default=ScriptStatus.DRAFT
    )
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    storyboards: Mapped[list[Storyboard]] = relationship(
        back_populates="script", cascade="all, delete-orphan"
    )


class Storyboard(Base):
    """分镜模型。"""

    __tablename__ = "storyboards"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    script_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.ForeignKey("scripts.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    status: Mapped[StoryboardStatus] = mapped_column(
        sa.Enum(StoryboardStatus), nullable=False, default=StoryboardStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    script: Mapped[Optional[Script]] = relationship(back_populates="storyboards")
    shots: Mapped[list[Shot]] = relationship(
        back_populates="storyboard", cascade="all, delete-orphan"
    )


class Shot(Base):
    """镜头模型（分镜下的单个镜头）。"""

    __tablename__ = "shots"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    storyboard_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("storyboards.id"), nullable=False
    )
    shot_number: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)
    shot_size: Mapped[ShotSize] = mapped_column(
        sa.Enum(ShotSize), nullable=False, default=ShotSize.MEDIUM
    )
    camera_movement: Mapped[CameraMovement] = mapped_column(
        sa.Enum(CameraMovement), nullable=False, default=CameraMovement.STATIC
    )
    description: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    dialogue: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    sound: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    duration_seconds: Mapped[float] = mapped_column(
        sa.Float, nullable=False, default=0.0
    )
    notes: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    storyboard: Mapped[Storyboard] = relationship(back_populates="shots")


class DirectingPlan(Base):
    """导演/编导方案模型。

    ``role`` 区分「导演阐述」（DIRECTOR）与「编导方案」（SHOWRUNNER），
    二者共享同一套字段，便于复用同一套管线与接口。
    """

    __tablename__ = "directing_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    script_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.ForeignKey("scripts.id"), nullable=True
    )
    storyboard_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.ForeignKey("storyboards.id"), nullable=True
    )
    role: Mapped[DirectingRole] = mapped_column(
        sa.Enum(DirectingRole), nullable=False, default=DirectingRole.DIRECTOR
    )
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    style: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    tone: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    pacing: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    visual_reference: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    director_notes: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    status: Mapped[DirectingStatus] = mapped_column(
        sa.Enum(DirectingStatus), nullable=False, default=DirectingStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )


class CreationRun(Base):
    """创作循环运行记录。

    记录一次「小说 → 剧本 → 分镜 → 导演」管线的执行过程。``stage_results``
    保存每个阶段每轮的 builder/checker 结果快照（JSON）。
    """

    __tablename__ = "creation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.ForeignKey("topics.id"), nullable=True
    )
    stages: Mapped[list[str]] = mapped_column(
        sa.JSON, nullable=False, default=list
    )
    current_stage: Mapped[Optional[CreationStage]] = mapped_column(
        sa.Enum(CreationStage), nullable=True
    )
    status: Mapped[CreationRunStatus] = mapped_column(
        sa.Enum(CreationRunStatus), nullable=False, default=CreationRunStatus.RUNNING
    )
    max_rounds: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=3)
    rounds: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    stage_results: Mapped[list[dict]] = mapped_column(
        sa.JSON, nullable=False, default=list
    )
    artifacts: Mapped[dict] = mapped_column(
        sa.JSON, nullable=False, default=dict
    )
    review: Mapped[Optional[dict]] = mapped_column(sa.JSON, nullable=True)
    review_score: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True)
    revise_rounds: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    revision_outcome: Mapped[Optional[RevisionOutcome]] = mapped_column(
        sa.Enum(RevisionOutcome), nullable=True
    )
    revise_log: Mapped[list[dict]] = mapped_column(
        sa.JSON, nullable=False, default=list
    )
    error_message: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )


class StoryState(Base):
    """故事状态模型（唯一结构化权威状态）。

    对应 novel-writing 的"状态落盘与连续性契约"：7 栏状态卡、角色状态、
    伏笔契约、目标分层。``Novel`` 1:1 关联，审查器据此做 schema 校验。
    """

    __tablename__ = "story_states"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    novel_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("novels.id"), nullable=False, unique=True
    )
    tracking: Mapped[dict] = mapped_column(sa.JSON, nullable=False, default=dict)
    characters: Mapped[list[dict]] = mapped_column(
        sa.JSON, nullable=False, default=list
    )
    foreshadowing: Mapped[list[dict]] = mapped_column(
        sa.JSON, nullable=False, default=list
    )
    goals: Mapped[dict] = mapped_column(sa.JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )
