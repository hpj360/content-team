"""R55：体系拆解第二批（5 部）+ 六维体系设计学蒸馏 契约测试。"""
from __future__ import annotations

import re
from pathlib import Path

from hermes.content_team.creative.corpus import (
    CORPUS_DIR,
    find_cases,
    get_case,
)

_ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "paradigm-power-system-three-body.md": (
        "TRI-T", ["技术代差", "威慑", "猜疑链", "封锁"]),
    "paradigm-power-system-battle-through-heavens.md": (
        "DPB-T", ["炼药师", "异火", "星阶", "越阶"]),
    "paradigm-power-system-rezero.md": (
        "RZ-T", ["死亡回归", "加护", "隐性数值", "代价"]),
    "paradigm-power-system-solo-leveling.md": (
        "SL-T", ["面板", "技能点", "评级", "副本"]),
    "paradigm-power-system-mushoku-tensei.md": (
        "MTS-T", ["魔术", "公会", "列强", "跨世"]),
}
SIX_DIMS = ["能力", "天赋", "经济", "科技", "实力", "数值"]
_DISTILL = _ROOT / "skills" / "novel-writing" / "references" / "power-system-design.md"


def _read_corpus(name: str) -> str:
    return (CORPUS_DIR / name).read_text(encoding="utf-8")


def test_batch_two_wellformed():
    for filename, (_prefix, _keywords) in FILES.items():
        text = _read_corpus(filename)
        assert text.lstrip().startswith("# "), f"{filename} 缺标题"
        assert len(text) > 5500, f"{filename} 内容偏薄"
        assert "版权声明" in text and "不复制" in text, f"{filename} 版权纪律缺失"
        assert "2026-11-15" in text and "content_freshness" in text, f"{filename} 缺校准/时效"


def test_batch_two_six_dimensions_and_coupling():
    for filename, (_prefix, _keywords) in FILES.items():
        text = _read_corpus(filename)
        for dim in SIX_DIMS:
            assert re.search(rf"^##\s+[^\n]*{dim}", text, flags=re.MULTILINE), (
                f"{filename} 缺维度小节 {dim}"
            )
        assert "耦合" in text and "失效" in text and "局限" in text, f"{filename} 结构缺节"


def test_batch_two_techniques_and_keywords():
    for filename, (prefix, keywords) in FILES.items():
        text = _read_corpus(filename)
        for i in range(1, 7):
            assert f"{prefix}{i}" in text, f"{filename} 缺技法 {prefix}{i}"
        for keyword in keywords:
            assert keyword in text, f"{filename} 缺核心机制 {keyword}"


def test_batch_two_registered_and_files_exist():
    ids = {c.id for c in find_cases(form="power-system")}
    expected = {
        "paradigm-power-system-three-body",
        "paradigm-power-system-battle-through-heavens",
        "paradigm-power-system-rezero",
        "paradigm-power-system-solo-leveling",
        "paradigm-power-system-mushoku-tensei",
    }
    missing = expected - ids
    assert not missing, f"第二批未注册: {missing}"
    for case_id in expected:
        case = get_case(case_id)
        assert case and (CORPUS_DIR / case.file).is_file() and case.foreshadowing_plan


def test_readme_family_and_distillation_link():
    readme = (CORPUS_DIR / "README.md").read_text(encoding="utf-8")
    assert "体系拆解（7" in readme, "README I 族计数应为 7"
    for filename in FILES:
        assert filename in readme
    assert "power-system-design" in readme, "README 缺设计学蒸馏链接"


def test_distillation_reference_complete():
    assert _DISTILL.is_file(), "power-system-design.md 未创建"
    text = _DISTILL.read_text(encoding="utf-8")
    assert text.lstrip().startswith("# ")
    for i in range(1, 11):
        assert f"S{i} " in text or f"S{i}\u3001" in text or f"### S{i}" in text, f"缺原理 S{i}"
    for concept in ("六维清单", "耦合图", "断点", "设计流程", "反模式", "自检", "蒸馏源", "局限"):
        assert concept in text, f"蒸馏篇缺 {concept}"
    assert "worldbuilding-guide" in text and "beat-sheets" in text and "event-conflict-arc" in text, (
        "蒸馏篇缺资产映射"
    )
    for word in ("打脸", "外卖员"):
        assert word not in text, f"蒸馏篇出现禁词 {word}"


def test_distillation_registered_everywhere():
    amap = (_ROOT / "knowledge" / "asset-map.md").read_text(encoding="utf-8")
    assert "power-system-design" in amap, "asset-map 缺设计学路由"
    skill = (_ROOT / "skills" / "novel-writing" / "SKILL.md").read_text(encoding="utf-8")
    assert "power-system-design" in skill, "SKILL.md 未登记设计学"
    canon = (_ROOT / "knowledge" / "methodology-canon.md").read_text(encoding="utf-8")
    assert "power-system-design" in canon, "正典 P7 未纳入设计学"


def test_no_forbidden_words_in_batch():
    for filename in FILES:
        text = _read_corpus(filename)
        for word in ("打脸", "外卖员"):
            assert word not in text, f"{filename} 出现禁词 {word}"
