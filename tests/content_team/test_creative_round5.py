"""Round 5：章号区间校验、LLM 生产修订器、审查报告导出。"""
from __future__ import annotations

import json

from tests.content_team._fakes import FakeLlmClient as _FakeClient
from hermes.content_team.creative.gates import (
    gate_foreshadowing_lifecycle,
    parse_chapter_number,
)
from hermes.content_team.creative.reporting import render_run_report
from hermes.content_team.creative.revision import make_llm_reviser


# ---------------------------------------------------------------------------
# 章号解析
# ---------------------------------------------------------------------------


def test_parse_chapter_number_digits():
    assert parse_chapter_number("第3章回收") == 3
    assert parse_chapter_number("第12章") == 12
    assert parse_chapter_number("第3回") is None
    assert parse_chapter_number("") is None


def test_parse_chapter_number_chinese():
    assert parse_chapter_number("第十章") == 10
    assert parse_chapter_number("第二十三章") == 23
    assert parse_chapter_number("第一百章") == 100


# ---------------------------------------------------------------------------
# 生命周期区间校验
# ---------------------------------------------------------------------------


def _fs(**kw):
    item = {
        "id": "F1",
        "content": "神秘信件来了",
        "planted_at": "第1章",
        "planned_resolution": "第3章回收",
        "status": "planted",
        "keyword": "信件",
    }
    item.update(kw)
    return item


def test_l004_planted_range_miss():
    data = {
        "foreshadowing": [_fs()],
        "chapter_bodies": [
            {"chapter_number": 1, "body": "无关章节。"},
            {"chapter_number": 2, "body": "他收到信件。"},  # 其他章命中不算埋设
        ],
    }
    report = gate_foreshadowing_lifecycle(data)
    assert "L004" in [i.code for i in report.errors]
    assert "L001" not in [i.code for i in report.errors]  # 区间优先于全局兜底


def test_range_hit_passes():
    data = {
        "foreshadowing": [_fs()],
        "chapter_bodies": [{"chapter_number": 1, "body": "桌上有一封信件。"}],
    }
    assert gate_foreshadowing_lifecycle(data).passed


def test_l001_fallback_when_planted_chapter_absent():
    data = {
        "foreshadowing": [_fs()],
        "chapter_bodies": [{"chapter_number": 5, "body": "后续章与此无关。"}],
    }
    report = gate_foreshadowing_lifecycle(data)
    assert "L001" in [i.code for i in report.errors]
    assert "L004" not in [i.code for i in report.errors]


def test_l005_resolved_but_resolution_chapter_miss():
    data = {
        "foreshadowing": [_fs(status="resolved")],
        "chapter_bodies": [
            {"chapter_number": 1, "body": "桌上有一封信件。"},
            {"chapter_number": 3, "body": "本章讲别的。"},
        ],
    }
    report = gate_foreshadowing_lifecycle(data)
    assert "L005" in [i.code for i in report.errors]


def test_l005_skipped_when_resolution_chapter_not_written():
    data = {
        "foreshadowing": [_fs(status="resolved")],
        "chapter_bodies": [{"chapter_number": 1, "body": "桌上有一封信件。"}],
    }
    assert gate_foreshadowing_lifecycle(data).passed


# ---------------------------------------------------------------------------
# LLM 生产修订器（可注入 fake client）
# ---------------------------------------------------------------------------


async def test_make_llm_reviser_parses_log():
    client = _FakeClient(
        data={"log": [{"code": "S004", "fixed": True, "action": "llm-补场景"}]}
    )
    backend = make_llm_reviser(client)
    log = await backend.revise({"script_id": "x"}, [{"code": "S004"}])
    assert len(client.calls) == 1
    assert log == [{"code": "S004", "fixed": True, "action": "llm-补场景"}]


async def test_make_llm_reviser_llm_failure_returns_empty():
    client = _FakeClient(error=RuntimeError("LLM down"))
    backend = make_llm_reviser(client)
    log = await backend.revise({"script_id": "x"}, [{"code": "S004"}])
    assert log == []


