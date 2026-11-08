"""R44：工作法蒸馏两篇 + 使用手册 契约测试。"""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SKILLS = _ROOT / "skills"
_NOVEL_REF = _SKILLS / "novel-writing" / "references"
_GUIDE = _ROOT / "knowledge" / "usage-writing-with-content-team.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_chapter_continuity_wellformed():
    text = _read(_NOVEL_REF / "chapter-continuity.md")
    assert text.lstrip().startswith("# ")
    assert len(text) > 4500, "蒸馏篇内容偏薄"
    # 转场七法
    for law in ("尾词复现", "物件接力", "声音桥", "行走过渡", "时间铆钉", "回环句", "制式桥"):
        assert law in text, f"缺转场法 {law}"
    # 叙述五层
    for layer in ("视角层", "信息层", "因果层", "支线层", "语感层"):
        assert layer in text, f"缺叙述层 {layer}"
    # 关键机制
    for concept in ("三型跳跃", "语者恒定", "半句定理", "补票", "支线预算", "修订归因"):
        assert concept in text, f"缺机制 {concept}"
    assert "局限" in text


def test_chapter_continuity_dedup_references():
    """去重要求：只交叉引用、不复述既有的过渡四类/叙述距离/节拍表。"""
    text = _read(_NOVEL_REF / "chapter-continuity.md")
    for target in ("scene-engineering", "narratology-toolbox", "beat-sheets", "web-fiction-craft"):
        assert target in text, f"缺去重交叉引用 {target}"


def test_rule_horror_wellformed():
    text = _read(_NOVEL_REF / "rule-horror-techniques.md")
    assert text.lstrip().startswith("# ")
    assert len(text) > 4200, "蒸馏篇内容偏薄"
    for concept in ("触发", "禁忌", "后果", "不可协商", "三级", "理解成本", "植入位", "卷宗"):
        assert concept in text, f"缺概念 {concept}"
    assert "局限" in text
    # 与既有资产分工
    for target in ("worldbuilding-guide", "genre-mystery", "paradigm-vertical-interactive"):
        assert target in text, f"缺分工互引 {target}"


def test_both_registered_in_skill_md():
    skill = _read(_SKILLS / "novel-writing" / "SKILL.md")
    for name in ("chapter-continuity.md", "rule-horror-techniques.md"):
        assert f"references/{name}" in skill, f"SKILL.md 未登记 {name}"


def test_usage_guide_actionable():
    text = _read(_GUIDE)
    assert text.lstrip().startswith("# ")
    for section in ("写前", "写中", "写后", "决策速查", "五道门"):
        assert section in text, f"手册缺章节 {section}"
    # 必须给出真实接口与命令
    for api in ("/api/creation/runs", "/api/novels", "/api/knowledge/search", "/api/corpus"):
        assert api in text, f"手册缺接口 {api}"
    assert "uvicorn" in text, "手册缺启动命令"
    assert "局限" in text


def test_usage_guide_lists_new_references():
    text = _read(_GUIDE)
    for name in ("chapter-continuity.md", "rule-horror-techniques.md", "revision-diagnosis.md"):
        assert name in text, f"手册未引用 {name}"


def test_no_wholesale_copy_markers():
    banned = ("原文如下", "全文如下", "照录如下")
    for path in (_NOVEL_REF / "chapter-continuity.md", _NOVEL_REF / "rule-horror-techniques.md", _GUIDE):
        text = _read(path)
        for word in banned:
            assert word not in text, f"{path.name} 出现整段引用痕迹 {word}"
