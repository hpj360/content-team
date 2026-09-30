"""阶段内规划器（创作者视角 Round 7 · A1）。

把"状态与记忆"层**接线到写侧**：写某一章/某一集之前，先按主题检索已有
状态（章节正文 / 状态卡 / 待回收伏笔），把命中片段注入 builder 上下文，
让生成内容与既有设定对账——直接回应创作者第一痛点「伏笔忘回收、人设漂移」。

不依赖 LLM，纯检索；LLM 版规划器可另行注入（`StageRoles.planner`）。
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from hermes.content_team.creative.state_store import StoryIndex
from hermes.content_team.models.creative import CreationStage

# 检索注入的上下文键名（builder 消费）
RETRIEVAL_KEY = "retrieval"
_MAX_HITS = 3
_QUERY_CHARS = 40


def derive_query(stage: CreationStage, ctx: dict[str, Any]) -> str:
    """按阶段推导检索词：优先显式 `options.retrieval_query`，否则取选题描述。"""
    explicit = str(ctx.get("retrieval_query") or "").strip()
    if explicit:
        return explicit
    topic = ctx.get("topic")
    description = str(getattr(topic, "description", "") or "").strip()
    if description:
        return description[:_QUERY_CHARS]
    title = str(getattr(topic, "title", "") or "").strip()
    return title[:_QUERY_CHARS]


def make_retrieval_planner(db: AsyncSession):
    """构造检索规划器：写前把相关既有设定注入 builder 上下文。

    仅在已有小说（``ctx['novel_id']``）的阶段生效（NOVEL 阶段尚无书，返回空）。
    """

    async def planner(
        stage: CreationStage, ctx: dict[str, Any]
    ) -> dict[str, Any]:
        if stage is CreationStage.NOVEL:
            return {}
        novel_id = ctx.get("novel_id")
        if not novel_id:
            return {}
        query = derive_query(stage, ctx)
        if not query:
            return {}
        try:
            hits = await StoryIndex(db).search(
                uuid.UUID(str(novel_id)), query, limit=_MAX_HITS
            )
        except Exception:  # noqa: BLE001  # FTS5 不可用等 → 降级为无检索
            return {}
        if not hits:
            return {}
        return {RETRIEVAL_KEY: hits}

    return planner


def render_retrieval_block(hits: list[dict[str, Any]]) -> str:
    """把检索命中渲染为可写入正文的"一致性参考"区块。"""
    if not hits:
        return ""
    lines = ["【一致性参考】"]
    for hit in hits:
        lines.append(f"- {hit.get('title', '')}：{hit.get('snippet', '')}")
    return "\n".join(lines)
