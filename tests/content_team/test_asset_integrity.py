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


# ---------------------------------------------------------------------------
# R47：项目工作法蒸馏（44 号四维细节 → references；工作区文件挂"已蒸馏"横幅）
# ---------------------------------------------------------------------------

NOVEL_DIR = _ROOT / "content-creation" / "novel"


def test_scene_detail_has_project_formulas():
    """scene-detail-engineering 须含项目实训公式（三拍/三账/环境参与/配比/句式）。"""
    text = (_SKILLS / "novel-writing/references/scene-detail-engineering.md").read_text(encoding="utf-8")
    for concept in ("动作三拍", "影响三账", "环境＝参与动作", "注意偏移", "闪回", "35%", "可套用句式"):
        assert concept in text, f"scene-detail-engineering 缺蒸馏公式 {concept}"


def test_emotion_file_has_conflict_layers_and_arc():
    """emotion-conflict-externalization 须含冲突四层与情感三段式。"""
    text = (_SKILLS / "novel-writing/references/emotion-conflict-externalization.md").read_text(encoding="utf-8")
    for concept in ("表层", "利益层", "价值层", "自我层", "引信", "三段式", "泪点写小"):
        assert concept in text, f"emotion-conflict-externalization 缺蒸馏概念 {concept}"


def test_novel_method_files_have_distilled_banner():
    """项目工作区 7 份方法文件须挂'已蒸馏'横幅（防止两套方法分叉）。"""
    files = [
        "16-章节体量标准V3.md", "22-场景连续性工作法.md", "23-叙述连贯性工作法.md",
        "24-勘察组规则体系.md", "25-理解成本优化-规则的呈现改造.md",
        "27-写作方法落地-章节修订日志.md",
        "44-吞兽维修师-写作手法优化-四维细节系统.md",
    ]
    for name in files:
        path = NOVEL_DIR / name
        assert path.is_file(), f"缺项目工作法 {name}"
        head = path.read_text(encoding="utf-8")[:800]
        assert "已蒸馏" in head, f"{name} 缺'已蒸馏'横幅"


def test_novel_asset_overview_has_mapping_table():
    text = (NOVEL_DIR / "00-资产总览.md").read_text(encoding="utf-8")
    assert "方法资产 ↔ 仓库 references 映射" in text, "00-资产总览 缺方法映射表"
    for target in ("chapter-continuity", "rule-horror-techniques",
                   "scene-detail-engineering", "emotion-conflict-externalization"):
        assert target in text, f"映射表缺 {target}"


# ---------------------------------------------------------------------------
# R48：方法论正典（跨文件去重合订）
# ---------------------------------------------------------------------------

_CANON = (_ROOT / "knowledge" / "methodology-canon.md").read_text(encoding="utf-8")


def test_canon_has_six_layers_and_thirteen_principles():
    assert "六层操作系统" in _CANON
    for i in range(1, 14):
        assert f"P{i} " in _CANON, f"正典缺原理 P{i}"


def test_canon_has_authority_numeric_and_antipattern_tables():
    for key in ("概念权威表", "数值口径总表", "反模式总表", "gates.py", "分档"):
        assert key in _CANON, f"正典缺 {key}"
    for concept in ("拍位/时长", "平台数值", "误会引擎", "失败编码", "风格包", "一致性锚点"):
        assert concept in _CANON, f"概念权威表缺 {concept}"


def test_style_packs_respect_shot_gate():
    """ASL 数值必须落在单镜硬门 2–5s 内（审计发现 6.0/5.5 超门已修）。"""
    for name in ("director-style-params.md", "style-pack-library.md"):
        text = (_SKILLS / "directing" / "references" / name).read_text(encoding="utf-8")
        vals = [float(v) for v in re.findall(r"avg_shot_length_s:\s*([\d.]+)", text)]
        assert vals, f"{name} 未解析到 avg_shot_length_s"
        bad = [v for v in vals if not (2.0 <= v <= 5.0)]
        assert bad == [], f"{name} 存在超门 ASL: {bad}"


def test_failure_casebook_code_claim_consistent():
    text = (_SKILLS / "directing" / "references" / "failure-casebook.md").read_text(encoding="utf-8")
    assert "F1–F10" in text, "failure-casebook 未标注实际编码范围"
    assert "F1–F19" not in text, "failure-casebook 仍含过时 F1–F19 声明"


def test_shot_patterns_declares_segment_boundary():
    text = (_SKILLS / "storyboarding" / "references" / "shot-patterns.md").read_text(encoding="utf-8")
    head = text[:800]
    assert "拆为 2 段" in head or "段 ≤15s" in head, "shot-patterns 未声明段长边界"
