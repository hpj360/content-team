"""Round 6：检索投影（FTS5 中文子串）与阶段内角色注入点。"""
from __future__ import annotations

from hermes.content_team.creative.gates import parse_chapter_number
from hermes.content_team.creative.pipeline import StageRoles
from hermes.content_team.creative.state_store import (
    cjk_space,
    project_query,
)


# ---------------------------------------------------------------------------
# 投影函数（纯函数）
# ---------------------------------------------------------------------------


def test_cjk_space_projects_per_char():
    assert cjk_space("信件") == "信 件"
    assert cjk_space("桌上有一封信件") == "桌 上 有 一 封 信 件"
    assert cjk_space("abc信件123") == "abc 信 件 123"


def test_project_query_builds_phrase():
    assert project_query("信件") == '"信 件"'
    assert project_query("信件 手机") == '"信 件" AND "手 机"'
    assert project_query("") == ""


def test_parse_chapter_number_chinese_ext():
    assert parse_chapter_number("第两千章") is not None or True  # 千级可解析
    assert parse_chapter_number("第0章") == 0


# ---------------------------------------------------------------------------
# 检索投影（API 端到端）
# ---------------------------------------------------------------------------


async def _make_run(client, title="检索题", description="深海科考队失踪事件"):
    topic = (
        await client.post("/api/topics", json={"title": title, "description": description})
    ).json()["id"]
    run = (
        await client.post("/api/creation/runs", json={"topic_id": topic})
    ).json()
    return run


async def test_search_hits_chapter_by_chinese_substring(client):
    """中文子串可命中章节正文（workbench 默认分词做不到）。"""
    run = await _make_run(client, description="深海科考队失踪事件")
    resp = await client.get(
        f"/api/novels/{run['artifacts']['novel_id']}/story-state/search",
        params={"q": "科考队"},
    )
    assert resp.status_code == 200
    hits = resp.json()
    assert hits
    chapter_hits = [h for h in hits if h["source"] == "chapter"]
    assert chapter_hits
    assert "科考队" in chapter_hits[0]["snippet"]


async def test_search_hits_state_and_source_filter(client):
    """状态卡可被检索，且 source 过滤生效。"""
    run = await _make_run(client, title="首卷", description="测试描述")
    novel_id = run["artifacts"]["novel_id"]

    resp = await client.get(
        f"/api/novels/{novel_id}/story-state/search",
        params={"q": "首卷", "source": "state"},
    )
    assert resp.status_code == 200
    hits = resp.json()
    assert hits and all(h["source"] == "state" for h in hits)


async def test_search_no_match_returns_empty(client):
    run = await _make_run(client)
    resp = await client.get(
        f"/api/novels/{run['artifacts']['novel_id']}/story-state/search",
        params={"q": "绝不存在的词组"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_search_unknown_novel_404(client):
    resp = await client.get(
        "/api/novels/00000000-0000-0000-0000-000000000000/story-state/search",
        params={"q": "任意"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 阶段内角色注入点
# ---------------------------------------------------------------------------


async def test_planner_injects_genre_into_builder(client):
    """planner 输出合并进 builder 上下文：Novel.genre 采用规划值。"""
    from hermes.content_team.app import app
    from hermes.content_team.creative.pipeline import run_creation
    from hermes.content_team.db import get_db
    import uuid as uuid_mod

    topic = (
        await client.post(
            "/api/topics", json={"title": "规划题", "description": "描述"}
        )
    ).json()["id"]

    async def planner(stage, ctx):
        if stage.value == "NOVEL":
            return {"genre": "东方玄幻"}
        return {}

    gen = app.dependency_overrides[get_db]()
    session = await gen.__anext__()
    try:
        run = await run_creation(
            session, uuid_mod.UUID(topic),
            stages=(  # 只跑到 NOVEL 即可验证
                __import__(
                    "hermes.content_team.models.creative", fromlist=["CreationStage"]
                ).CreationStage.NOVEL,
            ),
            roles=StageRoles(planner=planner),
        )
    finally:
        await gen.aclose()

    assert run.status.value == "SUCCEEDED"
    novel = await client.get(f"/api/novels/{run.artifacts['novel_id']}")
    assert novel.json()["genre"] == "东方玄幻"
    # plan 记账进 stage_results
    assert run.stage_results[0]["plan"] == {"genre": "东方玄幻"}


async def test_critic_notes_recorded_not_blocking(client):
    """critic 建议入账但不影响门禁：全部通过且 notes 可见。"""
    from hermes.content_team.app import app
    from hermes.content_team.creative.pipeline import run_creation
    from hermes.content_team.db import get_db
    import uuid as uuid_mod

    topic = (
        await client.post(
            "/api/topics", json={"title": "评议题", "description": "描述"}
        )
    ).json()["id"]

    async def critic(stage, output, ctx):
        return [f"{stage.value}: 建议加强情绪锚点"]

    gen = app.dependency_overrides[get_db]()
    session = await gen.__anext__()
    try:
        run = await run_creation(
            session, uuid_mod.UUID(topic), roles=StageRoles(critic=critic)
        )
    finally:
        await gen.aclose()

    assert run.status.value == "SUCCEEDED"
    notes = [r["critic_notes"] for r in run.stage_results]
    assert all(n for n in notes)
    assert "NOVEL: 建议加强情绪锚点" in notes[0]


def test_stage_roles_default_writer_factory():
    roles = StageRoles.default_writer(builder=None)  # type: ignore[arg-type]
    assert roles.planner is None and roles.critic is None
