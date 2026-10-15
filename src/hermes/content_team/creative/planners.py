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

from hermes.content_team.creative.corpus import (
    corpus_refs_for,
    foreshadowing_plan_for,
)
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


# ---------------------------------------------------------------------------
# 默认节奏规划器（R17）：把选题信息映射为可执行写作参数
# ---------------------------------------------------------------------------

_GENRE_SCENE_HINTS: tuple[tuple[str, int, str], ...] = (
    ("短剧", 3, "快节奏：3/30/60 公式，单集强钩子"),
    ("微短剧", 3, "快节奏：3/30/60 公式，单集强钩子"),
    ("悬疑", 3, "中速：线索分层，每场留信息缺口"),
    ("言情", 3, "中速：关系位移驱动，冲突快解"),
    ("甜宠", 3, "中速：心动信号每 2–3 场一次"),
    ("都市", 3, "偏快：打脸密度优先"),
    ("玄幻", 4, "偏快：升级与打脸交替"),
    ("仙侠", 4, "偏快：境界推进可见"),
    ("科幻", 4, "中速：设定自洽优先"),
    ("历史", 4, "中速：布局—见效—扬名循环"),
)


def make_beat_sheet_planner(*, include_corpus: bool = True):
    """默认节奏规划器：依据选题题材给出剧本类型/场景数/节奏提示。

    ``include_corpus=False`` 时不引用语料案例（用于对照实验：语料注入是否有效）。
    纯规则、零成本；LLM 版规划器可另行注入覆盖。
    """

    async def planner(
        stage: CreationStage, ctx: dict[str, Any]
    ) -> dict[str, Any]:
        topic = ctx.get("topic")
        text = (
            f"{getattr(topic, 'title', '')} {getattr(topic, 'description', '')}"
            f" {ctx.get('genre', '')} {ctx.get('script_type', '')}"
        )
        refs = corpus_refs_for(text, limit=2) if include_corpus else []

        if stage is CreationStage.NOVEL:
            # NOVEL：提供结构化伏笔种子（由 seed_foreshadowing 决定是否落库）
            seed = foreshadowing_plan_for(text, limit=2) if include_corpus else []
            plan: dict[str, Any] = {}
            if seed:
                plan["foreshadowing_seed"] = seed
            if refs:
                plan["corpus_refs"] = refs
            return plan

        if stage is not CreationStage.SCRIPT:
            return {}

        target_scenes, pacing = 3, "中速：冲突递进，每场价值转折"
        for keyword, scenes, hint in _GENRE_SCENE_HINTS:
            if keyword and keyword in text:
                target_scenes, pacing = scenes, hint
                break
        plan = {
            "target_scenes": target_scenes,
            "pacing_hint": pacing,
            "beat_sheet": "三幕：建置→对抗→转折",
        }
        if refs:
            plan["corpus_refs"] = refs
        return plan

    return planner


# 知识检索注入的上下文键名（builder 消费）
KNOWLEDGE_KEY = "knowledge_refs"

# 默认参与检索的知识类别（方法论 + 语料）
_KNOWLEDGE_CATEGORIES = ("skill-reference", "corpus")


def make_knowledge_planner(
    *,
    limit: int = 3,
    categories: tuple[str, ...] = _KNOWLEDGE_CATEGORIES,
):
    """知识库检索规划器（R29）：写前把相关知识资产注入 builder 上下文。

    复用 ``knowledge_base.search_knowledge`` 按选题关键词检索技能方法论与语料案例，
    使知识库从"可查"变为"自动消费"。纯检索、零 LLM 成本。
    """

    async def planner(
        stage: CreationStage, ctx: dict[str, Any]
    ) -> dict[str, Any]:
        from hermes.content_team.creative.knowledge_base import search_knowledge

        query = derive_query(stage, ctx)
        if not query:
            return {}
        hits = search_knowledge(query, limit=limit * 3)
        picked = [h for h in hits if h.get("category") in categories][:limit]
        if not picked:
            return {}
        return {
            KNOWLEDGE_KEY: [
                {
                    "title": h.get("title"),
                    "category": h.get("category"),
                    "path": h.get("path"),
                    "summary": h.get("summary"),
                }
                for h in picked
            ]
        }

    return planner


def compose_planners(*planners) -> Any:
    """把多个 planner 组合为一个（后者覆盖前者的同名字段）。"""
    active = [p for p in planners if p is not None]

    async def planner(
        stage: CreationStage, ctx: dict[str, Any]
    ) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for item in active:
            result = await item(stage, ctx) or {}
            merged.update(result)
        return merged

    return planner
