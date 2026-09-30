"""创作→发布桥（创作者视角 Round 10 · B1）。

把已通过审查的创作产物（剧本 + 分镜 + 导演阐述）组装成平台 `Content`，
再复用既有 `PublishDispatcher` 分发到平台账号——打通
「选题 → 创作 → 审查 → 发布 → 数据」的平台主链。

注意：桥接是**人工触发**（作者确认交付后再发布），不做自动发布。
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hermes.content_team.models.content import Content, ContentStatus
from hermes.content_team.models.creative import (
    CreationRun,
    DirectingPlan,
    Script,
    Shot,
    Storyboard,
)
from hermes.content_team.publish.dispatcher import PublishDispatcher

# 创作剧本 → 平台内容类型映射
_CONTENT_TYPE = "video_script"


def assemble_content_body(
    script: Script,
    shots: list[dict[str, Any]],
    directing_notes: str = "",
) -> str:
    """组装发布正文：剧本正文 + 分镜摘要 + 导演阐述。"""
    parts: list[str] = [str(script.body or "").strip()]
    if shots:
        lines = ["", "【分镜】"]
        for shot in shots:
            lines.append(
                f"镜{shot.get('shot_number')}｜{shot.get('shot_size')}｜"
                f"{shot.get('camera_movement')}｜"
                f"{str(shot.get('description') or '').strip()}"
            )
        parts.append("\n".join(lines))
    if directing_notes.strip():
        parts.append("\n【导演阐述】\n" + directing_notes.strip())
    return "\n".join(p for p in parts if p).strip()


async def publish_creation_run(
    db: AsyncSession,
    run_id: Any,
    platform_account_ids: list[Any],
    *,
    scheduled_at: Any | None = None,
) -> list[Any]:
    """把一次创作运行的产物组装为内容并分发；返回发布任务列表。

    抛出 ``ValueError``：运行不存在 / 缺少剧本产物 / 产物缺失。
    """
    run = await db.get(CreationRun, run_id)
    if run is None:
        raise ValueError("Creation run not found")

    artifacts = run.artifacts or {}
    script_id = artifacts.get("script_id")
    if not script_id:
        raise ValueError("创作运行缺少剧本产物，无法发布")

    script = await db.get(Script, uuid.UUID(str(script_id)))
    if script is None:
        raise ValueError("剧本产物已不存在")

    shots: list[dict[str, Any]] = []
    storyboard_id = artifacts.get("storyboard_id")
    if storyboard_id:
        storyboard = await db.get(Storyboard, uuid.UUID(str(storyboard_id)))
        if storyboard is not None:
            shot_result = await db.execute(
                select(Shot)
                .where(Shot.storyboard_id == storyboard.id)
                .order_by(Shot.shot_number.asc())
            )
            shots = [
                {
                    "shot_number": s.shot_number,
                    "shot_size": s.shot_size.value if s.shot_size else "",
                    "camera_movement": (
                        s.camera_movement.value if s.camera_movement else ""
                    ),
                    "description": s.description,
                }
                for s in shot_result.scalars().all()
            ]

    directing_notes = ""
    plan_id = artifacts.get("directing_plan_id")
    if plan_id:
        plan = await db.get(DirectingPlan, uuid.UUID(str(plan_id)))
        if plan is not None:
            directing_notes = plan.director_notes or ""

    content = Content(
        topic_id=run.topic_id,
        title=script.title,
        body=assemble_content_body(script, shots, directing_notes),
        content_type=_CONTENT_TYPE,
        status=ContentStatus.APPROVED,
    )
    db.add(content)
    await db.flush()

    # 回填剧本 → 内容的关联（创作侧可追溯）
    script.content_id = content.id
    await db.flush()

    dispatcher = PublishDispatcher(db_session=db)
    tasks = await dispatcher.dispatch(
        content_id=content.id,
        platform_accounts=platform_account_ids,
        scheduled_at=scheduled_at,
    )
    await db.commit()
    return tasks
