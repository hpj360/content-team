"""R22：语料注入生成 + 伏笔自动对账 测试。"""
from __future__ import annotations

import uuid

import hermes.content_team.creative.pipeline as pipeline_module
from hermes.content_team.creative.builders_llm import make_script_drafter
from hermes.content_team.creative.corpus import (
    corpus_payload_for,
    foreshadowing_plan_for,
    load_corpus_index,
    reconcile_foreshadowing,
)
from hermes.content_team.creative.planners import make_beat_sheet_planner
from hermes.content_team.models.creative import CreationStage

from tests.content_team._fakes import FakeLlmClient


async def _session_from_app():
    from hermes.content_team.app import app
    from hermes.content_team.db import get_db

    gen = app.dependency_overrides[get_db]()
    return gen, await gen.__anext__()


# ---------------------------------------------------------------------------
# 语料结构化伏笔计划
# ---------------------------------------------------------------------------


def test_corpus_cases_carry_foreshadowing_plan():
    with_plan = [c for c in load_corpus_index() if c.foreshadowing_plan]
    assert {"shortdrama-waimai-example", "mystery-game"} <= {c.id for c in with_plan}
    for case in with_plan:
        for item in case.foreshadowing_plan:
            assert item.get("content") and item.get("planned_resolution")
            assert item.get("keyword")


def test_foreshadowing_plan_for_matches_genre():
    plan = foreshadowing_plan_for("外卖员逆袭 复仇打脸 都市 短剧")
    assert plan and any(p["id"] == "W1" for p in plan)
    assert all(p.get("source_case") for p in plan)
    assert foreshadowing_plan_for("完全无关的主题") == []


def test_corpus_payload_for_ids():
    payload = corpus_payload_for("", ids=["mystery-game"])
    assert len(payload) == 1
    assert payload[0]["id"] == "mystery-game" and payload[0]["summary"]


def test_reconcile_foreshadowing():
    plan = [{"keyword": "云端", "content": "云端视频"}, {"keyword": "调监控", "content": "x"}]
    state = [{"keyword": "云端", "content": "云端视频"}, {"id": "Z", "content": "作者自加"}]
    report = reconcile_foreshadowing(plan, state)
    assert report["matched"] == ["云端"]
    assert report["missing"] == ["调监控"]
    assert report["unplanned"] == ["Z"]
    assert report["coverage"] == 0.5

    assert reconcile_foreshadowing([], [])["coverage"] is None


# ---------------------------------------------------------------------------
# planner 产出 seed / refs
# ---------------------------------------------------------------------------


async def test_beat_planner_emits_novel_seed_and_refs():
    planner = make_beat_sheet_planner()

    class T:
        title = "外卖员逆袭"
        description = "复仇打脸，都市短剧"

    novel_plan = await planner(CreationStage.NOVEL, {"topic": T()})
    assert novel_plan.get("foreshadowing_seed")
    assert novel_plan.get("corpus_refs")

    script_plan = await planner(CreationStage.SCRIPT, {"topic": T()})
    assert script_plan["target_scenes"] >= 3
    assert script_plan.get("corpus_refs")


# ---------------------------------------------------------------------------
# 语料注入 drafter prompt
# ---------------------------------------------------------------------------


async def test_drafter_payload_includes_corpus_refs():
    llm = FakeLlmClient(data={"title": "t", "body": "第一场　内景／日\n动作。"})
    drafter = make_script_drafter(llm)
    ctx = {
        "topic": None,
        "corpus_refs": ["mystery-game"],
    }
    await drafter(CreationStage.SCRIPT, ctx)

    import json

    payload = json.loads(llm.messages[1].content)
    assert "corpus_refs" in payload
    assert payload["corpus_refs"][0]["id"] == "mystery-game"
    assert payload["corpus_refs"][0]["tags"]


# ---------------------------------------------------------------------------
# seed 落库（显式开启）与对账
# ---------------------------------------------------------------------------


async def test_seed_foreshadowing_requires_flag(client):
    topic_id = (
        await client.post(
            "/api/topics",
            json={"title": "外卖员逆袭", "description": "复仇打脸 都市 短剧"},
        )
    ).json()["id"]

    # 关闭（默认）：不 seed
    gen, session = await _session_from_app()
    try:
        run_off = await pipeline_module.run_creation(
            session, uuid.UUID(topic_id), stages=(CreationStage.NOVEL,)
        )
    finally:
        await gen.aclose()
    state_off = await client.get(
        f"/api/novels/{run_off.artifacts['novel_id']}/story-state"
    )
    assert state_off.json()["foreshadowing"] == []

    # 开启：seed 进 StoryState
    gen, session = await _session_from_app()
    try:
        run_on = await pipeline_module.run_creation(
            session,
            uuid.UUID(topic_id),
            stages=(CreationStage.NOVEL,),
            options={"seed_foreshadowing": True},
        )
    finally:
        await gen.aclose()
    state_on = await client.get(
        f"/api/novels/{run_on.artifacts['novel_id']}/story-state"
    )
    seeded = state_on.json()["foreshadowing"]
    assert seeded and any(item.get("keyword") == "云端" for item in seeded)
    assert all(item.get("source_case") for item in seeded)


async def test_writing_desk_reports_corpus_reconciliation(client):
    topic_id = (
        await client.post(
            "/api/topics",
            json={"title": "外卖员逆袭", "description": "复仇打脸 都市 短剧"},
        )
    ).json()["id"]
    run = (
        await client.post("/api/creation/runs", json={"topic_id": topic_id})
    ).json()

    desk = (
        await client.get(f"/api/novels/{run['artifacts']['novel_id']}/writing-desk")
    ).json()
    recon = desk["corpus_foreshadowing"]
    assert recon is not None
    assert "missing" in recon and "coverage" in recon
    # 未 seed 时计划项应全部 missing，并出现在 next_actions
    assert recon["missing"]
    assert any("语料伏笔" in a for a in desk["next_actions"])
