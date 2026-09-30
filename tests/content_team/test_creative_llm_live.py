"""实网联调（Round 12）：对真实 LLM provider 跑通 drafter / judge / reviser。

默认跳过（不污染 CI）；显式开启：
    set CONTENT_TEAM_LIVE_LLM=1
    set HERMES_LLM_PROVIDER=zai
    set HERMES_LLM_MODEL=glm-4-flash
    # ZAI_API_KEY 已在环境中

运行：py -3.12 -m pytest tests/content_team/test_creative_llm_live.py -q
"""
from __future__ import annotations

import os
import uuid
from types import SimpleNamespace

import pytest

from hermes.content_team.creative.builders_llm import make_script_drafter
from hermes.content_team.creative.gates import count_scenes
from hermes.content_team.creative.judges import make_llm_judge
from hermes.content_team.creative.revision import make_llm_reviser
from hermes.content_team.models.creative import CreationStage

LIVE = os.environ.get("CONTENT_TEAM_LIVE_LLM") == "1"

pytestmark = pytest.mark.skipif(
    not LIVE, reason="set CONTENT_TEAM_LIVE_LLM=1 to run live LLM integration"
)


def _client():
    from hermes.workbench.llm import make_llm_client

    return make_llm_client()


def _topic(title="外卖员逆袭", description="外卖员在庆功宴被羞辱，被迫签下七天总裁协议"):
    return SimpleNamespace(title=title, description=description)


async def test_live_drafter_produces_script_body():
    """真实 LLM 起草剧本：返回合法 JSON 契约且正文含场景结构。"""
    drafter = make_script_drafter(_client())
    out = await drafter(CreationStage.SCRIPT, {"topic": _topic()})

    assert out, "实网 drafting 失败（LLM 未返回合法 JSON 契约）"
    body = out.get("body") or ""
    assert len(body) >= 60, f"正文过短：{body[:80]!r}"
    assert count_scenes(body) >= 1, f"未识别到场景：{body[:120]!r}"
    print("\n[live drafter] title=", out.get("title"), "| chars=", len(body))
    print("[live drafter] head=", body[:160].replace("\n", " / "))


async def test_live_judge_returns_notes():
    """真实 LLM 评议：返回建议清单（不门禁）。"""
    judge = make_llm_judge(_client())
    preview = (
        "第一场　内景／庆功宴·夜\n\n"
        "李默端着餐盘挤进人群，主管当众羞辱他，把工牌盒推到他面前。\n\n"
        "李默\n我不干了。\n\n"
        "主管\n签了这份七天协议，你才有资格站在这。"
    )
    notes = await judge(
        CreationStage.SCRIPT,
        {"script_title": "外卖员逆袭·剧本", "preview": preview},
        {"topic": _topic()},
    )
    assert notes, "实网 judge 未返回建议"
    assert not any("未提供正文" in n for n in notes), f"judge 未收到正文：{notes}"
    print("\n[live judge] notes=", notes)


async def test_live_reviser_returns_log():
    """真实 LLM 修订：返回与原建议对应的日志（可为 fixed=False，属正常）。"""
    backend = make_llm_reviser(
        _client(),
        rules_backend=None,
    )
    issues = [
        {
            "code": "S006",
            "message": "命中 AI 套路化表达：不由得",
            "severity": "warn",
            "dimension": "craft",
        }
    ]
    log = await backend.revise(
        {"script_id": str(uuid.uuid4()), "topic": "外卖员逆袭"},
        issues,
    )
    assert isinstance(log, list)
    print("\n[live reviser] log=", log)
