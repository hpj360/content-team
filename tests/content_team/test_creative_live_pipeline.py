"""实网联调 · 全链路（Round 14）：真实 LLM 驱动完整创作管线 + 质量评测。

默认跳过（不污染 CI）；显式开启：
    set CONTENT_TEAM_LIVE_LLM=1
    set HERMES_LLM_PROVIDER=zai
    set HERMES_LLM_MODEL=glm-4-flash
    # ZAI_API_KEY 已在环境中
"""
from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import hermes.content_team.creative.pipeline as pipeline_module
from hermes.content_team.db import Base
from hermes.content_team.creative.builders_llm import make_script_drafter
from hermes.content_team.creative.quality_eval import (
    compare_variants,
    load_quality_evals,
    measure_draft,
)
from hermes.content_team.creative.reviewer import review_creation
from hermes.content_team.creative.pipeline import StageRoles
from hermes.content_team.models.topic import Topic

LIVE = os.environ.get("CONTENT_TEAM_LIVE_LLM") == "1"

pytestmark = pytest.mark.skipif(
    not LIVE, reason="set CONTENT_TEAM_LIVE_LLM=1 to run live pipeline tests"
)


def _client():
    from hermes.workbench.llm import make_llm_client

    return make_llm_client()


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


async def _make_topic(session, title: str, description: str) -> Topic:
    topic = Topic(title=title, description=description)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    return topic


async def test_live_full_pipeline_with_real_drafter(session):
    """真实 LLM 驱动完整管线：小说→剧本→分镜→导演，并产出审查报告。"""
    topic = await _make_topic(
        session, "外卖员逆袭", "外卖员在庆功宴被羞辱，被迫签下七天总裁协议"
    )
    drafter = make_script_drafter(_client())

    run = await pipeline_module.run_creation(
        session,
        topic.id,
        roles=StageRoles(drafter=drafter),
        retrieval=False,  # NOVEL 阶段尚无检索源，关闭以省 token
    )

    assert run.status.value in {"SUCCEEDED", "NEEDS_REVISION"}, run.error_message
    assert run.artifacts.get("script_id")
    assert run.review is not None and run.review.get("dimensions")

    # 剧本正文来自真实 LLM（非模板标记）
    from hermes.content_team.models.creative import Script

    script = await session.get(Script, uuid.UUID(run.artifacts["script_id"]))
    assert script is not None and len(script.body) > 80
    assert "（场景占位" not in script.body

    print("\n[live pipeline] status=", run.status.value,
          "| score=", run.review_score,
          "| script_chars=", len(script.body))
    print("[live pipeline] stage_issues=", run.review.get("stage_issues"))


async def test_live_quality_eval_baseline_vs_style(session):
    """质量评测：同一选题在基线与风格锚定下的指标对比（真实 LLM）。"""
    evals = load_quality_evals()
    topic_spec = evals["topics"][0]
    topic = await _make_topic(session, topic_spec["title"], topic_spec["description"])

    rows = []
    for variant in evals["variants"]:
        drafter = make_script_drafter(_client())
        options = dict(variant.get("options") or {})
        run = await pipeline_module.run_creation(
            session,
            topic.id,
            roles=StageRoles(drafter=drafter),
            options=options,
            retrieval=False,
        )
        from hermes.content_team.models.creative import Script

        script = await session.get(Script, uuid.UUID(run.artifacts["script_id"]))
        metrics = measure_draft(
            {"body": script.body},
            topic=topic_spec,
            variant_id=variant["id"],
            logline=script.logline,
        )
        rows.append(metrics)
        print(f"\n[live quality] variant={variant['id']} metrics={metrics.to_dict()}")

    by_variant = compare_variants(rows)
    print("[live quality] summary=", by_variant)
    # 至少生成出可评测的稿子（指标已产出）
    assert len(by_variant) == len(evals["variants"])
    assert all(v["n"] == 1 for v in by_variant.values())


async def test_live_review_on_real_content(session):
    """真实 LLM 内容 + 独立审查：审查能读到正文并给出问题（不空转）。"""
    topic = await _make_topic(
        session, "深海科考队失踪", "深海科考队在万米海沟集体失踪"
    )
    drafter = make_script_drafter(_client())
    run = await pipeline_module.run_creation(
        session, topic.id, roles=StageRoles(drafter=drafter), retrieval=False
    )
    report = await review_creation(session, run.artifacts)
    assert report.dimensions
    print("\n[live review] score=", report.score, "| issues=", report.stage_issues)
