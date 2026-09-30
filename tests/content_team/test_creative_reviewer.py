"""独立审查器集成测试：审查与创作隔离、评分与裁定、留痕。"""
from __future__ import annotations

from hermes.content_team.creative.gates import REVIEW_PASS_SCORE
from hermes.content_team.creative.reviewer import review_creation


async def _create_topic(client, title="审查题", description="用于审查测试的选题") -> str:
    resp = await client.post(
        "/api/topics", json={"title": title, "description": description}
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _session_from_app():
    """借助依赖覆盖取得一个测试会话（与请求共用同一内存库）。"""
    from hermes.content_team.app import app
    from hermes.content_team.db import get_db

    gen = app.dependency_overrides[get_db]()
    return gen, await gen.__anext__()


async def test_default_run_passes_review(client):
    """默认管线产出应通过独立审查，且带评分与维度。"""
    topic_id = await _create_topic(client)
    resp = await client.post("/api/creation/runs", json={"topic_id": topic_id})
    assert resp.status_code == 201
    run = resp.json()

    assert run["status"] == "SUCCEEDED"
    assert run["review"] is not None
    assert run["review_score"] >= REVIEW_PASS_SCORE
    assert run["review"]["passed"] is True
    assert set(run["review"]["dimensions"]) == {
        "structure",
        "compliance",
        "consistency",
        "pacing",
        "craft",
    }


async def test_review_can_be_disabled(client):
    """review=False 时不执行审查 pass。"""
    topic_id = await _create_topic(client)
    run = (
        await client.post(
            "/api/creation/runs", json={"topic_id": topic_id, "review": False}
        )
    ).json()
    assert run["status"] == "SUCCEEDED"
    assert run["review"] is None
    assert run["review_score"] is None


async def test_review_detects_tampered_artifact(client):
    """审查器独立读取 DB：被篡改的产物会被判负，与 builder 无关。"""
    topic_id = await _create_topic(client)
    run = (
        await client.post("/api/creation/runs", json={"topic_id": topic_id})
    ).json()
    script_id = run["artifacts"]["script_id"]

    # 篡改剧本：仅剩 1 场，违反场景数硬门
    resp = await client.put(
        f"/api/scripts/{script_id}",
        json={"body": "第一场 内景/日\n只有一个场景。"},
    )
    assert resp.status_code == 200

    gen, session = await _session_from_app()
    try:
        report = await review_creation(session, run["artifacts"])
    finally:
        await gen.aclose()

    assert report.passed is False
    assert report.error_count >= 1
    assert report.dimensions["structure"] < 100.0
    assert "S004" in {i["code"] for i in report.stage_issues.get("SCRIPT", [])}


async def test_review_reports_dimension_penalties(client):
    """存在合规阻断词时合规维度扣分。"""
    topic_id = await _create_topic(client)
    run = (
        await client.post("/api/creation/runs", json={"topic_id": topic_id})
    ).json()
    script_id = run["artifacts"]["script_id"]

    await client.put(
        f"/api/scripts/{script_id}",
        json={
            "body": "第一场 内景/日\n代开发票。\n第二场 外景/夜\n动作。\n"
            "第三场 内景/日\n动作。"
        },
    )

    gen, session = await _session_from_app()
    try:
        report = await review_creation(session, run["artifacts"])
    finally:
        await gen.aclose()

    assert report.dimensions["compliance"] < 100.0
    assert report.error_count >= 1
