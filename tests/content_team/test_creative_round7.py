"""Round 7（创作者视角）：A1 一致性检索接线 + C1 记忆记账。"""
from __future__ import annotations

import hermes.content_team.creative.pipeline as pipeline_module
from hermes.content_team.creative.planners import (
    RETRIEVAL_KEY,
    derive_query,
    make_retrieval_planner,
    render_retrieval_block,
)
from hermes.content_team.memory import (
    get_recent_episodes,
    search_episodes,
)
from hermes.workbench.memory import MemoryService


async def _session_from_app():
    from hermes.content_team.app import app
    from hermes.content_team.db import get_db

    gen = app.dependency_overrides[get_db]()
    return gen, await gen.__anext__()


async def _topic(client, title="检索题", description="深海科考队失踪事件谜团"):
    return (
        await client.post(
            "/api/topics", json={"title": title, "description": description}
        )
    ).json()["id"]


# ---------------------------------------------------------------------------
# A1：检索接线
# ---------------------------------------------------------------------------


def test_render_retrieval_block():
    block = render_retrieval_block(
        [{"title": "第1章 开端", "snippet": "…科考队…"}]
    )
    assert "【一致性参考】" in block
    assert "第1章 开端" in block


def test_derive_query_uses_topic_description():
    class T:
        title = "题"
        description = "深海科考队失踪事件"

    assert derive_query(__import__(
        "hermes.content_team.models.creative", fromlist=["CreationStage"]
    ).CreationStage.SCRIPT, {"topic": T()}) == "深海科考队失踪事件"


async def test_retrieval_injected_into_script(client):
    """SCRIPT 阶段写前检索小说既有正文，注入一致性参考。"""
    topic_id = await _topic(client)
    gen, session = await _session_from_app()
    try:
        run = await pipeline_module.run_creation(session, __import__("uuid").UUID(topic_id))
    finally:
        await gen.aclose()

    assert run.status.value == "SUCCEEDED"
    script = await client.get(f"/api/scripts/{run.artifacts['script_id']}")
    body = script.json()["body"]
    assert "【一致性参考】" in body
    assert "科考队" in body  # 检索到的既有正文内容

    # 规划器记账：SCRIPT 阶段 plan 含 retrieval
    script_rounds = [r for r in run.stage_results if r["stage"] == "SCRIPT"]
    assert script_rounds and RETRIEVAL_KEY in script_rounds[0]["plan"]


async def test_retrieval_disabled(client):
    """retrieval=False 时不注入一致性参考。"""
    topic_id = await _topic(client)
    gen, session = await _session_from_app()
    try:
        run = await pipeline_module.run_creation(
            session, __import__("uuid").UUID(topic_id), retrieval=False
        )
    finally:
        await gen.aclose()
    script = await client.get(f"/api/scripts/{run.artifacts['script_id']}")
    assert "【一致性参考】" not in script.json()["body"]


async def test_retrieval_planner_noop_for_novel_stage():
    from hermes.content_team.models.creative import CreationStage

    planner = make_retrieval_planner(db=None)  # NOVEL 阶段不触库
    assert await planner(CreationStage.NOVEL, {}) == {}
    assert await planner(CreationStage.SCRIPT, {}) == {}


# ---------------------------------------------------------------------------
# C1：记忆记账
# ---------------------------------------------------------------------------


async def test_creation_memory_recorded(client, tmp_path):
    """提供 memory 时，运行与审查结论写入 L2 episodes。"""
    topic_id = await _topic(client, title="记账题", description="记账用描述")
    topic_uuid = __import__("uuid").UUID(topic_id)

    gen, session = await _session_from_app()
    try:
        memory = MemoryService(state_dir=tmp_path / "mem")
        run = await pipeline_module.run_creation(
            session, topic_uuid, memory=memory
        )
    finally:
        await gen.aclose()

    assert run.status.value == "SUCCEEDED"
    runs = get_recent_episodes(kind="creation_run", service=memory)
    reviews = get_recent_episodes(kind="creation_review", service=memory)
    assert len(runs) == 1 and runs[0].details["run_id"] == str(run.id)
    assert len(reviews) == 1 and reviews[0].details["passed"] is True

    hits = search_episodes("创作运行", service=memory)
    assert hits
