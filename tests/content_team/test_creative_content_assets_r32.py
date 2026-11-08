"""R32：综艺/动画实战工况拆解（原创示例实录级）测试。"""
from __future__ import annotations

from pathlib import Path

from hermes.content_team.creative.corpus import (
    CORPUS_DIR,
    find_cases,
    foreshadowing_plan_for,
    get_case,
)

_ROOT = Path(__file__).resolve().parents[2]

NEW_EXAMPLES = [
    ("example-variety-segment", "example-variety-segment.md", ["信封", "计分板", "X位"]),
    ("example-animation-unit", "example-animation-unit.md", ["灯塔", "腰带", "回执"]),
]


def test_new_example_files_wellformed():
    for case_id, filename, _keywords in NEW_EXAMPLES:
        path = CORPUS_DIR / filename
        text = path.read_text(encoding="utf-8")
        assert text.lstrip().startswith("#"), f"{filename} 缺少标题"
        assert len(text) > 500, f"{filename} 内容过短"
        assert "原创" in text, f"{filename} 未声明原创示例"
        assert "版权声明" in text, f"{filename} 缺少版权声明"
        assert "不复制" in text, f"{filename} 缺少'不复制'声明"
        assert "可迁移" in text, f"{filename} 缺少可迁移结论"


def test_keywords_recur_for_foreshadowing():
    for _case_id, filename, keywords in NEW_EXAMPLES:
        text = (CORPUS_DIR / filename).read_text(encoding="utf-8")
        for word in keywords:
            assert text.count(word) >= 2, f"{filename} 关键词 {word} 出现不足 2 次"


def test_new_examples_indexed_with_dimensions():
    for case_id, filename, _keywords in NEW_EXAMPLES:
        case = get_case(case_id)
        assert case is not None, f"index.json 缺少 {case_id}"
        assert (CORPUS_DIR / filename).is_file(), f"{case_id} 文件缺失"
        assert case.genres and case.tags and case.summary, f"{case_id} 维度不全"
        with_plan = [c for c in find_cases() if c.id == case_id]
        assert with_plan and with_plan[0].foreshadowing_plan, f"{case_id} 缺伏笔计划"


def test_find_cases_by_form():
    variety = find_cases(form="variety-segment")
    assert {c.id for c in variety} == {"example-variety-segment"}
    animation = find_cases(form="animation-episode")
    assert {c.id for c in animation} == {"example-animation-unit"}


def test_foreshadowing_plans_loadable_from_examples():
    # corpus_refs_for 只按案例登记的 genres/tags/form/title 打分，查询词须用字段词
    plans = foreshadowing_plan_for("综艺 任务赛段 动画 单元剧 逐拍实录 双引擎配比", limit=4)
    source_cases = {p["source_case"] for p in plans}
    assert {"example-variety-segment", "example-animation-unit"} <= source_cases


def test_waimai_top2_contract_unchanged():
    from hermes.content_team.creative.corpus import corpus_refs_for

    assert "shortdrama-waimai-example" in corpus_refs_for("复仇打脸 都市 短剧 外卖员")


def test_readme_lists_new_examples():
    readme = (CORPUS_DIR / "README.md").read_text(encoding="utf-8")
    for _case_id, filename, _keywords in NEW_EXAMPLES:
        assert filename in readme, f"README 目录表缺少 {filename}"
