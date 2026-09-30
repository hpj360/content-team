"""R15：提示词变体（离线）测试。"""
from __future__ import annotations

from hermes.content_team.creative.builders_llm import (
    make_llm_drafter,
    make_script_drafter,
)
from hermes.content_team.creative.prompts import (
    DEFAULT_VARIANT,
    DRAFTER_CONTRACTS,
    available_variants,
    drafter_contract,
)
from hermes.content_team.models.creative import CreationStage

from tests.content_team._fakes import FakeLlmClient


def test_variants_registry():
    assert set(available_variants()) == {"v1", "v2", "v3"}
    assert DEFAULT_VARIANT in DRAFTER_CONTRACTS


def test_contract_fallback_for_unknown_variant():
    assert drafter_contract("nope") == drafter_contract(DEFAULT_VARIANT)
    assert drafter_contract(None) == drafter_contract(DEFAULT_VARIANT)


def test_v2_enforces_quotas():
    v2 = drafter_contract("v2")
    assert "至少包含 3 个场次" in v2
    assert "300–900 字" in v2
    assert "钩子" in v2


def test_v3_adds_style_anchoring():
    v3 = drafter_contract("v3")
    assert "文风指纹" in v3
    assert "禁止 AI 腔" in v3


async def test_drafter_uses_selected_variant():
    llm = FakeLlmClient(data={"title": "t", "body": "第一场　内景／日\n动作。"})
    drafter = make_script_drafter(llm, prompt_variant="v2")
    await drafter(CreationStage.SCRIPT, {"topic": None})
    system = llm.messages[0].content
    assert "至少包含 3 个场次" in system  # v2 契约进入 system
    assert "文风指纹" not in system  # v3 内容不出现


async def test_drafter_default_variant_selected():
    llm = FakeLlmClient(data={"body": "第一场 x"})
    await make_llm_drafter(llm)(CreationStage.SCRIPT, {"topic": None})
    assert drafter_contract(None) in llm.messages[0].content
