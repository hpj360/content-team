"""R31：内容资产沉淀与拓展 测试（storyboarding references / 语料范式 ×5 / 总纲 / 模板）。"""
from __future__ import annotations

import re
from pathlib import Path

from hermes.content_team.creative.corpus import (
    CORPUS_DIR,
    find_cases,
    foreshadowing_plan_for,
    get_case,
)
from hermes.content_team.creative.knowledge_base import build_knowledge_index
from hermes.content_team.creative.templates import get_template, list_templates, render_template

_ROOT = Path(__file__).resolve().parents[2]
_SKILL_MD = _ROOT / "skills" / "storyboarding" / "SKILL.md"

NEW_REFS = [
    "references/vertical-shot-grammar.md",
    "references/edit-rhythm-and-transition.md",
    "references/storyboard-failure-casebook.md",
    "references/ai-video-storyboard-prompting.md",
]

NEW_CORPUS_CASES = [
    ("paradigm-modern-romance", "paradigm-modern-romance.md"),
    ("paradigm-urban-business", "paradigm-urban-business.md"),
    ("paradigm-variety-show", "paradigm-variety-show.md"),
    ("paradigm-animation-series", "paradigm-animation-series.md"),
    ("paradigm-vertical-interactive", "paradigm-vertical-interactive.md"),
]

NEW_TEMPLATE_IDS = [
    "romance-misunderstanding-engine",
    "vertical-two-minute-episode",
    "animation-unit-episode",
    "storyboard-vertical-scene",
]


# ---------------------------------------------------------------------------
# 分镜技能：references 对称补齐
# ---------------------------------------------------------------------------


def test_storyboarding_new_references_exist_and_linked():
    text = _SKILL_MD.read_text(encoding="utf-8")
    links = set(re.findall(r"references/[\w\-./]+\.md", text))
    for ref in NEW_REFS:
        path = _ROOT / "skills" / "storyboarding" / ref
        assert path.is_file(), f"缺少分镜新 references：{ref}"
        assert ref in links, f"SKILL.md 未登记 {ref}"


def test_storyboarding_new_references_wellformed():
    for ref in NEW_REFS:
        content = (_ROOT / "skills" / "storyboarding" / ref).read_text(encoding="utf-8")
        assert content.lstrip().startswith("#"), f"{ref} 缺少标题"
        assert len(content) > 300, f"{ref} 内容过短"


def test_storyboarding_failure_casebook_covers_sb8():
    content = (_ROOT / "skills" / "storyboarding" / "references"
               / "storyboard-failure-casebook.md").read_text(encoding="utf-8")
    for code in (f"SB{i}" for i in range(1, 9)):
        assert code in content, f"分镜失败手册缺少 {code}"


# ---------------------------------------------------------------------------
# 语料库：题材范式 ×5
# ---------------------------------------------------------------------------


def test_new_corpus_cases_indexed_with_files():
    for case_id, filename in NEW_CORPUS_CASES:
        case = get_case(case_id)
        assert case is not None, f"index.json 缺少 {case_id}"
        assert (CORPUS_DIR / filename).is_file(), f"{case_id} 文件缺失"
        assert case.genres and case.tags and case.summary


def test_new_corpus_paradigm_files_wellformed_and_original():
    for case_id, filename in NEW_CORPUS_CASES:
        path = CORPUS_DIR / filename
        text = path.read_text(encoding="utf-8")
        assert text.lstrip().startswith("#"), f"{filename} 缺少标题"
        assert len(text) > 500, f"{filename} 内容过短"
        # 范式分析文件的版权纪律
        assert "版权声明" in text, f"{filename} 缺少版权声明"
        assert "不复制" in text, f"{filename} 缺少'不复制'声明"
        assert "可迁移" in text, f"{filename} 缺少可迁移结论"


def test_new_corpus_genre_hits():
    assert any(c.id == "paradigm-modern-romance" for c in find_cases(genre="言情"))
    assert any(c.id == "paradigm-urban-business" for c in find_cases(genre="商战"))
    assert any(c.id == "paradigm-variety-show" for c in find_cases(genre="综艺"))
    assert any(c.id == "paradigm-animation-series" for c in find_cases(genre="动画"))
    assert any(c.id == "paradigm-vertical-interactive" for c in find_cases(genre="互动"))


def test_new_corpus_does_not_displace_waimai_refs():
    """既有契约：外卖员示例仍需在 top-2 命中中不被新案例挤出。"""
    from hermes.content_team.creative.corpus import corpus_refs_for

    assert "shortdrama-waimai-example" in corpus_refs_for("复仇打脸 都市 短剧 外卖员")


def test_new_corpus_foreshadowing_plans_loadable():
    plans = foreshadowing_plan_for("误会 引擎 言情 互动 竖屏")
    assert plans, "新案例伏笔计划未命中"
    assert all("source_case" in p and p["content"] for p in plans)


# ---------------------------------------------------------------------------
# 方法论总纲
# ---------------------------------------------------------------------------


def test_methodology_overview_exists():
    path = _ROOT / "knowledge" / "creative-methodology-overview.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# "), "总纲缺少标题"
    for section in ("施压——递进——回收", "五大手艺支柱", "写前→写中→写后", "失败模式的元模式"):
        assert section in text, f"总纲缺少章节：{section}"


def test_overview_registered_in_knowledge_index():
    entries = build_knowledge_index()
    assert any(
        e.category == "knowledge" and "creative-methodology-overview" in e.path
        for e in entries
    )


# ---------------------------------------------------------------------------
# 模板库
# ---------------------------------------------------------------------------


def test_new_templates_registered():
    all_ids = {t.id for t in list_templates()}
    for template_id in NEW_TEMPLATE_IDS:
        assert template_id in all_ids, f"模板 {template_id} 未注册"


def test_new_templates_render_with_variables():
    cases = {
        "romance-misunderstanding-engine": {"书名": "心动信号", "主角A": "A", "主角B": "B",
                                            "核心误解": "误会", "戳破时机": "第三章"},
        "vertical-two-minute-episode": {"集数": "1", "本集危机": "被拆穿", "反转点": "身份",
                                        "结尾钩子": "下一集"},
        "animation-unit-episode": {"集数": "1", "单元任务": "送信", "主线递进": "发现地图",
                                   "记忆点": "口头禅", "留主线钩": "塔亮了"},
        "storyboard-vertical-scene": {"场次": "1-2", "地点": "天台", "人物A": "阿男",
                                      "人物B": "阿女"},
    }
    for template_id, variables in cases.items():
        rendered = render_template(template_id, variables)
        assert rendered is not None
        for key in variables:
            assert "{" + key + "}" not in rendered, f"{template_id} 变量 {key} 未替换"


def test_storyboard_template_respects_shot_duration_gate():
    """竖屏分镜模板的单镜时长必须落在既有硬门 2–5s 内，且总和=各镜之和。"""
    template = get_template("storyboard-vertical-scene")
    assert template is not None
    durations = [float(m) for m in re.findall(r"([\d.]+)s ", template.body)]
    assert durations and all(2.0 <= d <= 5.0 for d in durations)
