"""R56：语料扩线（群像/反派/诡计 3 部）+ 方法论闭环（回填/审查单/出图配方/一致性审查）契约测试。"""
from __future__ import annotations

from pathlib import Path

from hermes.content_team.creative.corpus import (
    CORPUS_DIR,
    find_cases,
    get_case,
)

_ROOT = Path(__file__).resolve().parents[2]

CORPUS_FILES = {
    "paradigm-ensemble-sanguo.md": ("SG-T", ["势力线", "合流", "谋略", "群像"]),
    "breakdown-godfather-michael-arc.md": ("GF-T", ["旁观者", "掌权", "洗礼", "道德测量"]),
    "breakdown-orient-express.md": ("OE-T", ["公平", "嫌疑人", "密闭", "证词"]),
}
_NOVEL_REFS = _ROOT / "skills" / "novel-writing" / "references"
_SB_REFS = _ROOT / "skills" / "storyboarding" / "references"


def _corpus(name: str) -> str:
    return (CORPUS_DIR / name).read_text(encoding="utf-8")


def test_corpus_batch_wellformed():
    for filename, (_prefix, _keywords) in CORPUS_FILES.items():
        text = _corpus(filename)
        assert text.lstrip().startswith("# "), f"{filename} 缺标题"
        assert len(text) > 5500, f"{filename} 内容偏薄"
        assert "版权声明" in text, f"{filename} 版权纪律缺失"
        assert "2026-11-15" in text and "content_freshness" in text, f"{filename} 缺校准/时效"
        assert "局限" in text, f"{filename} 缺局限"


def test_corpus_batch_techniques_and_keywords():
    for filename, (prefix, keywords) in CORPUS_FILES.items():
        text = _corpus(filename)
        for i in range(1, 7):
            assert f"{prefix}{i}" in text, f"{filename} 缺技法 {prefix}{i}"
        for keyword in keywords:
            assert keyword in text, f"{filename} 缺核心机制 {keyword}"


def test_corpus_batch_registered():
    ids = {c.id for c in find_cases()}
    expected = {
        "paradigm-ensemble-sanguo",
        "breakdown-godfather-michael-arc",
        "breakdown-orient-express",
    }
    missing = expected - ids
    assert not missing, f"未注册: {missing}"
    for case_id in expected:
        case = get_case(case_id)
        assert case and (CORPUS_DIR / case.file).is_file() and case.foreshadowing_plan


def test_readme_families_updated():
    readme = (CORPUS_DIR / "README.md").read_text(encoding="utf-8")
    assert "E. 长篇双轨范式（3）" in readme, "README E 族计数应为 3"
    assert "H. 全拆与档案拆解 | 9" in readme, "README 地图 H 族计数应为 9"
    for filename in CORPUS_FILES:
        assert filename in readme, f"README 缺 {filename}"


def test_power_system_design_backfilled():
    text = (_NOVEL_REFS / "power-system-design.md").read_text(encoding="utf-8")
    assert "七部校准" in text, "设计学头部未升级为七部"
    assert "校准例证" in text, "缺 S1–S10 回填例证表"
    for work in ("斗破", "Re:Zero", "无职", "SL", "三体"):
        assert work in text, f"例证表缺 {work}"
    assert "体系一致性审查单" in text, "缺一致性审查单"
    for item in ("主数值单调", "兑换表稳定", "三重前置齐全", "倒计时在跑", "天花板在场"):
        assert item in text, f"审查单缺 {item}"
    assert "## 十、局限" in text, "局限节号应顺延为十"


def test_asset_consistency_audit():
    text = (_NOVEL_REFS / "asset-consistency-audit.md").read_text(encoding="utf-8")
    assert text.lstrip().startswith("# ")
    assert len(text) > 4500, "资产一致性审查内容偏薄"
    for concept in ("单一事实源", "审查五步", "抽查节奏", "对账表", "高频陷阱", "自检", "局限"):
        assert concept in text, f"缺 {concept}"
    for word in ("打脸", "外卖员"):
        assert word not in text, f"禁词 {word}"


def test_ai_image_recipe():
    text = (_SB_REFS / "ai-image-recipe.md").read_text(encoding="utf-8")
    assert text.lstrip().startswith("# ")
    assert len(text) > 4500, "出图配方内容偏薄"
    for concept in ("场景图", "角色立绘", "道具图", "字段", "一致性", "负面词", "失败", "自检", "局限"):
        assert concept in text, f"缺 {concept}"
    for word in ("打脸", "外卖员"):
        assert word not in text, f"禁词 {word}"


def test_adaptation_guide_transition_map():
    text = (_ROOT / "skills" / "script-writing" / "references" / "adaptation-guide.md").read_text(
        encoding="utf-8"
    )
    assert "文学 ↔ 影视转场对照表" in text, "adaptation-guide 缺转场对照表"
    for method in ("尾词复现", "物件接力", "声音桥", "回环句", "制式桥"):
        assert method in text, f"对照表缺七法 {method}"


def test_registrations():
    amap = (_ROOT / "knowledge" / "asset-map.md").read_text(encoding="utf-8")
    assert "asset-consistency-audit" in amap and "ai-image-recipe" in amap
    skill_n = (_ROOT / "skills" / "novel-writing" / "SKILL.md").read_text(encoding="utf-8")
    assert "asset-consistency-audit" in skill_n
    skill_sb = (_ROOT / "skills" / "storyboarding" / "SKILL.md").read_text(encoding="utf-8")
    assert "ai-image-recipe" in skill_sb
    canon = (_ROOT / "knowledge" / "methodology-canon.md").read_text(encoding="utf-8")
    assert "asset-consistency-audit" in canon


def test_task_list_file_exists():
    tl = _ROOT / "content-creation" / "novel" / "51-吞兽维修师-细节批量补写任务清单.md"
    assert tl.is_file(), "A 线任务清单缺失"
    text = tl.read_text(encoding="utf-8")
    for section in ("T0 前置阅读", "T1 P0", "T2 P1", "T3 档位复检", "T4 管线对比", "验收标准"):
        assert section in text, f"任务清单缺 {section}"


def test_no_forbidden_words_in_corpus_batch():
    for filename in CORPUS_FILES:
        text = _corpus(filename)
        for word in ("打脸", "外卖员"):
            assert word not in text, f"{filename} 出现禁词 {word}"
