"""R50：六拍事件链 + 细节具体化阶梯 契约测试。"""
from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_REFS = _REPO / "skills" / "novel-writing" / "references"


def _read(name: str) -> str:
    return (_REFS / name).read_text(encoding="utf-8")


def test_event_conflict_arc_wellformed():
    text = _read("event-conflict-arc.md")
    assert text.lstrip().startswith("# ")
    assert len(text) > 6000, "六拍事件链内容偏薄"
    for beat in ("失衡", "困难", "尝试", "失败", "再试", "假胜", "真胜"):
        assert beat in text, f"缺拍位概念 {beat}"
    for concept in ("三账", "新信息", "新策略", "假胜三形态", "真胜三条检验", "对账"):
        assert concept in text, f"缺核心机制 {concept}"
    assert "局限" in text and "自检" in text


def test_event_conflict_arc_maps_to_beat_sheets():
    text = _read("event-conflict-arc.md")
    for target in ("beat-sheets", "scene-engineering", "emotion-conflict-externalization", "story-state"):
        assert target in text, f"缺与 {target} 的分工/对账"


def test_scene_detail_has_concreteness_ladder():
    text = _read("scene-detail-engineering.md")
    assert "具体化阶梯" in text, "缺具体化阶梯章节"
    for concept in ("档1", "档2", "档3", "档4", "感官复合", "名词具体化", "动词具体化"):
        assert concept in text, f"缺具体化概念 {concept}"
    assert "具体化 ≠ 堆砌" in text or "具体化 ≠" in text, "缺'具体化≠堆砌'节"
    # 20 组对照表：数该表的行数
    sem = re.search(r"20 组.*?对照", text)
    assert sem, "缺 20 组对照表标题"


def test_scene_detail_concreteness_examples_count():
    text = _read("scene-detail-engineering.md")
    # 10.6 节内的对照表应有 ≥20 数据行
    m = re.search(r"### 10\.6.*?(?=\n### |\n## )", text, flags=re.S)
    assert m, "未找到 10.6 对照表节"
    rows = [ln for ln in m.group(0).splitlines() if ln.strip().startswith("|") and "---" not in ln]
    assert len(rows) >= 21, f"对照表数据行不足 20（含表头共 {len(rows)} 行）"


def test_skill_md_registers_new_reference():
    skill = (_REPO / "skills" / "novel-writing" / "SKILL.md").read_text(encoding="utf-8")
    assert "references/event-conflict-arc.md" in skill


def test_canon_and_asset_map_updated():
    canon = (_REPO / "knowledge" / "methodology-canon.md").read_text(encoding="utf-8")
    assert "event-conflict-arc" in canon, "正典未登记六拍事件链"
    amap = (_REPO / "knowledge" / "asset-map.md").read_text(encoding="utf-8")
    assert "event-conflict-arc" in amap, "asset-map 未登记六拍事件链"
