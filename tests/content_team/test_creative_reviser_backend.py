"""Round 4：修订后端注入点（rules / LLM）行为契约测试。"""
from __future__ import annotations

import uuid

import hermes.content_team.creative.pipeline as pipeline_module
from hermes.content_team.creative.reviewer import ReviewReport
from hermes.content_team.creative.revision import (
    CreativeReviser,
    LlmReviserBackend,
)

S004_ISSUE = {
    "code": "S004",
    "message": "场景数 1 少于 3",
    "severity": "error",
    "dimension": "structure",
}


async def _session_from_app():
    from hermes.content_team.app import app
    from hermes.content_team.db import get_db

    gen = app.dependency_overrides[get_db]()
    return gen, await gen.__anext__()


def test_protocol_conformance():
    """规则后端与 LLM 后端都满足 RevisionBackend 形状（鸭子契约）。"""
    assert hasattr(CreativeReviser.__new__(CreativeReviser), "revise")
    assert hasattr(LlmReviserBackend(lambda a, i: None), "revise")


async def test_llm_backend_success_path():
    """LLM 正常返回日志 → 原样透传。"""
    calls = {"n": 0}

    async def revise_fn(artifacts, issues):
        calls["n"] += 1
        return [{"code": i["code"], "fixed": True, "action": "llm"} for i in issues]

    backend = LlmReviserBackend(revise_fn)
    log = await backend.revise({"script_id": "x"}, [dict(S004_ISSUE)])
    assert calls["n"] == 1
    assert log == [{"code": "S004", "fixed": True, "action": "llm"}]


async def test_llm_backend_exception_falls_back_to_rules(client):
    """LLM 异常 → 降级 fallback（规则后端）并真实修复场景数问题。"""
    from hermes.content_team.creative.revision import CreativeReviser

    topic_id = (
        await client.post(
            "/api/topics", json={"title": "LLM", "description": "注入点"}
        )
    ).json()["id"]
    run = (
        await client.post(
            "/api/creation/runs", json={"topic_id": topic_id, "review": False}
        )
    ).json()

    gen, session = await _session_from_app()
    try:
        async def broken_revise(artifacts, issues):
            raise RuntimeError("LLM unavailable")

        backend = LlmReviserBackend(broken_revise, fallback=CreativeReviser(session))
        log = await backend.revise(run["artifacts"], [dict(S004_ISSUE)])
    finally:
        await gen.aclose()

    assert log and log[0]["code"] == "S004"
    assert log[0]["fixed"] is True
    assert log[0]["action"] == "补全场景"


async def test_llm_backend_no_fallback_returns_empty(client):
    """LLM 异常且无 fallback → 空日志（交回人工 / 触发 UNCHANGED）。"""
    async def broken_revise(artifacts, issues):
        raise RuntimeError("boom")

    backend = LlmReviserBackend(broken_revise)
    log = await backend.revise({}, [dict(S004_ISSUE)])
    assert log == []


async def test_run_creation_with_injected_backend(client, monkeypatch):
    """端到端：注入 LLM 后端后，审查失败 → LLM 修订 → 重审 → SUCCEEDED/FIXED。"""
    topic_id = (
        await client.post(
            "/api/topics", json={"title": "注入题", "description": "描述"}
        )
    ).json()["id"]

    calls = {"n": 0}
    original = pipeline_module.review_creation

    async def fake_review(db, artifacts):
        if calls["n"] == 0:
            calls["n"] += 1
            return ReviewReport(
                score=55.0,
                passed=False,
                stage_issues={"SCRIPT": [dict(S004_ISSUE)]},
                error_count=1,
                warning_count=0,
                dimensions={"structure": 55.0},
            )
        return await original(db, artifacts)

    async def llm_revise(artifacts, issues):
        # LLM 只“声称”修复 —— 实际场景由提示词/外部系统写库；此处验证注入路径
        return [{"code": i["code"], "fixed": True, "action": "llm"} for i in issues]

    monkeypatch.setattr(pipeline_module, "review_creation", fake_review)

    gen, session = await _session_from_app()
    try:
        backend = LlmReviserBackend(llm_revise)
        run = await pipeline_module.run_creation(
            session, uuid.UUID(topic_id), reviser=backend
        )
    finally:
        await gen.aclose()

    assert run.status.value == "SUCCEEDED"
    assert run.revision_outcome.value == "FIXED"
    assert run.revise_rounds == 1
    assert any(entry["action"] == "llm" for entry in run.revise_log)
