"""R23：语料注入开关 + judge 跨 provider（离线）测试。"""
from __future__ import annotations

import uuid

import hermes.content_team.creative.pipeline as pipeline_module
from hermes.content_team.creative.builders_llm import make_script_drafter
from hermes.content_team.creative.judges import (
    build_judge,
    make_cross_provider_judge,
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
# 语料注入开关
# ---------------------------------------------------------------------------


async def test_planner_include_corpus_false():
    planner = make_beat_sheet_planner(include_corpus=False)

    class T:
        title = "外卖员逆袭"
        description = "复仇打脸 都市 短剧"

    novel_plan = await planner(CreationStage.NOVEL, {"topic": T()})
    script_plan = await planner(CreationStage.SCRIPT, {"topic": T()})
    assert "corpus_refs" not in novel_plan
    assert "foreshadowing_seed" not in novel_plan
    assert "corpus_refs" not in script_plan
    # 结构参数仍在
    assert script_plan["target_scenes"] >= 3


async def test_corpus_injection_flag_controls_drafter_payload(client):
    """默认角色组下 corpus_injection 控制是否注入语料（对照实验开关）。"""
    topic_id = (
        await client.post(
            "/api/topics", json={"title": "外卖员逆袭", "description": "复仇打脸 都市 短剧"}
        )
    ).json()["id"]

    llm_on = FakeLlmClient(data={"title": "t", "body": "第一场　内景／日\n动作。"})
    llm_off = FakeLlmClient(data={"title": "t", "body": "第一场　内景／日\n动作。"})

    gen, session = await _session_from_app()
    try:
        await pipeline_module.run_creation(
            session,
            uuid.UUID(topic_id),
            stages=(CreationStage.SCRIPT,),
            roles=pipeline_module.StageRoles(
                planner=make_beat_sheet_planner(include_corpus=True),
                drafter=make_script_drafter(llm_on),
            ),
        )
    finally:
        await gen.aclose()

    gen, session = await _session_from_app()
    try:
        await pipeline_module.run_creation(
            session,
            uuid.UUID(topic_id),
            stages=(CreationStage.SCRIPT,),
            roles=pipeline_module.StageRoles(
                planner=make_beat_sheet_planner(include_corpus=False),
                drafter=make_script_drafter(llm_off),
            ),
        )
    finally:
        await gen.aclose()

    import json

    on_payload = json.loads(llm_on.messages[1].content)
    off_payload = json.loads(llm_off.messages[1].content)
    assert "corpus_refs" in on_payload
    assert "corpus_refs" not in off_payload


# ---------------------------------------------------------------------------
# judge 跨 provider
# ---------------------------------------------------------------------------


def test_cross_provider_judge_unset_returns_none(monkeypatch):
    monkeypatch.delenv("CONTENT_TEAM_JUDGE_PROVIDER", raising=False)
    assert make_cross_provider_judge() is None


def test_cross_provider_judge_uses_provider(monkeypatch):
    captured: dict = {}

    def fake_make_client(provider=None, model=None, settings=None):
        captured.update(provider=provider, model=model)
        return FakeLlmClient(data={"notes": ["x"], "score": 80})

    monkeypatch.setattr("hermes.workbench.llm.make_llm_client", fake_make_client)
    judge = make_cross_provider_judge("moonshot", "kimi-k2")
    assert judge is not None
    assert captured == {"provider": "moonshot", "model": "kimi-k2"}


def test_cross_provider_judge_reads_env(monkeypatch):
    monkeypatch.setenv("CONTENT_TEAM_JUDGE_PROVIDER", "openai")
    monkeypatch.setenv("CONTENT_TEAM_JUDGE_MODEL", "gpt-4o")
    captured: dict = {}

    def fake_make_client(provider=None, model=None, settings=None):
        captured.update(provider=provider, model=model)
        return FakeLlmClient(data={"notes": []})

    monkeypatch.setattr("hermes.workbench.llm.make_llm_client", fake_make_client)
    assert make_cross_provider_judge() is not None
    assert captured == {"provider": "openai", "model": "gpt-4o"}


def test_build_judge_falls_back_when_unset(monkeypatch):
    monkeypatch.delenv("CONTENT_TEAM_JUDGE_PROVIDER", raising=False)
    monkeypatch.setattr(
        "hermes.workbench.llm.make_llm_client",
        lambda **kw: FakeLlmClient(data={"notes": []}),
    )
    judge = build_judge()
    assert judge is not None  # 回退同源 client


async def test_judge_callable_contract_after_provider_wrap(monkeypatch):
    monkeypatch.setattr(
        "hermes.workbench.llm.make_llm_client",
        lambda **kw: FakeLlmClient(data={"notes": ["章尾钩子弱"], "score": 70}),
    )
    judge = make_cross_provider_judge("moonshot", "kimi-k2")
    notes = await judge(CreationStage.SCRIPT, {"preview": "第一场 内景/日\n动作。"}, {})
    assert "章尾钩子弱" in notes
    assert any(n.startswith("[judge] score=70") for n in notes)
