"""R34：热梗/核心台词/名场面沉淀 测试（hot-quotes-memes.md 契约）。"""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_QUOTES = _ROOT / "knowledge" / "corpus" / "hot-quotes-memes.md"

REQUIRED_ANCHORS = ["后会友期", "再见爱人", "狂飙", "繁花", "哪吒", "盛夏芬德拉", "甄嬛传", "浪浪山"]
REQUIRED_MEMES = ["鸭舌文学", "熏鸡事变", "老默", "风浪越大", "派头", "我命由我不由天",
                  "逃离浪浪山", "短剧细糠", "玫瑰窃贼", "十亿俱乐部"]


def test_quotes_file_wellformed():
    text = _QUOTES.read_text(encoding="utf-8")
    assert text.lstrip().startswith("# "), "缺少标题"
    assert len(text) > 2000, "内容过短"
    assert "2026-11-04" in text, "缺校准日期"
    assert "content_freshness" in text, "缺时效复审提示"


def test_quotes_discipline_header():
    """引用分级纪律必须存在：L1/L2 允许、L3 禁止、生成链路不得直接挪用。"""
    text = _QUOTES.read_text(encoding="utf-8")
    assert "L1" in text and "L2" in text and "禁止" in text
    assert "机制迁移" in text, "必须声明'机制迁移而非语句照搬'的用法"
    assert "本地文档" in text, "必须写明成段素材的本地文档替代路径"
    for anchor in REQUIRED_ANCHORS:
        assert anchor in text, f"缺锚点 {anchor}"


def test_quotes_entries_have_mechanism_and_source():
    """每个条目表必须含'出处 / 传播机制 / 复用点'列。"""
    text = _QUOTES.read_text(encoding="utf-8")
    for column in ("出处", "传播机制", "复用点"):
        assert f"| {column}" in text, f"条目表缺列 {column}"


def test_quotes_cover_current_hot_memes():
    text = _QUOTES.read_text(encoding="utf-8")
    for meme in REQUIRED_MEMES:
        assert meme in text, f"缺核心梗 {meme}"


def test_quotes_referenced_in_corpus_readme():
    readme = (_ROOT / "knowledge" / "corpus" / "README.md").read_text(encoding="utf-8")
    assert "hot-quotes-memes.md" in readme
