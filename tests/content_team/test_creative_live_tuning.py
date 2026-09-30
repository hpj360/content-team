"""R15 调优 pass（实网，opt-in）：变体 × 选题 → 指标对比 → 选定默认。

    set CONTENT_TEAM_LIVE_LLM=1
    set HERMES_LLM_PROVIDER=zai
    set HERMES_LLM_MODEL=glm-4-flash

运行后把控制台表格写入 knowledge/creative-tuning-report.md（人工归档）。
"""
from __future__ import annotations

import json
import os

import pytest

import hermes.content_team.creative.pipeline as pipeline_module
from hermes.content_team.creative.builders_llm import make_script_drafter
from hermes.content_team.creative.judges import make_llm_judge
from hermes.content_team.creative.pipeline import StageRoles
from hermes.content_team.creative.prompts import available_variants
from hermes.content_team.models.creative import CreationStage
from hermes.content_team.creative.quality_eval import (
    compare_variants,
    load_quality_evals,
    measure_draft,
    parse_judge_score,
    summarize_judge,
)

LIVE = os.environ.get("CONTENT_TEAM_LIVE_LLM") == "1"

pytestmark = pytest.mark.skipif(
    not LIVE, reason="set CONTENT_TEAM_LIVE_LLM=1 to run live tuning"
)

# 调优采样规模（控制成本）：默认 5 选题 × 3 变体
_TOPIC_LIMIT = int(os.environ.get("CONTENT_TEAM_TUNING_TOPICS", "5"))
_ENABLE_JUDGE = os.environ.get("CONTENT_TEAM_TUNING_JUDGE", "1") != "0"


def _client():
    from hermes.workbench.llm import make_llm_client

    return make_llm_client()


async def _session():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    from hermes.content_team.db import Base

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def test_live_variant_tuning():
    """对每个变体在若干选题上生成并度量，输出对比表。"""
    evals = load_quality_evals()
    topics = evals["topics"][:_TOPIC_LIMIT]
    variants = [v for v in available_variants() if v in {"v1", "v2", "v3"}]

    engine, factory = await _session()
    rows = []
    judge_scores: dict[str, list[float]] = {}
    try:
        async with factory() as session:
            from hermes.content_team.models.creative import Script
            from hermes.content_team.models.topic import Topic

            topic_rows = []
            for spec in topics:
                topic = Topic(title=spec["title"], description=spec["description"])
                session.add(topic)
                await session.commit()
                await session.refresh(topic)
                topic_rows.append((spec, topic))

            judge = make_llm_judge(_client()) if _ENABLE_JUDGE else None

            for spec, topic in topic_rows:
                for variant in variants:
                    drafter = make_script_drafter(_client(), prompt_variant=variant)
                    run = await pipeline_module.run_creation(
                        session,
                        topic.id,
                        roles=StageRoles(drafter=drafter),
                        retrieval=False,
                        review=False,  # 调优只测生成，不跑审查以省 token
                    )
                    script = await session.get(
                        Script, __import__("uuid").UUID(run.artifacts["script_id"])
                    )
                    metrics = measure_draft(
                        {"body": script.body},
                        topic=spec,
                        variant_id=variant,
                        logline=script.logline,
                    )
                    rows.append(metrics)

                    judge_score = None
                    if judge is not None:
                        notes = await judge(
                            CreationStage.SCRIPT,
                            {"script_title": script.title, "preview": script.body},
                            {"topic": topic},
                        )
                        judge_score = parse_judge_score(notes)
                        judge_scores.setdefault(variant, []).append(
                            judge_score if judge_score is not None else -1.0
                        )

                    print(
                        f"[tuning] topic={spec['id'][:14]} variant={variant} "
                        f"chars={metrics.draft_chars} scenes={metrics.scene_count} "
                        f"gate={metrics.gate_passed} deai={metrics.deai_hits_before} "
                        f"judge={judge_score}"
                    )
    finally:
        await engine.dispose()

    summary = compare_variants(rows)
    print("\n[tuning] structural=", json.dumps(summary, ensure_ascii=False, indent=2))

    if judge_scores:
        # -1.0 为"未返回分数"的哨兵，聚合时剔除
        cleaned = {
            variant: [v for v in values if v >= 0] for variant, values in judge_scores.items()
        }
        print(
            "\n[tuning] semantic=",
            json.dumps(summarize_judge(cleaned), ensure_ascii=False, indent=2),
        )

    # 变体对比必须产出完整矩阵
    assert set(summary) == set(variants)
    assert all(v["n"] == len(topics) for v in summary.values())
    assert any(v["avg_chars"] > 0 for v in summary.values())
