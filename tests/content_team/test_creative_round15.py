"""Round 15–18：文风指纹持久化 / 成本治理 / 默认多角色 / 内容模板。"""
from __future__ import annotations

import uuid

import hermes.content_team.creative.pipeline as pipeline_module
from hermes.content_team.creative.cost import (
    BudgetExceeded,
    UsageTracker,
    current_tracker,
    reset_tracker,
    set_tracker,
)
from hermes.content_team.creative.judges import make_checklist_critic
from hermes.content_team.creative.llm_io import chat_json_safe
from hermes.content_team.creative.planners import (
    compose_planners,
    make_beat_sheet_planner,
)
from hermes.content_team.creative.templates import (
    get_template,
    list_templates,
    render_template,
)
from hermes.content_team.models.creative import CreationStage

from tests.content_team._fakes import FakeLlmClient


async def _session_from_app():
    from hermes.content_team.app import app
    from hermes.content_team.db import get_db

    gen = app.dependency_overrides[get_db]()
    return gen, await gen.__anext__()


async def _topic(client, title="迭代题", description="外卖员被羞辱后逆袭"):
    return (
        await client.post(
            "/api/topics", json={"title": title, "description": description}
        )
    ).json()["id"]


# ---------------------------------------------------------------------------
# R15：文风指纹持久化与复用
# ---------------------------------------------------------------------------

SAMPLES = [
    "雨点砸在铁皮屋顶。他数到三。门开了。\n\n「你迟到了。」她说。",
    "灯灭了。整条街只剩一盏。他没回头。",
]


async def test_fingerprint_persisted_on_novel_via_api(client):
    """PUT /novels/{id}/style-fingerprint 持久化；GET 可见。"""
    topic_id = await _topic(client)
    run = (
        await client.post("/api/creation/runs", json={"topic_id": topic_id})
    ).json()
    novel_id = run["artifacts"]["novel_id"]

    resp = await client.put(
        f"/api/novels/{novel_id}/style-fingerprint", json={"samples": SAMPLES}
    )
    assert resp.status_code == 200
    fp = resp.json()["style_fingerprint"]
    assert fp and fp["sample_chars"] > 0 and fp["top_words"]

    got = await client.get(f"/api/novels/{novel_id}")
    assert got.json()["style_fingerprint"]["sample_chars"] == fp["sample_chars"]


async def test_fingerprint_reused_from_novel_in_later_run(client):
    """后续 run 以 options.novel_id 引用时复用已存指纹（注入 drafter）。"""
    topic_id = await _topic(client, title="复用题")
    run = (
        await client.post("/api/creation/runs", json={"topic_id": topic_id})
    ).json()
    novel_id = run["artifacts"]["novel_id"]
    await client.put(
        f"/api/novels/{novel_id}/style-fingerprint", json={"samples": SAMPLES}
    )

    from hermes.content_team.creative.builders_llm import make_script_drafter

    llm = FakeLlmClient(data={"title": "t", "body": "第一场 内景/日\n动作。"})
    drafter = make_script_drafter(llm)

    gen, session = await _session_from_app()
    try:
        reused = await pipeline_module.run_creation(
            session,
            uuid.UUID(topic_id),
            roles=pipeline_module.StageRoles(drafter=drafter),
            options={"novel_id": novel_id},
        )
    finally:
        await gen.aclose()

    # drafter 收到的 user payload 含风格指纹提示
    import json

    payload = json.loads(llm.messages[1].content)
    assert "style_fingerprint" in payload
    assert "模仿以下作者声线" in payload["style_fingerprint"]
    assert reused.artifacts.get("style_fingerprint")


