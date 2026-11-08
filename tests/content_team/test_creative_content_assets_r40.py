"""R40：用户点名双拆（黑神话：悟空 / 反相之地）契约测试。"""
from __future__ import annotations

import re
from pathlib import Path

from hermes.content_team.creative.corpus import (
    CORPUS_DIR,
    find_cases,
    get_case,
    corpus_refs_for,
)

_ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "breakdown-black-myth-wukong.md": {
        "prefix": "WM-T",
        "keywords": ["黑神话", "火照黑云", "未竟", "影神图"],
    },
    "breakdown-fanxiangzhidi.md": {
        "prefix": "FX-T",
        "keywords": ["反相之地", "规则怪谈", "藤蔓", "AI"],
    },
}

FORBIDDEN = ("打脸", "外卖员", "短剧")


def _read(name: str) -> str:
    return (CORPUS_DIR / name).read_text(encoding="utf-8")


def test_files_wellformed_and_disciplined():
    for filename in FILES:
        text = _read(filename)
        assert text.lstrip().startswith("# "), f"{filename} 缺标题"
        assert len(text) > 2000, f"{filename} 内容过短"
        assert "版权声明" in text, f"{filename} 缺版权声明"
        assert (
            "不复制" in text or "不拆解" in text or "不引用" in text
        ), f"{filename} 版权纪律缺失"
        assert "可迁移" in text, f"{filename} 缺可迁移"
        assert "2026-11-04" in text and "content_freshness" in text


def test_techniques_referenced():
    for filename, spec in FILES.items():
        text = _read(filename)
        prefix = spec["prefix"]
        refs = re.findall(rf"{prefix}\d", text)
        assert len(refs) >= 6, f"{filename} {prefix} 引用不足 6 处"
    # 黑神话六章节名（公开事实口径）必须入表
    wukong = _read("breakdown-black-myth-wukong.md")
    for chapter in ("风起黄昏", "夜生白露", "曲度紫鸳", "日落红尘"):
        assert chapter in wukong, f"缺章节名 {chapter}"


def test_fanxiang_rules_and_beats():
    text = _read("breakdown-fanxiangzhidi.md")
    assert "规则" in text and "钩子" in text
    assert "一致性" in text  # AI 生产管线拆解
    # 引用分级纪律：不允许出现长段台词（以 80 字符无标点长引作粗检）
    assert not re.search(r"[「“][^」”]{80,}[」”]", text), "疑似长引用"


def test_no_forbidden_words():
    for filename in FILES:
        text = _read(filename)
        for word in FORBIDDEN:
            assert word not in text, f"{filename} 出现禁词 {word}"


def test_cases_registered_no_forbidden_fields():
    for case_id in ("breakdown-black-myth-wukong", "breakdown-fanxiangzhidi"):
        case = get_case(case_id)
        assert case is not None, f"index.json 缺 {case_id}"
        assert case.genres and case.tags and case.summary
        assert (CORPUS_DIR / case.file).is_file()
        blob = case.title + "|" + case.summary + "|" + "|".join(case.tags) + "|" + "|".join(case.genres)
        for word in FORBIDDEN:
            assert word not in blob, f"{case_id} 登记字段出现禁词 {word}"
    assert {
        "breakdown-black-myth-wukong", "breakdown-fanxiangzhidi"
    } <= {c.id for c in find_cases(form="beat-breakdown")}


def test_waimai_top2_contract_unchanged():
    assert "shortdrama-waimai-example" in corpus_refs_for("复仇打脸 都市 短剧 外卖员")


def test_readme_rows_registered():
    readme = (CORPUS_DIR / "README.md").read_text(encoding="utf-8")
    for filename in FILES:
        assert filename in readme, f"README 缺 {filename}"


# ---------------------------------------------------------------------------
# R40·补：影神图档案级拆解（breakdown-blackmyth-yingshentu.md，本会话补录）
# ---------------------------------------------------------------------------

_YINGSHENTU = "breakdown-blackmyth-yingshentu.md"

SAMPLE_ENTRIES = ["狼斥候", "广智", "黄风大圣", "灵吉菩萨"]
Y_TECHNICS = [f"Y-T{i}" for i in range(1, 9)]


def test_yingshentu_file_wellformed_and_disciplined():
    text = _read(_YINGSHENTU)
    assert text.lstrip().startswith("# "), "缺标题"
    assert len(text) > 2000, "内容过短"
    assert "版权声明" in text and "不复制" in text, "版权纪律缺失"
    assert "可迁移" in text, "缺可迁移"
    assert "2026-11-04" in text and "content_freshness" in text, "缺校准/复审口径"


def test_yingshentu_sample_entries_and_techniques():
    text = _read(_YINGSHENTU)
    for entry in SAMPLE_ENTRIES:
        assert entry in text, f"缺样条 {entry}"
    assert text.count("摘要") >= 4, "样条缺机制摘要段"
    for code in Y_TECHNICS:
        assert code in text, f"缺技法 {code}"


def test_yingshentu_rashomon_cross_ref():
    text = _read(_YINGSHENTU)
    assert "akutagawa-rashomon" in text, "缺罗生门条目交叉引用"
    assert "五名相关者" in text or "五层叙述距离" in text, "五视角机制段缺失"


def test_yingshentu_registered():
    case = get_case("breakdown-blackmyth-yingshentu")
    assert case is not None, "index.json 缺条目"
    assert case.form == "archive-breakdown"
    assert (CORPUS_DIR / case.file).is_file()
    blob = case.title + "|" + case.summary + "|" + "|".join(case.tags) + "|" + "|".join(case.genres)
    for word in FORBIDDEN:
        assert word not in blob, f"登记字段出现禁词 {word}"
    with_plan = {c.id for c in find_cases() if c.foreshadowing_plan}
    assert "breakdown-blackmyth-yingshentu" in with_plan


def test_yingshentu_readme_row():
    readme = (CORPUS_DIR / "README.md").read_text(encoding="utf-8")
    assert _YINGSHENTU in readme