async def test_make_llm_reviser_rules_first_then_llm_rest():
    """可规则修复的编码先走规则版；LLM 只收剩余问题。"""
    from hermes.content_team.creative.revision import CreativeReviser

    seen_by_llm: list = []

    class _SpyClient(_FakeClient):
        def chat(self, messages, *, max_tokens=None, **_kw):
            seen_by_llm.append(messages)
            from types import SimpleNamespace

            return SimpleNamespace(content='{"log": []}', finish_reason="stop")

    class _SpyRules(CreativeReviser):
        async def revise(self, artifacts, issues):  # type: ignore[override]
            self.seen = list(issues)
            log = []
            for issue in issues:
                if issue["code"] == "S004":
                    log.append({"code": "S004", "fixed": True, "action": "rules"})
                else:
                    log.append(
                        {"code": issue["code"], "fixed": False, "action": "unsupported"}
                    )
            return log

    rules = _SpyRules(db=None)  # type: ignore[arg-type]
    client = _SpyClient(data={"log": []})
    backend = make_llm_reviser(client, rules_backend=rules)

    issues = [{"code": "S004"}, {"code": "ZZZ"}]  # S004 可规则修复，ZZZ 不行
    log = await backend.revise({}, issues)

    assert [e["code"] for e in log if e["action"] == "rules"] == ["S004"]
    # LLM 收到的剩余问题只有 ZZZ（且确被调用过一次）
    assert len(seen_by_llm) == 1
    payload = json.loads(seen_by_llm[0][1].content)
    assert [i["code"] for i in payload["issues"]] == ["ZZZ"]


# ---------------------------------------------------------------------------
# 报告导出
# ---------------------------------------------------------------------------


def _fake_run(**kw):
    from hermes.content_team.models.creative import (
        CreationRun,
        CreationRunStatus,
        RevisionOutcome,
    )

    defaults = dict(
        stages=["NOVEL", "SCRIPT"],
        status=CreationRunStatus.NEEDS_REVISION,
        review_score=55.0,
        revise_rounds=1,
        revision_outcome=RevisionOutcome.EXHAUSTED,
        review={
            "passed": False,
            "error_count": 1,
            "warning_count": 1,
            "dimensions": {"structure": 55.0, "compliance": 100.0},
            "stage_issues": {
                "SCRIPT": [
                    {
                        "code": "S004",
                        "severity": "error",
                        "message": "场景数 1 少于 3",
                    }
                ]
            },
        },
        revise_log=[{"code": "S004", "fixed": False, "action": "补全场景"}],
        artifacts={"script_id": "abc"},
        error_message="修订轮次耗尽：总分 55.0 < 80",
    )
    defaults.update(kw)
    return CreationRun(**defaults)


def test_report_contains_overview_and_issues():
    report = render_run_report(_fake_run())
    assert "# 创作审查报告" in report
    assert "需修订" in report
    assert "55.0" in report
    assert "EXHAUSTED" in report
    assert "S004" in report and "场景数 1 少于 3" in report
    assert "补全场景" in report
    assert "script_id" in report


def test_report_without_review_renders():
    run = _fake_run(
        status=__import__(
            "hermes.content_team.models.creative", fromlist=["CreationRunStatus"]
        ).CreationRunStatus.SUCCEEDED,
        review=None,
        review_score=None,
        revise_rounds=0,
        revise_log=[],
        error_message=None,
        artifacts={},
    )
    report = render_run_report(run)
    assert "通过" in report
    assert "-" in report  # 缺省分占位


# ---------------------------------------------------------------------------
# 报告导出 API（端到端）
# ---------------------------------------------------------------------------


async def test_report_endpoint_markdown_and_json(client):
    """/runs/{id}/report 支持 markdown 与 json。"""
    topic = (
        await client.post(
            "/api/topics", json={"title": "报告题", "description": "导出"}
        )
    ).json()["id"]
    run = (
        await client.post("/api/creation/runs", json={"topic_id": topic})
    ).json()
    run_id = run["id"]

    resp = await client.get(f"/api/creation/runs/{run_id}/report")
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]
    assert "# 创作审查报告" in resp.text
    assert run_id in resp.text

    resp_json = await client.get(f"/api/creation/runs/{run_id}/report?format=json")
    assert resp_json.status_code == 200
    assert "application/json" in resp_json.headers["content-type"]
    data = resp_json.json()
    assert data["run_id"] == run_id
    assert data["review_score"] is not None


async def test_report_endpoint_404(client):
    resp = await client.get(
        "/api/creation/runs/00000000-0000-0000-0000-000000000000/report"
    )
    assert resp.status_code == 404
