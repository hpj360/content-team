"""Round 10（创作者视角）：B2 写作台 + B1 创作→发布桥。"""
from __future__ import annotations

from hermes.content_team.creative.bridge import assemble_content_body


async def _session_from_app():
    from hermes.content_team.app import app
    from hermes.content_team.db import get_db

    gen = app.dependency_overrides[get_db]()
    return gen, await gen.__anext__()


async def _make_run(client, title="交付题", description="深海科考队失踪"):
    topic = (
        await client.post(
            "/api/topics", json={"title": title, "description": description}
        )
    ).json()["id"]
    return (
        await client.post("/api/creation/runs", json={"topic_id": topic})
    ).json()


# ---------------------------------------------------------------------------
# B2 写作台
# ---------------------------------------------------------------------------


async def test_writing_desk_view(client):
    run = await _make_run(client)
    resp = await client.get(
        f"/api/novels/{run['artifacts']['novel_id']}/writing-desk"
    )
    assert resp.status_code == 200
    desk = resp.json()

    assert desk["novel"]["title"].endswith("（小说）")
    assert desk["progress"]["chapters"] == 1
    assert desk["progress"]["next_chapter"] == 2
    assert desk["progress"]["total_words"] > 0
    assert desk["context_card"]  # 状态卡上下文
    assert isinstance(desk["pending_foreshadowing"], list)
    assert isinstance(desk["continuity_warnings"], list)
    assert "写第2章" in desk["next_actions"]


async def test_writing_desk_lists_pending_foreshadowing(client):
    """埋下未回收伏笔 → 写作台待办出现。"""
    from hermes.content_team.models.creative import StoryState
    import uuid as uuid_mod

    run = await _make_run(client, title="伏笔台", description="信件线索")
    novel_id = run["artifacts"]["novel_id"]
    state_id = run["artifacts"]["story_state_id"]

    gen, session = await _session_from_app()
    try:
        state = await session.get(StoryState, uuid_mod.UUID(state_id))
        state.foreshadowing = [
            {
                "id": "F1",
                "content": "神秘信件",
                "planted_at": "第1章",
                "planned_resolution": "第3章",
                "status": "planted",
                "keyword": "信件",
            }
        ]
        state.tracking["pending_foreshadowing"] = "F1 神秘信件"
        await session.commit()
    finally:
        await gen.aclose()

    desk = (
        await client.get(f"/api/novels/{novel_id}/writing-desk")
    ).json()
    assert len(desk["pending_foreshadowing"]) == 1
    assert desk["pending_foreshadowing"][0]["id"] == "F1"
    assert any("伏笔" in a for a in desk["next_actions"])


async def test_writing_desk_404(client):
    resp = await client.get(
        "/api/novels/00000000-0000-0000-0000-000000000000/writing-desk"
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# B1 创作→发布桥
# ---------------------------------------------------------------------------


def test_assemble_content_body_includes_parts():
    class _Script:
        body = "第一场　内景／日\n动作。"

    body = assemble_content_body(
        _Script(),  # type: ignore[arg-type]
        [
            {
                "shot_number": 1,
                "shot_size": "WIDE",
                "camera_movement": "DOLLY",
                "description": "建置",
            }
        ],
        "克制表演",
    )
    assert "第一场" in body
    assert "【分镜】" in body and "镜1｜WIDE｜DOLLY｜建置" in body
    assert "【导演阐述】" in body and "克制表演" in body


async def _account(client, platform="WECHAT_OFFICIAL", name="公众号"):
    return (
        await client.post(
            "/api/accounts",
            json={"platform": platform, "display_name": name},
        )
    ).json()["id"]


async def test_publish_run_bridges_to_content_and_tasks(client):
    run = await _make_run(client, title="发布题")
    account_id = await _account(client)

    resp = await client.post(
        f"/api/creation/runs/{run['id']}/publish",
        json={"platform_account_ids": [account_id]},
    )
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 1
    assert tasks[0]["status"] == "SUCCESS"

    # 内容已创建且剧本已回填 content_id
    content = await client.get(f"/api/content/{tasks[0]['content_id']}")
    assert content.status_code == 200
    body = content.json()["body"]
    assert "第一场" in body and "【分镜】" in body and "【导演阐述】" in body

    script = await client.get(f"/api/scripts/{run['artifacts']['script_id']}")
    assert script.json()["content_id"] == tasks[0]["content_id"]


async def test_publish_run_missing_run_404(client):
    account_id = await _account(client)
    resp = await client.post(
        "/api/creation/runs/00000000-0000-0000-0000-000000000000/publish",
        json={"platform_account_ids": [account_id]},
    )
    assert resp.status_code == 404
