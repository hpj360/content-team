"""R39：新赛道×三 + 单案全拆×四 契约测试。"""
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

PARADIGMS = {
    "paradigm-paid-short-drama.md": (["盛夏芬德拉", "十亿俱乐部"], "R-T"),
    "paradigm-narrative-podcast.md": (["秒时刻", "悬崖钩"], "POD-T"),
    "paradigm-game-narrative.md": (["影神图", "黑神话"], "G-T"),
}
BREAKDOWNS = {
    "breakdown-internet-health-check.md": (["互联网体检"], "S-T"),
    "breakdown-inception.md": (["盗梦空间"], "BI-T"),
    "breakdown-kuangbiao-arc.md": (["狂飙", "黑化"], "KB-T"),
    "breakdown-rear-window.md": (["后窗"], "RW-T"),
}


def _read(filename: str) -> str:
    return (CORPUS_DIR / filename).read_text(encoding="utf-8")


def test_files_wellformed_and_disciplined():
    for filename in [*PARADIGMS, *BREAKDOWNS]:
        text = _read(filename)
        assert text.lstrip().startswith("# "), f"{filename} 缺标题"
        assert len(text) > 2000, f"{filename} 内容过短"
        assert "版权声明" in text, f"{filename} 缺版权声明"
        # 纪律用语：语料文件用"不复制"，拆解/播客文件可用"不拆解/不引用"等价表述
        assert (
            "不复制" in text or "不拆解" in text or "不引用" in text
        ), f"{filename} 版权纪律缺失"
        assert "可迁移" in text, f"{filename} 缺可迁移"
        assert "2026-11-04" in text and "content_freshness" in text, (
            f"{filename} 缺校准/复审口径"
        )


def test_paradigms_mechanisms_and_techniques():
    for filename, (keywords, prefix) in PARADIGMS.items():
        text = _read(filename)
        for keyword in keywords:
            assert keyword in text, f"{filename} 缺锚点/机制 {keyword}"
        for i in range(1, 9):
            assert f"{prefix}{i}" in text, f"{filename} 缺技法 {prefix}{i}"


def test_breakdown_tables_and_techniques():
    # 全拆文件的技法允许复用上游范式编号（如体检全拆复用 S 系），不做连续编号要求
    for filename, (keywords, prefix) in BREAKDOWNS.items():
        text = _read(filename)
        for keyword in keywords:
            assert keyword in text, f"{filename} 缺锚点 {keyword}"
        assert "可迁移" in text
        refs = re.findall(rf"{prefix}\d", text)
        assert len(refs) >= 6, f"{filename} 技法引用不足 6 处（{len(refs)}）"


def test_breakdown_specific_structures():
    health = _read("breakdown-internet-health-check.md")
    assert "逐拍" in health or "拍 " in health
    assert "388" in health or "360" in health  # 公开报道口径的数字锚
    inception = _read("breakdown-inception.md")
    assert "规则卡" in inception and "同步锚" in inception
    kuangbiao = _read("breakdown-kuangbiao-arc.md")
    assert "三幕" in kuangbiao and "黑化" in kuangbiao
    rear = _read("breakdown-rear-window.md")
    assert "POV" in rear and "窗" in rear


def test_cases_registered_with_forms():
    for case_id in (
        "paradigm-paid-short-drama", "paradigm-narrative-podcast",
        "paradigm-game-narrative", "breakdown-internet-health-check",
        "breakdown-inception", "breakdown-kuangbiao-arc", "breakdown-rear-window",
    ):
        case = get_case(case_id)
        assert case is not None, f"index.json 缺 {case_id}"
        assert case.genres and case.tags and case.summary, f"{case_id} 维度不全"
        assert (CORPUS_DIR / case.file).is_file(), f"{case_id} 文件缺失"
    breakdown_ids = {c.id for c in find_cases(form="beat-breakdown")}
    assert {
        "breakdown-internet-health-check", "breakdown-inception",
        "breakdown-kuangbiao-arc", "breakdown-rear-window",
    } <= breakdown_ids


def test_waimai_top2_contract_unchanged():
    assert "shortdrama-waimai-example" in corpus_refs_for("复仇打脸 都市 短剧 外卖员")


def test_readme_rows_registered():
    readme = (CORPUS_DIR / "README.md").read_text(encoding="utf-8")
    for filename in [*PARADIGMS, *BREAKDOWNS]:
        assert filename in readme, f"README 缺 {filename}"


def test_no_forbidden_words():
    for filename in [*PARADIGMS, *BREAKDOWNS]:
        text = _read(filename)
        for word in ("打脸", "外卖员"):
            assert word not in text, f"{filename} 出现禁词 {word}"
