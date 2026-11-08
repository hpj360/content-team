"""R33：语料锚点热门化 测试（范式拆解须挂现象级热门锚点并与登记一致）。"""
from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_CORPUS = _ROOT / "knowledge" / "corpus"

# id -> (锚点关键词列表)  每个关键词必须出现在对应文件正文与 index.json author 中
# 最近校准：2026-11-04（据公开报道热点）
ANCHORS = {
    "paradigm-modern-romance.md": ["后会友期", "玫瑰的故事"],
    "paradigm-urban-business.md": ["繁花", "狂飙"],
    "paradigm-variety-show.md": ["后会友期", "种地吧"],
    "paradigm-animation-series.md": ["哪吒之魔童闹海", "浪浪山小妖怪"],
    "paradigm-vertical-interactive.md": ["盛夏芬德拉"],
}


def test_paradigm_files_have_hot_anchor_section():
    for filename, keywords in ANCHORS.items():
        text = (_CORPUS / filename).read_text(encoding="utf-8")
        assert "热门锚点对照" in text, f"{filename} 缺少热门锚点对照章节"
        for keyword in keywords:
            assert keyword in text, f"{filename} 缺少锚点 {keyword}"
        # 时效纪律与校准日期
        assert "content_freshness" in text, f"{filename} 缺少锚点时效复核提示"
        assert "2026-11-04" in text, f"{filename} 缺少最近校准日期"


def test_paradigm_index_authors_reference_anchors():
    data = json.loads((_CORPUS / "index.json").read_text(encoding="utf-8"))
    authors = {c["id"]: c.get("author", "") for c in data["cases"]}
    for case_id, expected in {
        "paradigm-modern-romance": "后会友期",
        "paradigm-urban-business": "繁花",
        "paradigm-variety-show": "后会友期",
        "paradigm-animation-series": "浪浪山小妖怪",
        "paradigm-vertical-interactive": "盛夏芬德拉",
    }.items():
        assert "参考《" in authors[case_id], f"{case_id} author 未登记锚点"
        assert expected in authors[case_id], f"{case_id} author 锚点不一致"
    assert "复核时效" in data["note"] and "2026-11-04" in data["note"], (
        "index.json note 缺少时效提示与校准日期"
    )


def test_paradigm_readme_rows_reference_anchors():
    readme = (_CORPUS / "README.md").read_text(encoding="utf-8")
    for keyword in ["后会友期", "繁花", "哪吒之魔童闹海", "盛夏芬德拉", "2026-11-04"]:
        assert keyword in readme, f"README 未体现锚点 {keyword}"


def test_copyright_notice_kept_in_reanchored_files():
    """热门化改造后版权声明与'不复制'纪律必须保留。"""
    for filename in ANCHORS:
        text = (_CORPUS / filename).read_text(encoding="utf-8")
        assert "版权声明" in text and "不复制" in text, f"{filename} 版权纪律缺失"


def test_waimai_top2_contract_unchanged():
    from hermes.content_team.creative.corpus import corpus_refs_for

    assert "shortdrama-waimai-example" in corpus_refs_for("复仇打脸 都市 短剧 外卖员")
