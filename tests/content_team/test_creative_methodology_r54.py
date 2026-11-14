"""R54：体系拆解（能力/天赋/经济/科技/实力/数值六维）契约测试。"""
from __future__ import annotations

import re
from pathlib import Path

from hermes.content_team.creative.corpus import (
    CORPUS_DIR,
    corpus_refs_for,
    find_cases,
    get_case,
)

_ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "paradigm-power-system-lord-of-mysteries.md": ("LOM-T", ["序列", "扮演法", "金镑", "封印物"]),
    "paradigm-power-system-mortal-cultivation.md": ("MC-T", ["灵根", "灵石", "越阶", "寿元"]),
}
SIX_DIMS = ["能力", "天赋", "经济", "科技", "实力", "数值"]


def _read(name: str) -> str:
    return (CORPUS_DIR / name).read_text(encoding="utf-8")


def test_power_system_files_wellformed():
    for filename, _payload in FILES.items():
        text = _read(filename)
        assert text.lstrip().startswith("# "), f"{filename} 缺标题"
        assert len(text) > 5500, f"{filename} 内容偏薄"
        assert "版权声明" in text and ("不复制" in text), f"{filename} 版权纪律缺失"
        assert "2026-11-15" in text and "content_freshness" in text, f"{filename} 缺校准/时效"


def test_six_dimensions_and_coupling():
    for filename, _payload in FILES.items():
        text = _read(filename)
        for dim in SIX_DIMS:
            # 每维须有独立小节（## N、能力 之类）
            assert re.search(rf"^##\s+[^\n]*{dim}", text, flags=re.MULTILINE), (
                f"{filename} 缺维度小节 {dim}"
            )
        assert "耦合" in text, f"{filename} 缺六维耦合图"
        assert "失效" in text, f"{filename} 缺失效信号"
        assert "局限" in text


def test_transferable_techniques_numbered():
    for filename, (prefix, _keywords) in FILES.items():
        text = _read(filename)
        for i in range(1, 7):
            assert f"{prefix}{i}" in text, f"{filename} 缺技法 {prefix}{i}"


def test_core_mechanisms_present():
    for filename, (_prefix, keywords) in FILES.items():
        text = _read(filename)
        for keyword in keywords:
            assert keyword in text, f"{filename} 缺核心机制 {keyword}"


def test_cases_registered_with_form():
    ids = {c.id for c in find_cases(form="power-system")}
    assert {
        "paradigm-power-system-lord-of-mysteries",
        "paradigm-power-system-mortal-cultivation",
    } <= ids, f"首批体系拆解注册缺失: {ids}"
    for case_id in ids:
        case = get_case(case_id)
        assert case and case.genres and case.tags and case.summary
        assert (CORPUS_DIR / case.file).is_file()
        assert case.foreshadowing_plan, f"{case_id} 缺伏笔计划"


def test_readme_and_asset_map_updated():
    readme = (CORPUS_DIR / "README.md").read_text(encoding="utf-8")
    assert "I. 体系拆解" in readme, "README 语料地图缺 I 族"
    for filename in FILES:
        assert filename in readme, f"README 缺 {filename}"
    amap = (_ROOT / "knowledge" / "asset-map.md").read_text(encoding="utf-8")
    assert "paradigm-power-system" in amap, "asset-map 缺体系拆解路由"


def test_waimai_top2_contract_unchanged():
    assert "shortdrama-waimai-example" in corpus_refs_for("复仇打脸 都市 短剧 外卖员")


def test_no_forbidden_words():
    for filename in FILES:
        text = _read(filename)
        for word in ("打脸", "外卖员"):
            assert word not in text, f"{filename} 出现禁词 {word}"
