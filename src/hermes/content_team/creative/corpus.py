"""语料库索引（R19 续）：让拆解案例可被规划器/模板按题材与技法引用。

- 索引：``knowledge/corpus/index.json``（案例 id/题材/技法标签）；
- 供 beat-sheet planner 在 SCRIPT 阶段给出 ``corpus_refs``，随 plan 记入
  ``CreationRun.stage_results[].plan``，实现"拆解结论被引用"而非躺在文档里。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
CORPUS_DIR = _PROJECT_ROOT / "knowledge" / "corpus"
INDEX_PATH = CORPUS_DIR / "index.json"


@dataclass
class CorpusCase:
    """语料案例条目。"""

    id: str
    title: str
    author: str
    form: str
    genres: list[str]
    tags: list[str]
    summary: str
    file: str
    foreshadowing_plan: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_corpus_index(path: Path | None = None) -> list[CorpusCase]:
    """载入语料库索引（缺失或损坏时返回空列表，不抛错）。"""
    target = path or INDEX_PATH
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    cases = []
    for item in data.get("cases") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        cases.append(
            CorpusCase(
                id=str(item.get("id")),
                title=str(item.get("title") or ""),
                author=str(item.get("author") or ""),
                form=str(item.get("form") or ""),
                genres=[str(g) for g in item.get("genres") or []],
                tags=[str(t) for t in item.get("tags") or []],
                summary=str(item.get("summary") or ""),
                file=str(item.get("file") or ""),
                foreshadowing_plan=[
                    dict(p)
                    for p in item.get("foreshadowing_plan") or []
                    if isinstance(p, dict)
                ],
            )
        )
    return cases


def find_cases(
    *,
    genre: str | None = None,
    tag: str | None = None,
    form: str | None = None,
    limit: int | None = None,
    path: Path | None = None,
) -> list[CorpusCase]:
    """按题材/技法标签/形态筛选案例。"""
    results = []
    for case in load_corpus_index(path):
        if genre and genre not in case.genres:
            continue
        if tag and tag not in case.tags:
            continue
        if form and form != case.form:
            continue
        results.append(case)
    return results[:limit] if limit else results


def corpus_refs_for(text: str, *, limit: int = 2, path: Path | None = None) -> list[str]:
    """按文本（标题/描述/题材）命中的题材与标签，返回最相关的案例 id 列表。"""
    if not text:
        return []
    scored: list[tuple[int, str]] = []
    for case in load_corpus_index(path):
        score = 0
        for keyword in [*case.genres, *case.tags, case.form, case.title]:
            if keyword and keyword in text:
                score += 1
        if score:
            scored.append((score, case.id))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [case_id for _score, case_id in scored[:limit]]


def get_case(case_id: str, path: Path | None = None) -> CorpusCase | None:
    for case in load_corpus_index(path):
        if case.id == case_id:
            return case
    return None


def corpus_payload_for(
    text: str, *, ids: list[str] | None = None, path: Path | None = None
) -> list[dict[str, Any]]:
    """返回用于注入生成 prompt 的语料精简负载（摘要 + 技法标签）。"""
    cases = load_corpus_index(path)
    wanted = set(ids) if ids else set(corpus_refs_for(text, path=path))
    payload: list[dict[str, Any]] = []
    for case in cases:
        if case.id not in wanted:
            continue
        payload.append(
            {
                "id": case.id,
                "title": case.title,
                "form": case.form,
                "summary": case.summary,
                "tags": case.tags,
            }
        )
    return payload


def foreshadowing_plan_for(
    text: str, *, limit: int = 3, path: Path | None = None
) -> list[dict[str, Any]]:
    """从命中的语料案例抽取结构化伏笔计划（用于 seed 进 StoryState）。"""
    wanted = set(corpus_refs_for(text, limit=limit, path=path))
    plan: list[dict[str, Any]] = []
    seen: set[str] = set()
    for case in load_corpus_index(path):
        if case.id not in wanted:
            continue
        for item in case.foreshadowing_plan:
            content = str(item.get("content") or "")
            if not content or content in seen:
                continue
            seen.add(content)
            plan.append({**item, "source_case": case.id})
    return plan


def reconcile_foreshadowing(
    plan: list[dict[str, Any]], state_items: list[dict[str, Any]]
) -> dict[str, Any]:
    """语料伏笔计划 ↔ StoryState.foreshadowing 对账。

    - ``matched``：计划项在状态卡中找到（按 keyword 或 content 匹配）
    - ``missing``：计划有、状态卡无（应 seed 或补登记）
    - ``unplanned``：状态卡有、计划无（作者自加，非错误）
    """
    state_keys = set()
    for item in state_items or []:
        for key in ("keyword", "content"):
            value = str(item.get(key) or "").strip()
            if value:
                state_keys.add(value)
    matched: list[str] = []
    missing: list[str] = []
    for item in plan or []:
        key = str(item.get("keyword") or item.get("content") or "").strip()
        (matched if key in state_keys else missing).append(key or "(空)")
    planned_keys = {
        str(item.get("keyword") or item.get("content") or "").strip()
        for item in plan or []
    }
    unplanned = [
        str(item.get("id") or item.get("content") or "")
        for item in state_items or []
        if str(item.get("keyword") or item.get("content") or "").strip()
        not in planned_keys
    ]
    return {
        "matched": matched,
        "missing": missing,
        "unplanned": unplanned,
        "coverage": (
            round(len(matched) / len(plan), 3) if plan else None
        ),
    }
