"""R43：原理层方法论五件套契约测试（叙述学/钩子机制/场景工程/诊断法/主题工程）。"""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SKILLS = _ROOT / "skills"

FILES = {
    "novel-writing/references/narratology-toolbox.md": [
        "视角", "叙述距离", "时序", "叙事速度", "自由间接",
    ],
    "novel-writing/references/hook-mechanics.md": [
        "好奇缺口", "蔡格尼克", "预期违背", "信息不对称", "失效",
    ],
    "script-writing/references/scene-engineering.md": [
        "价值翻转", "删除测试", "进入钩", "退出钩", "过渡",
    ],
    "script-writing/references/revision-diagnosis.md": [
        "结构体检", "场景体检", "句子体检", "手术", "诊断表",
    ],
    "novel-writing/references/theme-engineering.md": [
        "控制性观念", "命题", "反命题", "综合", "象征",
    ],
}

# 每份方法论必须声明与仓库资产的落点（可被 planner/gates 消费）
MAPPING_MARKERS = ["gates", "planner", "beat-sheets", "revision", "StoryState"]


def _read(rel: str) -> str:
    return (_SKILLS / rel).read_text(encoding="utf-8")


def test_files_exist_and_substantial():
    for rel in FILES:
        path = _SKILLS / rel
        assert path.is_file(), f"缺文件 {rel}"
        text = path.read_text(encoding="utf-8")
        assert text.lstrip().startswith("# "), f"{rel} 缺一级标题"
        assert len(text) > 3500, f"{rel} 内容偏薄（原理层应 ≥3500 字符）"


def test_required_concepts_present():
    for rel, concepts in FILES.items():
        text = _read(rel)
        for concept in concepts:
            assert concept in text, f"{rel} 缺核心概念 {concept}"


def test_each_has_checklist_and_limitations():
    for rel in FILES:
        text = _read(rel)
        assert "自检" in text or "清单" in text, f"{rel} 缺自检清单"
        assert "局限" in text, f"{rel} 缺局限声明"


def test_each_maps_to_repo_assets():
    for rel in FILES:
        text = _read(rel)
        assert any(marker in text for marker in MAPPING_MARKERS), (
            f"{rel} 未声明与仓库资产的落点映射"
        )


def test_skill_md_links_all_new_references():
    novel = (_SKILLS / "novel-writing" / "SKILL.md").read_text(encoding="utf-8")
    script = (_SKILLS / "script-writing" / "SKILL.md").read_text(encoding="utf-8")
    for name in ("narratology-toolbox.md", "hook-mechanics.md", "theme-engineering.md"):
        assert f"references/{name}" in novel, f"novel-writing SKILL.md 未登记 {name}"
    for name in ("scene-engineering.md", "revision-diagnosis.md"):
        assert f"references/{name}" in script, f"script-writing SKILL.md 未登记 {name}"


def test_no_copyright_copy_markers():
    """原理层文件不得出现"照录/原文如下/引用原文"等整段引用痕迹。"""
    banned = ("原文如下", "全文如下", "照录如下")
    for rel in FILES:
        text = _read(rel)
        for word in banned:
            assert word not in text, f"{rel} 出现整段引用痕迹 {word}"


def test_cross_reference_hook_mechanics_to_library():
    """钩子机制篇必须显式声明与 hook-library 的互补关系（原理层↔招式层）。"""
    text = _read("novel-writing/references/hook-mechanics.md")
    assert "hook-library" in text
