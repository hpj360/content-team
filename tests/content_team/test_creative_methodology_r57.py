"""R57：语料→方法论蒸馏（母题/喜剧/群像多线工程）契约测试。"""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_NOVEL = _ROOT / "skills" / "novel-writing" / "references"
_SCRIPT = _ROOT / "skills" / "script-writing" / "references"

FILES = {
    _NOVEL / "plot-device-engineering.md": (
        "母题工程", ["母题卡片", "悬念延迟", "反转", "双重身份", "语料源", "蒸馏源"]),
    _SCRIPT / "comedy-engineering.md": (
        "喜剧工程", ["Setup", "三拍装载", "笑点五型", "排布纪律", "喜悲", "蒸馏源"]),
    _NOVEL / "ensemble-engineering.md": (
        "群像多线工程", ["线型", "线架构", "合流", "群像管理", "信息公平", "蒸馏源"]),
}


def test_distilled_files_wellformed():
    for path, (title, concepts) in FILES.items():
        assert path.is_file(), f"{path.name} 未创建"
        text = path.read_text(encoding="utf-8")
        assert text.lstrip().startswith("# "), f"{path.name} 缺标题"
        assert title in text, f"{path.name} 标题缺 {title}"
        assert len(text) > 5000, f"{path.name} 内容偏薄"
        for concept in concepts:
            assert concept in text, f"{path.name} 缺 {concept}"
        for section in ("反模式", "自检", "局限"):
            assert section in text, f"{path.name} 缺 {section}"
        assert "corpus" in text, f"{path.name} 未标注语料蒸馏源"


def test_no_forbidden_words():
    for path, _payload in FILES.items():
        text = path.read_text(encoding="utf-8")
        for word in ("打脸", "外卖员"):
            assert word not in text, f"{path.name} 出现禁词 {word}"


def test_distillations_registered():
    amap = (_ROOT / "knowledge" / "asset-map.md").read_text(encoding="utf-8")
    for path, _payload in FILES.items():
        stem = path.stem
        assert stem in amap, f"asset-map 缺 {stem}"
    assert "novel-writing（22）" in amap, "asset-map novel 计数应为 22"
    assert "script-writing（14）" in amap, "asset-map script 计数应为 14"
    canon = (_ROOT / "knowledge" / "methodology-canon.md").read_text(encoding="utf-8")
    for key in ("母题/叙事装置", "喜剧三拍装载", "多线合流/群像"):
        assert key in canon, f"正典概念权威表缺 {key}"


def test_skill_md_registered():
    skill_n = (_ROOT / "skills" / "novel-writing" / "SKILL.md").read_text(encoding="utf-8")
    assert "plot-device-engineering" in skill_n and "ensemble-engineering" in skill_n
    skill_s = (_ROOT / "skills" / "script-writing" / "SKILL.md").read_text(encoding="utf-8")
    assert "comedy-engineering" in skill_s
