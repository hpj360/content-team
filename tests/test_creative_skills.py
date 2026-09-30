"""创作方向 skill 质量校验。

覆盖 novel-writing / script-writing / storyboarding / directing / showrunning：
- frontmatter（name 与目录一致、description 有效且含中文触发词）
- 结构（标题、角色、边界声明、方法论参考）
- references 目录与链接完整性
- manifest.json 注册
- 单文件行数上限（<500）
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from hermes.skills import discover_skills, parse_skill_frontmatter

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
MANIFEST_PATH = REPO_ROOT / "manifest.json"

CREATIVE_SKILLS = [
    "novel-writing",
    "script-writing",
    "storyboarding",
    "directing",
    "showrunning",
]

REF_LINK_RE = re.compile(r"references/[\w\-./]+\.md")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _skill_text(name: str) -> str:
    return (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", CREATIVE_SKILLS)
def test_skill_dir_and_md_exist(name: str) -> None:
    assert (SKILLS_DIR / name).is_dir(), f"{name} 目录不存在"
    assert (SKILLS_DIR / name / "SKILL.md").is_file()


@pytest.mark.parametrize("name", CREATIVE_SKILLS)
def test_no_bom_and_utf8(name: str) -> None:
    raw = (SKILLS_DIR / name / "SKILL.md").read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "SKILL.md 不应带 BOM"
    raw.decode("utf-8")  # 不抛异常即可


@pytest.mark.parametrize("name", CREATIVE_SKILLS)
def test_frontmatter_name_matches_dir(name: str) -> None:
    fm = parse_skill_frontmatter(SKILLS_DIR / name / "SKILL.md")
    assert fm.get("name") == name


@pytest.mark.parametrize("name", CREATIVE_SKILLS)
def test_description_valid_with_chinese(name: str) -> None:
    fm = parse_skill_frontmatter(SKILLS_DIR / name / "SKILL.md")
    desc = fm.get("description", "")
    assert isinstance(desc, str) and len(desc.strip()) > 20
    assert len(desc) <= 1024, "description 不得超过 1024 字符"
    assert CJK_RE.search(desc), "description 需含中文触发词"


@pytest.mark.parametrize("name", CREATIVE_SKILLS)
def test_required_sections(name: str) -> None:
    text = _skill_text(name)
    assert text.startswith("---")
    assert re.search(r"^#\s+\S", text, re.MULTILINE), "缺少 H1 标题"
    assert "## 角色" in text
    assert "## Related skills" in text
    assert "## 方法论参考" in text


@pytest.mark.parametrize("name", CREATIVE_SKILLS)
def test_boundary_mentions_sibling(name: str) -> None:
    text = _skill_text(name)
    boundary = text.split("## Related skills", 1)[1]
    others = [s for s in CREATIVE_SKILLS if s != name]
    assert any(s in boundary for s in others), "边界声明需点名至少一个同族 skill"


@pytest.mark.parametrize("name", CREATIVE_SKILLS)
def test_line_count_reasonable(name: str) -> None:
    lines = _skill_text(name).splitlines()
    assert len(lines) <= 500, f"SKILL.md 过长（{len(lines)} 行），应拆分到 references/"


@pytest.mark.parametrize("name", CREATIVE_SKILLS)
def test_references_present_and_linked(name: str) -> None:
    refs_dir = SKILLS_DIR / name / "references"
    assert refs_dir.is_dir(), f"{name}/references 不存在"
    ref_files = sorted(p.name for p in refs_dir.glob("*.md"))
    assert ref_files, f"{name}/references 下无 markdown"

    text = _skill_text(name)
    links = REF_LINK_RE.findall(text)
    assert links, "SKILL.md 未引用任何 references 文件"
    for link in links:
        assert (SKILLS_DIR / name / link).is_file(), f"引用缺失：{link}"


@pytest.mark.parametrize("name", CREATIVE_SKILLS)
def test_reference_files_wellformed(name: str) -> None:
    refs_dir = SKILLS_DIR / name / "references"
    for ref in sorted(refs_dir.glob("*.md")):
        content = ref.read_text(encoding="utf-8")
        assert content.lstrip().startswith("#"), f"{ref.name} 缺少标题"
        assert len(content) > 300, f"{ref.name} 内容过短"


@pytest.mark.parametrize("name", CREATIVE_SKILLS)
def test_manifest_registers_skill(name: str, manifest: dict) -> None:
    assert name in manifest.get("skills", [])


@pytest.mark.parametrize("name", CREATIVE_SKILLS)
def test_discoverable(name: str) -> None:
    names = {info.name for info in discover_skills()}
    assert name in names
