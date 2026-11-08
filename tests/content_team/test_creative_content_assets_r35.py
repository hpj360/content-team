"""R35：导演方法论五件套 测试（六维拆解 + 登记 + 语料协同）。"""
from __future__ import annotations

import json
from pathlib import Path

from hermes.content_team.creative.corpus import find_cases, get_case, corpus_refs_for

_ROOT = Path(__file__).resolve().parents[2]
_CORPUS = _ROOT / "knowledge" / "corpus"

DIRECTORS = {
    "paradigm-director-hitchcock.md": ["希区柯克", "MacGuffin"],
    "paradigm-director-wongkarwai.md": ["王家卫", "花样年华"],
    "paradigm-director-kurosawa.md": ["黑泽明", "七武士"],
    "paradigm-director-tarantino.md": ["昆汀", "低俗小说"],
    "paradigm-director-nolan.md": ["诺兰", "盗梦空间"],
}

# 用户点名的六维：每维都必须在文件中有独立小节
DIMENSIONS = ["核心命题", "叙事结构", "分镜", "台词", "热梗", "可迁移"]


def test_director_files_exist_and_wellformed():
    for filename, _keywords in DIRECTORS.items():
        path = _CORPUS / filename
        text = path.read_text(encoding="utf-8")
        assert text.lstrip().startswith("# "), f"{filename} 缺标题"
        assert len(text) > 1500, f"{filename} 内容过短"
        assert "版权声明" in text and "不复制" in text, f"{filename} 版权纪律缺失"
        assert "可迁移" in text, f"{filename} 缺可迁移结论"


def test_director_files_cover_six_dimensions():
    for filename, _keywords in DIRECTORS.items():
        text = (_CORPUS / filename).read_text(encoding="utf-8")
        for dim in DIMENSIONS:
            assert dim in text, f"{filename} 缺维度 {dim}"


def test_director_files_have_transferable_techniques():
    """每份文件至少 6 条编号可迁移技法（T1…T6 + 专属前缀）。"""
    prefixes = {"hitchcock": "H-T", "wongkarwai": "W-T", "kurosawa": "K-T",
                "tarantino": "Q-T", "nolan": "N-T"}
    for filename in DIRECTORS:
        stem = filename.removesuffix(".md").removeprefix("paradigm-director-")
        prefix = prefixes[stem]
        text = (_CORPUS / filename).read_text(encoding="utf-8")
        for i in range(1, 7):
            assert f"{prefix}{i}" in text, f"{filename} 缺技法 {prefix}{i}"


def test_director_cases_indexed():
    data = json.loads((_CORPUS / "index.json").read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in data["cases"] if c["id"].startswith("paradigm-director-")}
    assert set(by_id) == {
        "paradigm-director-hitchcock", "paradigm-director-wongkarwai",
        "paradigm-director-kurosawa", "paradigm-director-tarantino",
        "paradigm-director-nolan",
    }
    for case_id, (filename, keywords) in _zip_items():
        case = by_id[case_id]
        assert case["file"] == filename
        assert case["form"] == "director-paradigm"
        assert "参考《" in case["author"], f"{case_id} author 未登记锚点"
        for keyword in keywords:
            assert keyword in case["author"], f"{case_id} author 缺 {keyword}"
        assert case["genres"] and case["tags"] and case["summary"]


def _zip_items():
    yield from (
        ("paradigm-director-hitchcock", ("paradigm-director-hitchcock.md", ["惊魂记", "后窗"])),
        ("paradigm-director-wongkarwai", ("paradigm-director-wongkarwai.md", ["花样年华"])),
        ("paradigm-director-kurosawa", ("paradigm-director-kurosawa.md", ["罗生门", "七武士"])),
        ("paradigm-director-tarantino", ("paradigm-director-tarantino.md", ["低俗小说"])),
        ("paradigm-director-nolan", ("paradigm-director-nolan.md", ["记忆碎片", "盗梦空间"])),
    )


def test_director_cases_findable_by_form():
    by_form = {c.id for c in find_cases(form="director-paradigm")}
    assert by_form == {
        "paradigm-director-hitchcock", "paradigm-director-wongkarwai",
        "paradigm-director-kurosawa", "paradigm-director-tarantino",
        "paradigm-director-nolan",
    }


def test_director_semantic_hits_and_contract_unchanged():
    assert get_case("paradigm-director-hitchcock") is not None
    # 既有契约不受影响
    assert "shortdrama-waimai-example" in corpus_refs_for("复仇打脸 都市 短剧 外卖员")


def test_wongkarwai_links_romance_paradigm():
    text = (_CORPUS / "paradigm-director-wongkarwai.md").read_text(encoding="utf-8")
    assert "误会引擎" in text or "modern-romance" in text
