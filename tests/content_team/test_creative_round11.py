"""Round 11（创作者视角 · C5 收官 + A3）：工作台与 LLM 评委。"""
from __future__ import annotations

import hermes.content_team.creative.pipeline as pipeline_module
from hermes.content_team.creative.judges import (
    RUBRICS,
    judge_report,
    make_llm_judge,
)
from hermes.content_team.creative.pipeline import StageRoles
from hermes.content_team.models.creative import CreationStage

from tests.content_team._fakes import FakeLlmClient as _FakeJudgeClient


async def _session_from_app():
    from hermes.content_team.app import app
    from hermes.content_team.db import get_db

    gen = app.dependency_overrides[get_db]()
    return gen, await gen.__anext__()


async def _make_run(client, title="工作台题", description="深海科考队失踪"):
    topic = (
        await client.post(
            "/api/topics", json={"title": title, "description": description}
        )
    ).json()["id"]
    return (
        await client.post("/api/creation/runs", json={"topic_id": topic})
    ).json()


# ---------------------------------------------------------------------------
# C5：工作台
# ---------------------------------------------------------------------------


async def test_dashboard_page_served(client):
    resp = await client.get("/dashboard")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    html = resp.text
    assert "content-team 工作台" in html
    assert "/api/dashboard/overview" in html
    assert "写作台" in html and "发起创作" in html
    # 零构建：无外部资源引用
    assert "http://" not in html and "https://" not in html


async def test_dashboard_overview_shape(client):
    resp = await client.get("/api/dashboard/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert {"novels", "topics", "runs", "stats"} <= set(data)
    assert data["stats"]["total_runs"] == 0


async def test_dashboard_overview_after_run(client):
    run = await _make_run(client)
    overview = (await client.get("/api/dashboard/overview")).json()

    assert overview["stats"]["total_runs"] >= 1
    assert overview["stats"]["avg_review_score"] is not None
    run_ids = [r["id"] for r in overview["runs"]]
    assert run["id"] in run_ids

    novel = next(n for n in overview["novels"] if n["id"] == run["artifacts"]["novel_id"])
    assert novel["chapters"] == 1 and novel["words"] > 0

    topic_ids = [t["id"] for t in overview["topics"]]
    assert run["topic_id"] in topic_ids

    latest = overview["runs"][0]
    assert latest["novel_id"] and latest["script_id"]


# ---------------------------------------------------------------------------
# A3：LLM 评委（不门禁）
# ---------------------------------------------------------------------------


async def test_judge_returns_notes_with_score_line():
    client = _FakeJudgeClient(
        data={"notes": ["章尾钩子偏弱", "台词有解释性"], "score": 72, "verdict": "REVISE"}
    )
    judge = make_llm_judge(client)
    notes = await judge(CreationStage.SCRIPT, {"script_title": "x"}, {})
    assert "章尾钩子偏弱" in notes
    assert any(n.startswith("[judge] score=72") for n in notes)
    # rubric 确实进入 prompt
    assert "每场是否发生价值转折" in client.messages[1].content


async def test_judge_failure_returns_empty():
    judge = make_llm_judge(_FakeJudgeClient(error=RuntimeError("llm down")))
    assert await judge(CreationStage.NOVEL, {}, {}) == []


async def test_judge_no_rubric_stage_returns_empty():
    judge = make_llm_judge(_FakeJudgeClient(data={"notes": ["x"]}), rubrics={})
    assert await judge(CreationStage.NOVEL, {}, {}) == []


def test_judge_report_shape():
    report = judge_report(["a", "b"])
    assert report["count"] == 2 and report["judge_notes"] == ["a", "b"]


def test_rubrics_cover_core_stages():
    assert set(RUBRICS) == {
        CreationStage.NOVEL,
        CreationStage.SCRIPT,
        CreationStage.STORYBOARD,
        CreationStage.DIRECTING,
    }


async def test_judge_injected_as_critic_records_notes(client):
    """judge 作为 critic 注入：建议入账但不影响门禁（仍 SUCCEEDED）。"""
    topic = (
        await client.post(
            "/api/topics", json={"title": "评议题", "description": "描述"}
        )
    ).json()["id"]

    judge = make_llm_judge(_FakeJudgeClient(data={"notes": ["建议加强钩子"], "score": 80}))

    gen, session = await _session_from_app()
    try:
        run = await pipeline_module.run_creation(
            session, __import__("uuid").UUID(topic), roles=StageRoles(critic=judge)
        )
    finally:
        await gen.aclose()

    assert run.status.value == "SUCCEEDED"  # 门禁不受影响
    assert run.stage_results[0]["critic_notes"] == ["建议加强钩子", "[judge] score=80 verdict=None"]
