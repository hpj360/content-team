"""R42：推荐执行包（命中审计 + 中式公版补缺 + 新赛道失败库）契约测试。"""
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

CLASSICS = {
    "deconstruction-dou-e-yuan.md": (["窦娥冤", "三桩誓愿"], "DE-T"),
    "deconstruction-mudanting.md": (["牡丹亭", "生死双段"], "MT-T"),
    "deconstruction-honglou-meng.md": (["判词", "草蛇灰线"], "HL-T"),
}
FAILURE_LIBS = {
    "failure-vertical-drama.md": ["V-F1", "V-F10"],
    "failure-ai-drama.md": ["AI-F1", "AI-F10"],
}
AUDIT = CORPUS_DIR / "corpus-coverage-audit.md"


def _read(name: str) -> str:
    return (CORPUS_DIR / name).read_text(encoding="utf-8")


def test_classics_wellformed():
    for filename, (keywords, prefix) in CLASSICS.items():
        text = _read(filename)
        assert text.lstrip().startswith("# "), f"{filename} 缺标题"
        assert len(text) > 2000, f"{filename} 内容过短（戏曲/档案拆解应有深度）"
        # 纪律用语：语料文件可用"不复制/不整段照录/不拆解/不拆…"等价表述
        assert (
            "不复制" in text or "不整段照录" in text or "不拆" in text
        ), f"{filename} 纪律缺失"
        assert "可迁移" in text, f"{filename} 缺可迁移"
        assert "2026-11-08" in text and "content_freshness" in text
        for keyword in keywords:
            assert keyword in text, f"{filename} 缺锚点 {keyword}"
        for i in range(1, 7):
            assert f"{prefix}{i}" in text, f"{filename} 缺技法 {prefix}{i}"


def test_failure_libs_structure():
    for filename, (first, last) in FAILURE_LIBS.items():
        text = _read(filename)
        assert text.lstrip().startswith("# ")
        assert first in text and last in text, f"{filename} 缺条目"
        assert "症状" in text and "修复" in text, f"{filename} 缺症状→修复结构"
        assert "content_freshness" in text
        # 条目数：F 编码出现次数 ≥10
        codes = re.findall(r"[VAI]{1,2}-F\d+", text)
        assert len(codes) >= 12, f"{filename} 条目引用不足"


def test_failure_libs_forbidden_words():
    """失败库正文禁词：打脸/外卖员 零出现；"短剧"仅允许出现在"微短剧"复合词内。"""
    for filename in FAILURE_LIBS:
        text = _read(filename)
        assert "打脸" not in text, f"{filename} 出现禁词 打脸"
        assert "外卖员" not in text, f"{filename} 出现禁词 外卖员"
        standalone = re.sub(r"微短剧", "", text)
        assert "短剧" not in standalone, f"{filename} 出现独立'短剧'（仅允许'微短剧'复合词）"


def test_classics_no_forbidden_words():
    for filename in CLASSICS:
        text = _read(filename)
        for word in ("打脸", "外卖员"):
            assert word not in text, f"{filename} 出现禁词 {word}"


def test_classics_registered():
    for case_id in ("dou-e-yuan", "mudanting", "honglou-meng"):
        case = get_case(case_id)
        assert case is not None, f"index.json 缺 {case_id}"
        assert case.genres and case.tags and case.summary
        assert (CORPUS_DIR / case.file).is_file()
        assert "2026-11-08" not in case.author  # 校准日在文件内，登记字段保持简洁
    with_plan = {c.id for c in find_cases() if c.foreshadowing_plan}
    assert "honglou-meng" in with_plan


def test_narrow_gate_post_patch():
    """审计补丁后窄门（corpus_refs_for top-2/top-4）的可达性验证。"""
    # 补丁前零命中的缝合案例，补丁后应可达
    assert corpus_refs_for("综艺 任务 游戏 翻盘", limit=4)
    assert any(
        c.id == "paradigm-variety-show" for c in find_cases(genre="综艺")
    )


def test_waimai_top2_contract_unchanged():
    assert "shortdrama-waimai-example" in corpus_refs_for("复仇打脸 都市 短剧 外卖员")


def test_audit_file_exists_with_real_numbers():
    text = AUDIT.read_text(encoding="utf-8")
    assert text.lstrip().startswith("# ")
    assert "44" in text and "47" in text, "审计应含真实模拟规模"
    for section in ("窄门", "宽门", "死键", "短别名", "补丁后复测"):
        assert section in text, f"审计缺章节 {section}"
    assert "corpus_refs_for" in text and "search_knowledge" in text


def test_readme_updated():
    readme = (CORPUS_DIR / "README.md").read_text(encoding="utf-8")
    for filename in [*CLASSICS, *FAILURE_LIBS, "corpus-coverage-audit.md"]:
        assert filename in readme, f"README 缺 {filename}"
    assert "同 IP 多文件不重复" in readme or "分工声明" in readme