async def test_fingerprint_endpoint_rejects_empty(client):
    topic_id = await _topic(client, title="空样本")
    run = (
        await client.post("/api/creation/runs", json={"topic_id": topic_id})
    ).json()
    novel_id = run["artifacts"]["novel_id"]
    resp = await client.put(
        f"/api/novels/{novel_id}/style-fingerprint", json={"samples": ["   "]}
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# R16：成本治理（token 记账 + 预算护栏）
# ---------------------------------------------------------------------------


def test_usage_tracker_accumulates_and_budget():
    tracker = UsageTracker(budget_tokens=100)
    assert current_tracker() is None
    token = set_tracker(tracker)
    try:
        assert current_tracker() is tracker
        chat_json_safe(FakeLlmClient(data={"ok": 1}), [], role="drafter")
    finally:
        reset_tracker(token)
    assert tracker.calls == 1
    assert tracker.to_dict()["total_tokens"] == 0  # fake 无 usage 字段

    tracker.record(prompt_tokens=60, completion_tokens=50, role="x")
    assert tracker.over_budget
    try:
        tracker.check(role="x")
        raised = False
    except BudgetExceeded:
        raised = True
    assert raised


async def test_budget_exceeded_degrades_llm_role(client):
    """预算为 0 时，LLM 角色被守卫拦截 → 降级（不影响管线成功）。"""
    topic_id = await _topic(client, title="预算题")
    from hermes.content_team.creative.builders_llm import make_script_drafter

    drafter = make_script_drafter(FakeLlmClient(data={"body": "第一场 x"}))

    gen, session = await _session_from_app()
    try:
        run = await pipeline_module.run_creation(
            session,
            uuid.UUID(topic_id),
            roles=pipeline_module.StageRoles(drafter=drafter),
            budget_tokens=0,  # 立即超限
        )
    finally:
        await gen.aclose()

    assert run.status.value in {"SUCCEEDED", "NEEDS_REVISION"}
    assert run.llm_usage["over_budget"] is True
    assert run.token_total == 0
    script = await client.get(f"/api/scripts/{run.artifacts['script_id']}")
    assert "建置" in script.json()["body"]  # 降级到模板


async def test_creation_run_exposes_usage(client):
    topic_id = await _topic(client, title="用量题2")
    run = (
        await client.post("/api/creation/runs", json={"topic_id": topic_id})
    ).json()
    assert "llm_usage" in run and "token_total" in run
    assert isinstance(run["llm_usage"], dict)


# ---------------------------------------------------------------------------
# R17：默认多角色（节奏规划 + 清单评议）
# ---------------------------------------------------------------------------


async def test_beat_sheet_planner_returns_script_params():
    planner = make_beat_sheet_planner()

    class T:
        title = "都市短剧"
        description = "外卖员逆袭"

    plan = await planner(CreationStage.SCRIPT, {"topic": T()})
    assert plan["target_scenes"] >= 3
    assert "pacing_hint" in plan and "beat_sheet" in plan
    # 非 SCRIPT 阶段不干预
    assert await planner(CreationStage.NOVEL, {"topic": T()}) == {}


async def test_compose_planners_merges():
    async def a(stage, ctx):
        return {"x": 1}

    async def b(stage, ctx):
        return {"y": 2, "x": 9}

    merged = await compose_planners(a, b)(CreationStage.SCRIPT, {})
    assert merged == {"x": 9, "y": 2}


async def test_checklist_critic_flags_short_dialogue():
    critic = make_checklist_critic()
    notes = await critic(CreationStage.SCRIPT, {"preview": "面板上一行行文字，全无对话。"}, {})
    assert any("对话" in n for n in notes)


async def test_default_roles_run_produce_plan_and_notes(client):
    """默认 run 会应用节奏规划与清单评议（不门禁）。"""
    topic_id = await _topic(client, title="默认角色")
    run = (
        await client.post("/api/creation/runs", json={"topic_id": topic_id})
    ).json()
    script_rounds = [r for r in run["stage_results"] if r["stage"] == "SCRIPT"]
    assert script_rounds and script_rounds[0]["plan"].get("target_scenes")
    assert any(r["critic_notes"] for r in run["stage_results"])


async def test_default_roles_disabled(client):
    topic_id = await _topic(client, title="禁用角色")
    gen, session = await _session_from_app()
    try:
        run = await pipeline_module.run_creation(
            session, uuid.UUID(topic_id), default_roles=False
        )
    finally:
        await gen.aclose()
    assert all(r["plan"] == {} for r in run.stage_results)
    assert all(not r["critic_notes"] for r in run.stage_results)


# ---------------------------------------------------------------------------
# R18：内容模板系统
# ---------------------------------------------------------------------------


def test_list_templates_includes_builtins():
    templates = list_templates()
    ids = {t.id for t in templates}
    assert {"novel-golden-three", "short-drama-episode-8beat",
            "storyboard-dialogue-scene", "directing-style-pack-starter"} <= ids


def test_get_and_render_template():
    assert get_template("nonexistent") is None
    rendered = render_template(
        "novel-golden-three",
        {"书名": "山海纪", "主角": "林越", "核心卖点": "寻父", "金手指": "青铜镜",
         "初始冲突": "被逐出宗门"},
    )
    assert "《山海纪》" in rendered and "林越" in rendered
    # 未提供变量保留占位符
    assert "{书名}" not in rendered


def test_render_unknown_template_returns_none():
    assert render_template("nope", {}) is None


async def test_templates_api(client):
    resp = await client.get("/api/templates")
    assert resp.status_code == 200
    assert len(resp.json()) >= 4

    one = await client.get("/api/templates/short-drama-episode-8beat")
    assert one.status_code == 200 and one.json()["category"] == "script"

    rendered = await client.post(
        "/api/templates/short-drama-episode-8beat/render",
        json={"variables": {"集数": 3, "集名": "食堂风波"}},
    )
    assert rendered.status_code == 200
    assert "【第3集】食堂风波" in rendered.json()["rendered"]

    missing = await client.get("/api/templates/does-not-exist")
    assert missing.status_code == 404
