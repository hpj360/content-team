"""故事状态（连续性权威）与 schema 校验测试。"""
from __future__ import annotations

from hermes.content_team.creative.gates import gate_story_state


VALID_TRACKING = {
    "position": "第1章",
    "recent_summary": "近五章摘要",
    "active_characters": "主角",
    "pending_foreshadowing": "无",
    "volume_goal": "完成首卷冲突闭环",
    "global_rules": "世界观与合规红线",
    "next_step": "推进第二章",
}


def _valid_state() -> dict:
    return {
        "tracking": dict(VALID_TRACKING),
        "characters": [
            {
                "name": "主角",
                "ability": "初始",
                "psychology": "目标驱动",
                "relations": "与对手对立",
                "goals": "完成主线",
            }
        ],
        "foreshadowing": [],
        "goals": {"global": "一致性", "volume": "首卷", "chapter": "钩子"},
    }


def test_state_gate_valid():
    report = gate_story_state(_valid_state())
    assert report.passed, report.error_messages()


def test_state_gate_missing_tracking_fields():
    data = _valid_state()
    del data["tracking"]["position"]
    del data["tracking"]["next_step"]
    report = gate_story_state(data)
    assert not report.passed
    assert "T001" in [i.code for i in report.errors]


def test_state_gate_no_characters():
    data = _valid_state()
    data["characters"] = []
    report = gate_story_state(data)
    assert "T002" in [i.code for i in report.errors]


def test_state_gate_character_missing_name():
    data = _valid_state()
    data["characters"][0]["name"] = ""
    report = gate_story_state(data)
    assert "T003" in [i.code for i in report.errors]


def test_state_gate_foreshadowing_missing_field():
    data = _valid_state()
    data["foreshadowing"] = [
        {
            "id": "F1",
            "content": "神秘信件",
            "planted_at": "第1章",
            "status": "planted",
        }
    ]
    report = gate_story_state(data)
    assert "T005" in [i.code for i in report.errors]


def test_state_gate_foreshadowing_status_warns():
    data = _valid_state()
    data["foreshadowing"] = [
        {
            "id": "F1",
            "content": "神秘信件",
            "planted_at": "第1章",
            "planned_resolution": "第3章",
            "status": "in_progress",
        }
    ]
    report = gate_story_state(data)
    assert report.passed  # 非初始状态仅警告
    assert "T006" in [i.code for i in report.warnings]


def test_state_gate_missing_goal_levels():
    data = _valid_state()
    data["goals"] = {"global": "g"}
    report = gate_story_state(data)
    assert "T007" in [i.code for i in report.errors]


# ---------------------------------------------------------------------------
# 端到端：管线生成状态；审查包含状态门；API 可查询
# ---------------------------------------------------------------------------


async def test_run_includes_story_state_artifact(client):
    """run_creation 会创建 StoryState 并纳入审查产物。"""
    topic_id = (
        await client.post(
            "/api/topics", json={"title": "状态题", "description": "科考队失踪"}
        )
    ).json()["id"]

    run_resp = await client.post("/api/creation/runs", json={"topic_id": topic_id})
    assert run_resp.status_code == 201
    run = run_resp.json()
    assert "story_state_id" in run["artifacts"]
    assert run["status"] == "SUCCEEDED"
    assert run["revision_outcome"] == "NONE"
    assert run["revise_rounds"] == 0

    state_resp = await client.get(
        f"/api/novels/{run['artifacts']['novel_id']}/story-state"
    )
    assert state_resp.status_code == 200
    state = state_resp.json()
    assert set(state["tracking"]) >= {
        "position",
        "volume_goal",
        "global_rules",
        "next_step",
    }
    assert state["characters"]
    assert set(state["goals"]) >= {"global", "volume", "chapter"}


async def test_story_state_404s(client):
    resp = await client.get(
        "/api/novels/00000000-0000-0000-0000-000000000000/story-state"
    )
    assert resp.status_code == 404
