"""知识库索引与检索（R28）。

把散落在仓库各处的知识资产统一为**可检索索引**：
- `skills/<name>/SKILL.md` 与 `skills/<name>/references/*.md`（创作方法论）
- `knowledge/**/*.md`（质量模型/调优报告/语料库/ADR 沉淀）
- `knowledge/corpus/index.json`（结构化案例，带题材与技法标签）
- `creative/templates.py`（可渲染写作模板）

能力：
- ``build_knowledge_index()`` 扫描并产出 ``KnowledgeEntry`` 列表；
- ``search_knowledge(q)`` 中文友好的关键词打分检索（标题/标签/摘要/路径）；
- ``render_index_markdown()`` 生成人可读总目录（`knowledge/INDEX.md`）。
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_FRONTMATTER_DESC_RE = re.compile(
    r'^description:\s*"?(.*?)"?\s*$', re.MULTILINE
)

# 排除项（归档技能、生成目录、自索引）
_SKILL_EXCLUDE = {"_archive"}
_KNOWLEDGE_EXCLUDE = {"INDEX.md"}

_CATEGORY_LABELS = {
    "skill": "创作技能",
    "skill-reference": "技能方法论（references）",
    "corpus": "语料案例",
    "knowledge": "知识沉淀",
    "template": "写作模板",
}


@dataclass
class KnowledgeEntry:
    """知识资产条目。"""

    id: str
    category: str
    title: str
    path: str
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    skill: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def project_root() -> Path:
    return _PROJECT_ROOT


def _filename_tokens(path: Path) -> list[str]:
    stem = path.stem.lower()
    tokens = [t for t in re.split(r"[-_\s]+", stem) if t]
    return tokens


def _first_h1(text: str, fallback: str) -> str:
    match = _H1_RE.search(text)
    return match.group(1).strip() if match else fallback


def _frontmatter_description(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    block = text[: end if end > 0 else len(text)]
    match = _FRONTMATTER_DESC_RE.search(block)
    return match.group(1).strip() if match else ""


def _first_paragraph(text: str, limit: int = 160) -> str:
    """取首个正文段落（跳过标题、引用、代码块、列表）。"""
    in_fence = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line:
            continue
        if line.startswith(("#", ">", "-", "*", "|", "---")):
            continue
        return line[:limit]
    return ""


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _iter_skill_dirs(skills_dir: Path):
    """遍历技能目录，产出 (技能名, 目录)。支持 `@namespace/name` 形式。"""
    for entry in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        if entry.name in _SKILL_EXCLUDE:
            continue
        if entry.name.startswith("@"):
            for sub in sorted(p for p in entry.iterdir() if p.is_dir()):
                yield f"{entry.name}/{sub.name}", sub
        else:
            yield entry.name, entry


def _skill_entries(root: Path) -> list[KnowledgeEntry]:
    entries: list[KnowledgeEntry] = []
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return entries
    for skill_name, skill_dir in _iter_skill_dirs(skills_dir):
        skill_md = skill_dir / "SKILL.md"
        if skill_md.is_file():
            text = _read(skill_md)
            entries.append(
                KnowledgeEntry(
                    id=f"skill:{skill_name}",
                    category="skill",
                    title=_first_h1(text, skill_name),
                    path=str(skill_md.relative_to(root)).replace("\\", "/"),
                    summary=_frontmatter_description(text)
                    or _first_paragraph(text),
                    tags=[skill_name, *_filename_tokens(Path(skill_name))],
                    skill=skill_name,
                )
            )
        refs_dir = skill_dir / "references"
        if refs_dir.is_dir():
            for ref in sorted(refs_dir.glob("*.md")):
                text = _read(ref)
                entries.append(
                    KnowledgeEntry(
                        id=f"skill-ref:{skill_name}/{ref.stem}",
                        category="skill-reference",
                        title=_first_h1(text, ref.stem),
                        path=str(ref.relative_to(root)).replace("\\", "/"),
                        summary=_first_paragraph(text),
                        tags=[skill_name, *_filename_tokens(ref)],
                        skill=skill_name,
                    )
                )
    return entries


def _knowledge_entries(root: Path) -> list[KnowledgeEntry]:
    entries: list[KnowledgeEntry] = []
    knowledge_dir = root / "knowledge"
    if not knowledge_dir.is_dir():
        return entries
    # 已被 corpus/index.json 登记为案例的文件不重复收录
    indexed_corpus = {
        f"knowledge/corpus/{case['file']}"
        for case in _raw_corpus_cases(root)
        if case.get("file")
    }
    for doc in sorted(knowledge_dir.rglob("*.md")):
        if doc.name in _KNOWLEDGE_EXCLUDE:
            continue
        rel = doc.relative_to(knowledge_dir)
        rel_posix = str(doc.relative_to(root)).replace("\\", "/")
        if rel_posix in indexed_corpus:
            continue
        text = _read(doc)
        parts = rel.parts
        category = "corpus" if parts and parts[0] == "corpus" else "knowledge"
        entries.append(
            KnowledgeEntry(
                id=f"{category}:{rel.as_posix()}",
                category=category,
                title=_first_h1(text, doc.stem),
                path=rel_posix,
                summary=_first_paragraph(text),
                tags=[*parts[:-1], *_filename_tokens(doc)],
            )
        )
    return entries


def _raw_corpus_cases(root: Path) -> list[dict[str, Any]]:
    index_path = root / "knowledge" / "corpus" / "index.json"
    if not index_path.is_file():
        return []
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return [c for c in data.get("cases") or [] if isinstance(c, dict)]


def _corpus_case_entries(root: Path) -> list[KnowledgeEntry]:
    entries: list[KnowledgeEntry] = []
    for case in _raw_corpus_cases(root):
        if not case.get("id"):
            continue
        entries.append(
            KnowledgeEntry(
                id=f"corpus-case:{case['id']}",
                category="corpus",
                title=str(case.get("title") or case["id"]),
                path=f"knowledge/corpus/{case.get('file') or ''}",
                summary=str(case.get("summary") or ""),
                tags=[str(t) for t in case.get("tags") or []]
                + [str(g) for g in case.get("genres") or []],
            )
        )
    return entries


def _template_entries() -> list[KnowledgeEntry]:
    try:
        from hermes.content_team.creative.templates import list_templates
    except Exception:  # noqa: BLE001
        return []
    entries: list[KnowledgeEntry] = []
    for template in list_templates():
        entries.append(
            KnowledgeEntry(
                id=f"template:{template.id}",
                category="template",
                title=template.name,
                path=f"GET /api/templates/{template.id}",
                summary=template.description,
                tags=[template.category, *template.variables],
            )
        )
    return entries


def build_knowledge_index(root: Path | None = None) -> list[KnowledgeEntry]:
    """扫描并返回全部知识资产条目（按类别与标题排序）。"""
    base = root or _PROJECT_ROOT
    entries = [
        *_skill_entries(base),
        *_knowledge_entries(base),
        *_corpus_case_entries(base),
        *_template_entries(),
    ]
    order = {
        "skill": 0,
        "skill-reference": 1,
        "corpus": 2,
        "knowledge": 3,
        "template": 4,
    }
    entries.sort(key=lambda e: (order.get(e.category, 9), e.title))
    return entries


# ---------------------------------------------------------------------------
# 检索（中文友好的关键词打分）
# ---------------------------------------------------------------------------


def _score(entry: KnowledgeEntry, terms: list[str], raw_query: str) -> int:
    title = entry.title.lower()
    summary = entry.summary.lower()
    path = entry.path.lower()
    tags = " ".join(entry.tags).lower()
    score = 0
    if raw_query.lower() in title:
        score += 4
    for term in terms:
        if term in title:
            score += 3
        if term in tags:
            score += 2
        if term in summary:
            score += 1
        if term in path:
            score += 1
    return score


def search_knowledge(
    query: str,
    *,
    category: str | None = None,
    limit: int = 10,
    root: Path | None = None,
) -> list[dict[str, Any]]:
    """按关键词检索知识资产，返回按相关度排序的条目（含 score）。"""
    query = (query or "").strip()
    if not query:
        return []
    terms = [t.lower() for t in re.split(r"\s+", query) if t]
    results: list[tuple[int, KnowledgeEntry]] = []
    for entry in build_knowledge_index(root):
        if category and entry.category != category:
            continue
        score = _score(entry, terms, query)
        if score > 0:
            results.append((score, entry))
    results.sort(key=lambda item: (-item[0], item[1].title))
    return [{**entry.to_dict(), "score": score} for score, entry in results[:limit]]


# ---------------------------------------------------------------------------
# 目录渲染
# ---------------------------------------------------------------------------


def render_index_markdown(
    entries: list[KnowledgeEntry] | None = None,
) -> str:
    """生成人可读的知识库总目录（Markdown）。"""
    items = entries if entries is not None else build_knowledge_index()
    lines = [
        "# 知识库总目录（INDEX）",
        "",
        "> 由 `creative/knowledge_base.py` 生成；检索用 `GET /api/knowledge/search?q=`。",
        "",
    ]
    by_category: dict[str, list[KnowledgeEntry]] = {}
    for entry in items:
        by_category.setdefault(entry.category, []).append(entry)

    lines.append("## 统计")
    lines.append("")
    lines.append("| 类别 | 数量 |")
    lines.append("|---|---|")
    for category in _CATEGORY_LABELS:
        if category in by_category:
            lines.append(f"| {_CATEGORY_LABELS[category]} | {len(by_category[category])} |")
    lines.append(f"| **合计** | **{len(items)}** |")
    lines.append("")

    for category, label in _CATEGORY_LABELS.items():
        group = by_category.get(category)
        if not group:
            continue
        lines.append(f"## {label}")
        lines.append("")
        for entry in group:
            tags = f" · `{'、'.join(entry.tags[:4])}`" if entry.tags else ""
            lines.append(f"- **{entry.title}** — `{entry.path}`{tags}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
