"""Round 8（创作者视角 · A2'）：文风指纹、去 AI 味出口门、LLM 陪写注入。"""
from __future__ import annotations

import hermes.content_team.creative.pipeline as pipeline_module
from hermes.content_team.creative.builders_llm import (
    make_llm_drafter,
    make_script_drafter,
)
from hermes.content_team.creative.deai import apply_de_ai_pass
from hermes.content_team.creative.pipeline import StageRoles
from hermes.content_team.creative.style_fingerprint import (
    compare_fingerprints,
    extract_fingerprint,
    fingerprint_to_prompt,
)
from hermes.content_team.models.creative import CreationStage

from tests.content_team._fakes import FakeLlmClient as _FakeClient


async def _session_from_app():
    from hermes.content_team.app import app
    from hermes.content_team.db import get_db

    gen = app.dependency_overrides[get_db]()
    return gen, await gen.__anext__()


async def _topic(client, title="陪写题", description="深海科考队失踪事件"):
    return (
        await client.post(
            "/api/topics", json={"title": title, "description": description}
        )
    ).json()["id"]


# ---------------------------------------------------------------------------
# 文风指纹
# ---------------------------------------------------------------------------

SAMPLE_A = (
    "雨点砸在铁皮屋顶。他数到三。门开了。\n\n"
    "「你迟到了。」她说。他把伞收起来，水顺着伞骨滴在门槛上。"
)
SAMPLE_B = (
    "雨点砸在铁皮屋顶。他数到三。门开了。\n\n"
    "「你迟到了。」她说。他把伞收好，水顺着伞骨滴下。"
)


def test_extract_fingerprint_basic():
    fp = extract_fingerprint([SAMPLE_A])
    assert fp.sample_chars > 0
    assert fp.sentence_len_avg > 0
    assert 0 <= fp.short_sentence_ratio <= 1
    assert fp.dialogue_ratio > 0
    assert fp.top_words


def test_extract_fingerprint_empty():
    fp = extract_fingerprint([])
    assert fp.sample_chars == 0
    assert fingerprint_to_prompt(fp) == ""


def test_fingerprint_prompt_contains_constraints():
    prompt = fingerprint_to_prompt(extract_fingerprint([SAMPLE_A]))
    assert "模仿以下作者声线" in prompt
    assert "禁止 AI 腔" in prompt


def test_compare_fingerprints_similar_vs_different():
    a = extract_fingerprint([SAMPLE_A])
    b = extract_fingerprint([SAMPLE_B])
    c = extract_fingerprint(["这是完全不同的另一种文风，句子很长，而且充满了各种各样的修饰与铺陈，读起来节奏拖沓。"])
    assert compare_fingerprints(a, b) > compare_fingerprints(a, c)
    assert 0 <= compare_fingerprints(a, c) <= 1


# ---------------------------------------------------------------------------
# 去 AI 味出口门
# ---------------------------------------------------------------------------


def test_de_ai_removes_cliche_and_psych():
    # 注意：心理旁白用「他心里」验证（「心中暗道」属 cliché 词表，会被先移除）
    text = "他不由得停下，他心里想：不妙。值得一提的是，天亮了。"
    clean, rules = apply_de_ai_pass(text)
    assert "不由得" not in clean
    assert "他心里" not in clean
    assert "值得一提的是" not in clean
    assert any(r.startswith("cliche:") for r in rules)
    assert "psych-narration" in rules


def test_de_ai_removes_parallel_and_notbut():
    text = "这不仅是一次失败，更是整支队伍的耻辱。这不是结束，而是开始。"
    clean, rules = apply_de_ai_pass(text)
    assert "不仅" not in clean and "而是" not in clean
    assert "parallel-triple" in rules or "not-but" in rules


def test_de_ai_noop_on_clean_text():
    clean, rules = apply_de_ai_pass("门开了。他站着没动。")
    assert rules == []


# ---------------------------------------------------------------------------
# LLM 陪写注入
# ---------------------------------------------------------------------------


DRAFT_BODY = (
    "第一场　内景／日\n\n他不由得停下，心中暗道不妙。\n\n"
    "第二场　内景／夜\n\n对手施压。\n\n"
    "第三场　外景／夜\n\n他做了选择。"
)


async def test_llm_draft_injected_and_de_ai_applied(client):
    """注入 LLM 草稿 → 剧本正文采用草稿并过强制去 AI 味出口门。"""
    topic_id = await _topic(client)
    client_llm = _FakeClient(data={"title": "AI 剧本", "body": DRAFT_BODY})
    drafter = make_script_drafter(client_llm)

    gen, session = await _session_from_app()
    try:
        run = await pipeline_module.run_creation(
            session,
            __import__("uuid").UUID(topic_id),
            roles=StageRoles(drafter=drafter),
        )
    finally:
        await gen.aclose()

    assert run.status.value == "SUCCEEDED"
    script = await client.get(f"/api/scripts/{run.artifacts['script_id']}")
    body = script.json()["body"]
    assert "不由得" not in body and "心中暗道" not in body
    assert "对手施压" in body  # 来自草稿
    assert run.artifacts.get("de_ai_rules")


async def test_llm_draft_failure_falls_back_to_template(client):
    """drafter 异常 → 降级模板（不影响交付）。"""
    topic_id = await _topic(client)
    drafter = make_script_drafter(_FakeClient(error=RuntimeError("LLM down")))

    gen, session = await _session_from_app()
    try:
        run = await pipeline_module.run_creation(
            session,
            __import__("uuid").UUID(topic_id),
            roles=StageRoles(drafter=drafter),
        )
    finally:
        await gen.aclose()

    assert run.status.value == "SUCCEEDED"
    script = await client.get(f"/api/scripts/{run.artifacts['script_id']}")
    assert "建置" in script.json()["body"]  # 模板标记


async def test_style_samples_fingerprint_recorded_and_prompted(client):
    """options.style_samples → 指纹注入 drafter prompt 并记录进 artifacts。"""
    topic_id = await _topic(client)
    llm = _FakeClient(data={"title": "t", "body": DRAFT_BODY})
    drafter = make_llm_drafter(llm)

    gen, session = await _session_from_app()
    try:
        run = await pipeline_module.run_creation(
            session,
            __import__("uuid").UUID(topic_id),
            roles=StageRoles(drafter=drafter),
            options={"style_samples": [SAMPLE_A, SAMPLE_B]},
        )
    finally:
        await gen.aclose()

    fp = run.artifacts.get("style_fingerprint")
    assert fp and fp["sample_chars"] > 0
    # SCRIPT 阶段的 user payload 含指纹提示
    import json as _json

    payload = _json.loads(llm.messages[1].content)
    assert "style_fingerprint" in payload
    assert "模仿以下作者声线" in payload["style_fingerprint"]


async def test_drafter_no_client_returns_empty():
    """无 SKILL.md 的 stage（不映射）→ 不产出草稿。"""
    drafter = make_llm_drafter(_FakeClient(data={"body": "x"}))
    # STORYBOARD 有映射 → 会尝试；用不存在的 skills_root 验证降级
    drafter2 = make_llm_drafter(_FakeClient(data={"body": "x"}), skills_root=__import__("pathlib").Path("/nonexistent"))
    out = await drafter2(CreationStage.SCRIPT, {"topic": None})
    assert out == {}
    assert drafter is not None
