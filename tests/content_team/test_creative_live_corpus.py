"""R23 实网对照（opt-in）：语料注入是否有效 + judge provider 探测。

    set CONTENT_TEAM_LIVE_LLM=1
    set HERMES_LLM_PROVIDER=zai
    set HERMES_LLM_MODEL=glm-4-flash
    # 可选：set CONTENT_TEAM_JUDGE_PROVIDER=moonshot CONTENT_TEAM_JUDGE_MODEL=kimi-k2

运行后按控制台对比表更新 knowledge/creative-tuning-report.md。
"""
from __future__ import annotations

import json
import os
import uuid

import pytest

import hermes.content_team.creative.pipeline as pipeline_module
from hermes.content_team.creative.builders_llm import make_script_drafter
from hermes.content_team.creative.judges import build_judge
from hermes.content_team.creative.planners import make_beat_sheet_planner
from hermes.content_team.creative.prompts import DEFAULT_VARIANT
from hermes.content_team.creative.quality_eval import (
    load_quality_evals,
    measure_draft,
    parse_judge_score,
)

LIVE = os.environ.get("CONTENT_TEAM_LIVE_LLM") == "1"

pytestmark = pytest.mark.skipif(
    not LIVE, reason="set CONTENT_TEAM_LIVE_LLM=1 to run live corpus-effect test"
)


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


async def test_live_corpus_injection_effect():
    """同一选题、同一提示词变体：语料注入 on/off 的指标 + judge 分对比。"""
    evals = load_quality_evals()
    # 选与语料强相关的选题（外卖员逆袭 → shortdrama-waimai-example）
    spec = next(t for t in evals["topics"] if t["id"] == "waimai-counterattack")

    engine, factory = await _session()
    judge = build_judge()
    rows = []
    try:
        async with factory() as session:
            from hermes.content_team.models.creative import Script
            from hermes.content_team.models.topic import Topic

            for corpus_on in (False, True):
                topic = Topic(title=spec["title"], description=spec["description"])
                session.add(topic)
                await session.commit()
                await session.refresh(topic)

                drafter = make_script_drafter(_client(), prompt_variant=DEFAULT_VARIANT)
                run = await pipeline_module.run_creation(
                    session,
                    topic.id,
                    roles=pipeline_module.StageRoles(
                        planner=make_beat_sheet_planner(include_corpus=corpus_on),
                        drafter=drafter,
                    ),
                    retrieval=False,
                    review=False,
                )
                script = await session.get(
                    Script, uuid.UUID(run.artifacts["script_id"])
                )
                metrics = measure_draft(
                    {"body": script.body},
                    topic=spec,
                    variant_id="corpus-on" if corpus_on else "corpus-off",
                    logline=script.logline,
                    retrieval=None,
                )
                notes = await judge(
                    __import__(
                        "hermes.content_team.models.creative", fromlist=["CreationStage"]
                    ).CreationStage.SCRIPT,
                    {"script_title": script.title, "preview": script.body},
                    {"topic": topic},
                )
                score = parse_judge_score(notes)
                rows.append((metrics.variant_id, metrics, score))
                print(
                    f"[corpus] {metrics.variant_id}: chars={metrics.draft_chars} "
                    f"scenes={metrics.scene_count} gate={metrics.gate_passed} "
                    f"judge={score}"
                )
    finally:
        await engine.dispose()

    print(
        "\n[corpus] table=",
        json.dumps(
            [
                {"variant": v, "chars": m.draft_chars, "scenes": m.scene_count,
                 "gate": m.gate_passed, "judge": s}
                for v, m, s in rows
            ],
            ensure_ascii=False,
            indent=2,
        ),
    )
    assert len(rows) == 2
    assert all(m.draft_chars > 0 for _v, m, _s in rows)


def test_live_judge_provider_config():
    """探测 judge provider 配置：跨 provider 可用则报告，否则回退同源。"""
    cross = os.environ.get("CONTENT_TEAM_JUDGE_PROVIDER")
    judge = build_judge()
    assert judge is not None
    print(f"\n[judge] cross-provider={cross or '(未配置，回退同源)'}")
