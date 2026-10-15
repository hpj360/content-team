"""R28：知识库索引与检索 测试。"""
from __future__ import annotations

from pathlib import Path

from hermes.content_team.creative.knowledge_base import (
    KnowledgeEntry,
    build_knowledge_index,
    render_index_markdown,
    search_knowledge,
)

_ROOT = Path(__file__).resolve().parents[2]


def test_index_covers_all_categories():
    entries = build_knowledge_index()
    categories = {e.category for e in entries}
    assert categories == {"skill", "skill-reference", "corpus", "knowledge", "template"}
    assert len(entries) >= 100


def test_every_entry_path_is_valid():
    for entry in build_knowledge_index():
        if entry.category == "template":
            assert entry.path.startswith("GET /api/templates/")
            continue
        assert (_ROOT / entry.path).exists(), f"路径不存在: {entry.path}"


def test_skill_entries_and_references_have_skill_name():
    entries = build_knowledge_index()
    skills = [e for e in entries if e.category == "skill"]
    refs = [e for e in entries if e.category == "skill-reference"]
    assert any(e.skill == "novel-writing" for e in skills)
    # 本项目 5 技能都有 references
    for skill in ("novel-writing", "script-writing", "storyboarding",
                  "directing", "showrunning"):
        assert any(e.skill == skill for e in refs), f"{skill} 无 reference 条目"
    # scoped 技能也被收录
    assert any(e.skill.startswith("@") for e in skills)


def test_corpus_cases_not_duplicated_by_doc_entries():
    entries = build_knowledge_index()
    corpus_paths = [e.path for e in entries if e.category == "corpus"]
    assert len(corpus_paths) == len(set(corpus_paths))


def test_search_by_title_and_tag_and_category():
    by_title = search_knowledge("钩子", limit=5)
    assert by_title and any("钩子" in r["title"] for r in by_title)

    by_tag = search_knowledge("剧本杀", limit=5)
    assert any("剧本杀" in r["title"] for r in by_tag)

    filtered = search_knowledge("钩子", category="skill-reference", limit=5)
    assert all(r["category"] == "skill-reference" for r in filtered)

    assert search_knowledge("") == []
    assert search_knowledge("绝不存在的词xyz") == []


def test_search_scores_descending():
    results = search_knowledge("平台", limit=10)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_render_index_markdown_structure():
    md = render_index_markdown()
    assert md.startswith("# 知识库总目录")
    for label in ("创作技能", "技能方法论", "语料案例", "知识沉淀", "写作模板"):
        assert f"## {label}" in md
    assert "| **合计** |" in md
    # 与条目数一致
    assert str(len(build_knowledge_index())) in md


def test_render_index_markdown_accepts_entries():
    md = render_index_markdown(
        [KnowledgeEntry(id="x", category="skill", title="测试技能", path="skills/x/SKILL.md")]
    )
    assert "测试技能" in md and "skills/x/SKILL.md" in md


def test_committed_index_matches_generator():
    """仓库内 knowledge/INDEX.md 与生成器输出一致（防手改漂移）。"""
    committed = (_ROOT / "knowledge" / "INDEX.md").read_text(encoding="utf-8")
    assert committed.strip() == render_index_markdown().strip()


async def test_knowledge_api(client):
    resp = await client.get("/api/knowledge")
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) >= 100
    assert {"id", "category", "title", "path"} <= set(entries[0])

    filtered = await client.get("/api/knowledge", params={"category": "corpus"})
    assert all(e["category"] == "corpus" for e in filtered.json())

    search = await client.get("/api/knowledge/search", params={"q": "钩子"})
    assert search.status_code == 200
    assert search.json()["matched"] >= 1

    md = await client.get("/api/knowledge/index")
    assert md.status_code == 200
    assert "text/markdown" in md.headers["content-type"]
    assert "# 知识库总目录" in md.text
