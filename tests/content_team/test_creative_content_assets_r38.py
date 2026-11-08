"""R38：长篇双轨语料（冰与火之歌专篇 + 网文爆款引擎六作逐案）契约测试。"""
from __future__ import annotations

from pathlib import Path

from hermes.content_team.creative.corpus import (
    CORPUS_DIR,
    find_cases,
    get_case,
    corpus_refs_for,
)

_ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "paradigm-western-epic-asoiaf.md": (["冰与火之歌", "POV"], "A-T"),
    "paradigm-webnovel-hit-masters.md": (
        ["十日终焉", "斩神", "我不是戏神", "剑来", "持械入宋", "悟空传"], "E-T"),
}

ASOIAF_QUOTES = ["凛冬将至", "凡人皆有一死", "混乱不是深渊"]
WEBNOVEL_TECHNICS = ["数值化", "轮回", "禁墟", "语录", "AI 合规"]

DIMS = ["核心命题", "叙事结构", "台词", "热梗", "可迁移"]


def test_files_wellformed_and_disciplined():
    for filename, _payload in FILES.items():
        text = (CORPUS_DIR / filename).read_text(encoding="utf-8")
        assert text.lstrip().startswith("# "), f"{filename} 缺标题"
        assert len(text) > 2000, f"{filename} 内容过短"
        assert "版权声明" in text and "不复制" in text, f"{filename} 版权纪律缺失"
        assert "可迁移" in text, f"{filename} 缺可迁移"
        assert "2026-11-04" in text and "content_freshness" in text, f"{filename} 缺校准/复审"


def test_six_dimensions_and_techniques():
    for filename, (_payload, prefix) in FILES.items():
        text = (CORPUS_DIR / filename).read_text(encoding="utf-8")
        for dim in DIMS:
            assert dim in text, f"{filename} 缺维度 {dim}"
        for i in range(1, 9):
            assert f"{prefix}{i}" in text, f"{filename} 缺技法 {prefix}{i}"


def test_asoiaf_mechanisms_and_quotes():
    text = (CORPUS_DIR / "paradigm-western-epic-asoiaf.md").read_text(encoding="utf-8")
    for mechanism in ("POV 章节制", "家族线账本", "婚约攻防", "低魔", "事件代词"):
        assert mechanism in text, f"缺机制 {mechanism}"
    for quote in ASOIAF_QUOTES:
        assert quote in text, f"缺金句档案 {quote}"


def test_webnovel_six_cases():
    text = (CORPUS_DIR / "paradigm-webnovel-hit-masters.md").read_text(encoding="utf-8")
    for work in ("十日终焉", "斩神", "我不是戏神", "剑来", "持械入宋", "悟空传"):
        assert work in text, f"缺逐案 {work}"
    assert text.count("设定卡") >= 6, "六案应各含设定卡"
    for technic in WEBNOVEL_TECHNICS:
        assert technic in text, f"缺核心工艺 {technic}"


def test_cases_registered():
    for case_id in ("paradigm-western-epic-asoiaf", "paradigm-webnovel-hit-masters"):
        case = get_case(case_id)
        assert case is not None, f"index.json 缺 {case_id}"
        assert case.genres and case.tags and case.summary, f"{case_id} 维度不全"
        assert case.file and (CORPUS_DIR / case.file).is_file()
    with_plan = {c.id for c in find_cases() if c.foreshadowing_plan}
    assert {
        "paradigm-western-epic-asoiaf", "paradigm-webnovel-hit-masters"
    } <= with_plan


def test_waimai_top2_contract_unchanged():
    assert "shortdrama-waimai-example" in corpus_refs_for("复仇打脸 都市 短剧 外卖员")


def test_readme_rows_registered():
    readme = (CORPUS_DIR / "README.md").read_text(encoding="utf-8")
    for filename in FILES:
        assert filename in readme, f"README 缺 {filename}"
