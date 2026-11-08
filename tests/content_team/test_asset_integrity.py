"""资产整合防漂移测试（asset-map 全量覆盖 + 边界声明 + 索引一致性）。"""
from __future__ import annotations

import json
import re
from pathlib import Path

from hermes.content_team.creative.templates import BUILTIN_TEMPLATES

_ROOT = Path(__file__).resolve().parents[2]
_SKILLS = _ROOT / "skills"
_CORPUS = _ROOT / "knowledge" / "corpus"
_ASSET_MAP = (_ROOT / "knowledge" / "asset-map.md").read_text(encoding="utf-8")

CREATIVE_SKILLS = ["novel-writing", "script-writing", "showrunning", "directing", "storyboarding"]


def test_asset_map_covers_all_creative_references():
    """asset-map 必须提及全部创作技能 references 文件名（新增文件须同步登记）。"""
    missing = []
    for skill in CREATIVE_SKILLS:
        for ref in sorted((_SKILLS / skill / "references").glob("*.md")):
            if ref.stem not in _ASSET_MAP:
                missing.append(f"{skill}/{ref.name}")
    assert missing == [], f"asset-map 缺 references: {missing[:8]}（共 {len(missing)} 份）"


def test_asset_map_covers_all_builtin_templates():
    missing = [t.id for t in BUILTIN_TEMPLATES if t.id not in _ASSET_MAP]
    assert missing == [], f"asset-map 缺模板 id: {missing}"


def test_asset_map_has_failure_code_families():
    for family in ("F1–F10", "SB1–SB8", "N-FAIL", "V-F1", "AI-F1", "ST/SC/SE"):
        assert family in _ASSET_MAP, f"asset-map 缺失败编码族 {family}"


def test_style_pack_library_count_matches():
    """style-pack-library 头部声明的风格包数必须与正文实际条目一致。"""
    text = (_SKILLS / "directing" / "references" / "style-pack-library.md").read_text(encoding="utf-8")
    header = text[:600]
    m = re.search(r"再补\s*(\d+)\s*个", header)
    if not m:
        m = re.search(r"(\d+)\s*个类型化风格包", header)
    actual = len(re.findall(r"^##\s+\d+", text, flags=re.MULTILINE))
    if m:
        declared = int(m.group(1))
        assert declared == actual, f"style-pack-library 头部声明 {declared} 个，正文实际 {actual} 个"
    else:
        assert actual > 0, "style-pack-library 未解析到风格包条目"


def test_root_readme_links_asset_map():
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    assert "asset-map" in readme, "根 README 未链接 asset-map"
    for target in ("creative-methodology-overview", "usage-writing-with-content-team", "corpus/README"):
        assert target in readme, f"根 README 未链接 {target}"


def test_corpus_readme_tool_count_matches():
    """corpus README 的'工具文档'计数必须与实际非案例文档数一致。"""
    readme = (_CORPUS / "README.md").read_text(encoding="utf-8")
    data = json.loads((_CORPUS / "index.json").read_text(encoding="utf-8"))
    case_files = {c["file"] for c in data["cases"]}
    tool_docs = [
        p.name for p in _CORPUS.glob("*.md")
        if p.name != "README.md" and p.name not in case_files
    ]
    m = re.search(r"索引与工具文档（(\d+)", readme)
    assert m, "corpus README 缺'索引与工具文档（N'计数"
    assert int(m.group(1)) == len(tool_docs), (
        f"README 声明 {m.group(1)} 份工具文档，实际 {len(tool_docs)} 份：{sorted(tool_docs)}"
    )


def test_top_documents_declare_positioning():
    """六份顶层文档须声明定位/受众/权威口径（边界清晰化）。"""
    docs = [
        "creative-methodology-overview.md",
        "usage-writing-with-content-team.md",
        "method-distillation-log.md",
        "creative-quality-model.md",
        "creative-tuning-report.md",
        "material-intake.md",
    ]
    for name in docs:
        text = (_ROOT / "knowledge" / name).read_text(encoding="utf-8")
        head = text[:1200]
        assert ("定位" in head or "权威口径" in head or "权威" in head), (
            f"{name} 头部未声明定位/权威"
        )


def test_same_ip_boundaries_declared():
    """同 IP 多文件必须在文件头声明分工（审计发现的关键缺口）。"""
    checks = {
        "deconstruction-chapter-form-wukong.md": "breakdown-blackmyth-yingshentu",
        "paradigm-game-narrative.md": "breakdown-blackmyth-yingshentu",
        "breakdown-black-myth-wukong.md": "paradigm-game-narrative",
        "breakdown-blackmyth-yingshentu.md": "paradigm-game-narrative",
        "paradigm-vertical-interactive.md": "paradigm-paid-short-drama",
        "deconstruction-wilde-earnest.md": "paradigm-modern-romance",
        "deconstruction-comedy-sketch.md": "paradigm-sketch-competition",
    }
    for filename, target in checks.items():
        text = (_CORPUS / filename).read_text(encoding="utf-8")
        head = text[:2500]
        assert target in head, f"{filename} 头部未声明与 {target} 的分工"


def test_failure_index_in_failure_corpus():
    text = (_CORPUS / "failure-corpus.md").read_text(encoding="utf-8")
    head = text[:3000]
    for code in ("F1–F10", "SB1–SB8", "V-F1", "AI-F1", "ST/SC/SE"):
        assert code in head, f"failure-corpus 顶部缺编码映射 {code}"


def test_template_descriptions_have_boundaries():
    by_id = {t.id: t for t in BUILTIN_TEMPLATES}
    assert "90 秒" in by_id["short-drama-episode-8beat"].description or "90" in by_id[
        "short-drama-episode-8beat"].description
    assert "120" in by_id["vertical-two-minute-episode"].description
    assert "16:9" in by_id["storyboard-dialogue-scene"].description
    assert "9:16" in by_id["storyboard-vertical-scene"].description
    assert "配合" in by_id["scene-detail-expansion"].description
    assert "配合" in by_id["emotion-curve-card"].description
