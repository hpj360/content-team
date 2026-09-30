"""自动修订闭环测试：审查失败 → 修订 → 重审 → 收敛/记账。"""
from __future__ import annotations

import pytest

import hermes.content_team.creative.pipeline as pipeline_module
from hermes.content_team.creative.gates import REVIEW_PASS_SCORE
from hermes.content_team.creative.reviewer import ReviewReport
from hermes.content_team.creative.revision import CreativeReviser

S004_ISSUE = {
    "code": "S004",
    "message": "场景数 1 少于 3",
    "severity": "error",
    "dimension": "structure",
}


def _failed_report(score: float = 55.0) -> ReviewReport:
    return ReviewReport(
        score=score,
        passed=False,
        stage_issues={"SCRIPT": [dict(S004_ISSUE)]},
        error_count=1,
        warning_count=0,
        dimensions={"structure": 55.0},
    )


async def _create_topic(client) -> str:
    resp = await client.post(
        "/api/topics", json={"title": "修订题", "description": "用于自动修订"}
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _session_from_app():
    from hermes.content_team.app import app
    from hermes.content_team.db import get_db

    gen = app.dependency_overrides[get_db]()
    return gen, await gen.__anext__()


async def test_reviser_fixes_few_scenes(client):
    """reviser 按编码直接修复：场景数 <3 时补齐到 3 场。"""
    topic_id = await _create_topic(client)
    run = (
        await client.post(
            "/api/creation/runs", json={"topic_id": topic_id, "review": False}
        )
    ).json()
    script_id = run["artifacts"]["script_id"]

    await client.put(
        f"/api/scripts/{script_id}",
        json={"body": "第一场 内景/日\n只有一个场景。"},
    )

    gen, session = await _session_from_app()
    try:
        reviser = CreativeReviser(session)
        log = await reviser.revise(run["artifacts"], [dict(S004_ISSUE)])
        assert log and log[0]["code"] == "S004" and log[0]["fixed"] is True
    finally:
        await gen.aclose()

    script = (await client.get(f"/api/scripts/{script_id}")).json()
    assert script["body"].count("场") >= 3


async def test_auto_revise_fixes_and_passes(client, monkeypatch):
    """审查失败 → 自动修订 → 重审通过：状态 SUCCEEDED + FIXED + 轮次 1。"""
    topic_id = await _create_topic(client)
    calls = {"n": 0}
    original = pipeline_module.review_creation

    async def fake_review(db, artifacts):
        if calls["n"] == 0:
            calls["n"] += 1
            return _failed_report()
        return await original(db, artifacts)

    monkeypatch.setattr(pipeline_module, "review_creation", fake_review)

    run = (
        await client.post("/api/creation/runs", json={"topic_id": topic_id})
    ).json()

    assert run["status"] == "SUCCEEDED"
    assert run["revision_outcome"] == "FIXED"
    assert run["revise_rounds"] == 1
    assert run["review_score"] >= REVIEW_PASS_SCORE
    assert any(e["code"] == "S004" for e in run["revise_log"])


async def test_auto_revise_exhausts(client, monkeypatch):
    """问题不可收敛时：修订轮次耗尽 → NEEDS_REVISION + EXHAUSTED。"""
    topic_id = await _create_topic(client)
    scores = iter([40.0, 52.0, 68.0])

    async def drift_fail(db, artifacts):
        try:
            score = next(scores)
        except StopIteration:
            score = 68.0
        return ReviewReport(
            score=score,
            passed=False,
            stage_issues={"UNKNOWN": [dict(S004_ISSUE)]},
            error_count=1,
            warning_count=0,
            dimensions={},
        )

    monkeypatch.setattr(pipeline_module, "review_creation", drift_fail)

    run = (
        await client.post(
            "/api/creation/runs",
            json={"topic_id": topic_id, "max_revise_rounds": 1},
        )
    ).json()
    assert run["status"] == "NEEDS_REVISION"
    assert run["revision_outcome"] == "EXHAUSTED"
    assert run["revise_rounds"] == 1


async def test_auto_revise_off_marks_needs_revision(client):
    """auto_revise=False 时审查失败直接交回人工。"""
    topic_id = await _create_topic(client)
    calls = {"n": 0}
    original = pipeline_module.review_creation

    async def fake_review(db, artifacts):
        if calls["n"] == 0:
            calls["n"] += 1
            return _failed_report()
        return await original(db, artifacts)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(pipeline_module, "review_creation", fake_review)
    try:
        run = (
            await client.post(
                "/api/creation/runs",
                json={"topic_id": topic_id, "auto_revise": False},
            )
        ).json()
    finally:
        monkeypatch.undo()

    assert run["status"] == "NEEDS_REVISION"
    assert run["revision_outcome"] == "NONE"
    assert run["revise_rounds"] == 0
