"""R37：喜剧双赛道语料（素描竞赛工程 / 单口竞技工程）契约测试。"""
from __future__ import annotations

from pathlib import Path

from hermes.content_team.creative.corpus import (
    CORPUS_DIR,
    find_cases,
    foreshadowing_plan_for,
    get_case,
    corpus_refs_for,
)

_ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "paradigm-sketch-competition.md": (["互联网体检", "少爷和我"], "S-T"),
    "paradigm-standup-competition.md": (["脱口秀大会", "杨笠"], "U-T"),
}

SKETCH_CASES = ["互联网体检", "少爷和我", "小品的世界", "八十一难", "大侠别动手"]
STANDUP_TALENTS = ["杨笠", "王建国", "李雪琴", "王勉", "呼兰", "周奇墨"]


def test_files_wellformed_and_disciplined():
    for filename, _payload in FILES.items():
        text = (CORPUS_DIR / filename).read_text(encoding="utf-8")
        assert text.lstrip().startswith("# "), f"{filename} 缺标题"
        assert len(text) > 1500, f"{filename} 内容过短"
        assert "版权声明" in text and "不复制" in text, f"{filename} 版权纪律缺失"
        assert "可迁移" in text, f"{filename} 缺可迁移"
        assert "2026-11-04" in text and "content_freshness" in text, f"{filename} 缺校准/复审口径"


def test_six_dimensions_and_techniques():
    for filename, (_keywords, prefix) in FILES.items():
        text = (CORPUS_DIR / filename).read_text(encoding="utf-8")
        for dim in ("核心命题", "叙事结构", "台词", "热梗", "可迁移"):
            assert dim in text, f"{filename} 缺维度 {dim}"
        for i in range(1, 9):
            assert f"{prefix}{i}" in text, f"{filename} 缺技法 {prefix}{i}"


def test_sketch_file_has_per_work_breakdowns():
    text = (CORPUS_DIR / "paradigm-sketch-competition.md").read_text(encoding="utf-8")
    assert "逐案四段拆解" in text
    for work in SKETCH_CASES:
        assert work in text, f"缺逐案拆解 {work}"
    assert text.count("结构骨架") >= 5 and text.count("热梗与复用") >= 5


def test_standup_file_has_per_talent_breakdowns():
    text = (CORPUS_DIR / "paradigm-standup-competition.md").read_text(encoding="utf-8")
    assert "逐案拆解" in text
    for name in STANDUP_TALENTS:
        assert name in text, f"缺人设拆解 {name}"
    assert text.count("人设货币") >= 6 and text.count("复用点") >= 6


def test_cases_indexed_with_dimensions_and_plans():
    for case_id in ("paradigm-sketch-competition", "paradigm-standup-competition"):
        case = get_case(case_id)
        assert case is not None, f"index.json 缺 {case_id}"
        assert case_genres_ok(case), f"{case_id} 维度不全"
    with_plan = {c.id for c in find_cases() if c.foreshadowing_plan}
    assert {"paradigm-sketch-competition", "paradigm-standup-competition"} <= with_plan


def case_genres_ok(case) -> bool:
    return bool(case.genres) and bool(case.tags) and bool(case.summary)


def test_find_by_form_and_waimai_contract():
    ids = {c.id for c in find_cases(form="comedy-competition")}
    assert {"paradigm-sketch-competition", "paradigm-standup-competition"} <= ids
    assert "shortdrama-waimai-example" in corpus_refs_for("复仇打脸 都市 短剧 外卖员")


def test_foreshadowing_plans_loadable():
    plans = foreshadowing_plan_for("喜剧 综艺 脱口秀", limit=4)
    sources = {p["source_case"] for p in plans}
    assert {"paradigm-sketch-competition", "paradigm-standup-competition"} <= sources


def test_readme_rows_registered():
    readme = (CORPUS_DIR / "README.md").read_text(encoding="utf-8")
    for filename, _payload in FILES.items():
        assert filename in readme, f"README 缺 {filename}"


def test_no_forbidden_words():
    for filename, _payload in FILES.items():
        text = (CORPUS_DIR / filename).read_text(encoding="utf-8")
        for word in ("打脸", "外卖员"):
            assert word not in text, f"{filename} 出现禁词 {word}"
