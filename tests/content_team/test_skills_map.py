"""R51：技能总图与资产归属 完整性测试。"""
from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_MAP = (_ROOT / "skills" / "README.md").read_text(encoding="utf-8")
_ASSET_MAP = (_ROOT / "knowledge" / "asset-map.md").read_text(encoding="utf-8")


def test_skills_map_exists_and_wellformed():
    assert _MAP.lstrip().startswith("# ")
    assert len(_MAP) > 3000, "技能总图内容过薄"


def test_skills_map_covers_all_registered_skills():
    manifest = json.loads((_ROOT / "manifest.json").read_text(encoding="utf-8"))
    missing = [name for name in manifest["skills"] if name not in _MAP]
    assert missing == [], f"技能总图缺已注册技能: {missing}"


def test_skills_map_covers_scoped_skills():
    skills_dir = _ROOT / "skills"
    scoped = []
    for ns in sorted(p for p in skills_dir.iterdir() if p.is_dir() and p.name.startswith("@")):
        scoped += [sub.name for sub in ns.iterdir() if sub.is_dir()]
    assert len(scoped) >= 6, "未发现 @scope 技能目录"
    missing = [name for name in scoped if name not in _MAP]
    assert missing == [], f"技能总图缺外部 scope 技能: {missing}"


def test_skills_map_has_creative_chain_and_boundaries():
    for keyword in ("创作链", "横切统筹", "边界速查", "Related skills"):
        assert keyword in _MAP, f"技能总图缺 {keyword}"
    for skill in ("novel-writing", "script-writing", "storyboarding", "directing", "showrunning"):
        assert skill in _MAP, f"技能总图缺创作技能 {skill}"


def test_skills_map_has_search_selection_rules():
    for tool in ("brave-search", "tavily-search", "research", "agent-browser", "summarize"):
        assert tool in _MAP, f"技能总图缺检索技能 {tool}"
    assert "选型规则" in _MAP, "缺检索技能选型规则"


def test_asset_map_links_skills_map():
    assert "skills/README.md" in _ASSET_MAP, "asset-map 未链接技能总图"


def test_asset_map_covers_all_knowledge_docs():
    """knowledge/ 顶层全部 md（除 INDEX）必须在 asset-map 中有归属。"""
    docs = sorted(p.name for p in (_ROOT / "knowledge").glob("*.md") if p.name != "INDEX.md")
    missing = [name for name in docs if name not in _ASSET_MAP]
    assert missing == [], f"asset-map 未归属的知识文档: {missing}"


def test_skills_map_not_discovered_as_skill():
    """skills/README.md 是目录说明，不应被技能发现器当作技能。"""
    from hermes.skills import discover_skills

    names = {info.name for info in discover_skills()}
    assert "README" not in names and "readme" not in names


def test_skills_map_mentions_archive_policy():
    assert "_archive" in _MAP, "技能总图缺归档策略说明"
