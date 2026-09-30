"""审查质量统计 API 测试。"""
from __future__ import annotations


async def test_creation_stats_structure(client):
    """/api/creation/runs/stats 返回状态分布/平均分/维度均值/趋势。"""
    # 先制造运行（默认全绿）
    for idx in range(2):
        resp = await client.post(
            "/api/topics", json={"title": f"统计{idx}", "description": "统计"}
        )
        topic_id = resp.json()["id"]
        run = await client.post("/api/creation/runs", json={"topic_id": topic_id})
        assert run.status_code == 201

    stats = await client.get("/api/creation/runs/stats")
    assert stats.status_code == 200
    data = stats.json()

    assert data["total_runs"] >= 2
    assert data["by_status"].get("SUCCEEDED", 0) >= 2
    assert data["avg_review_score"] is not None
    assert 0 <= data["avg_review_score"] <= 100
    assert set(data["avg_dimensions"]) == {
        "structure",
        "compliance",
        "consistency",
        "pacing",
        "craft",
    }
    assert "NONE" in data["revision_outcomes"]
    assert len(data["trend"]) >= 2
    for item in data["trend"]:
        assert {"run_id", "status", "review_score", "revise_rounds", "created_at"} <= set(
            item
        )


async def test_stats_empty(client):
    """无数据时返回空结构。"""
    resp = await client.get("/api/creation/runs/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_runs"] == 0
    assert data["by_status"] == {}
    assert data["avg_review_score"] is None
    assert data["avg_dimensions"] == {}
    assert data["trend"] == []
