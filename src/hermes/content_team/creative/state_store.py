"""故事检索投影：SQLite FTS5 全文检索（小说章节 + 故事状态）。

与 ``hermes.workbench.memory.FTS5Index`` 的差异：workbench 使用 FTS5 默认
unicode61 分词，对中文**整句成词**导致短语查询不命中。本模块在索引与查询
两侧做 **CJK 逐字切分投影**（汉字间插入空格），使任意中文子串可作为短语
精确命中，并保留 BM25 排序。

- 虚拟表 ``story_fts``：``novel_id/source/ref_id UNINDEXED + content``。
- 检索流程：投影查询 → MATCH 短语 → 按 rank 排序 → 回读原文截取上下文窗口。
- 索引来源：``NovelChapter.body``（chapter）/ ``StoryState``（state）/
  伏笔逐条（foreshadowing，keyword 与分镜识别符同词对账）。
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from hermes.content_team.models.creative import (
    Novel,
    NovelChapter,
    StoryState,
)

_CJK_RE = re.compile(r"([\u4e00-\u9fff])")
_MATCH_RE = re.compile(r"([\u4e00-\u9fff]+|[A-Za-z0-9]+)")

# FTS5 虚拟表（幂等创建；unicode61 + 投影空格即可实现中文子串短语匹配）
_DDL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS story_fts USING fts5("
    "novel_id UNINDEXED, source UNINDEXED, ref_id UNINDEXED, content,"
    " tokenize='unicode61')"
)

_CONTEXT_WINDOW = 40


class StoryIndexUnavailable(RuntimeError):
    """当前 SQLite 不支持 FTS5（极少见，嵌入式构建可能裁剪）。"""


def cjk_space(text: str) -> str:
    """CJK 逐字切分投影：汉字前后插入边界空格（拉丁词保持完整）。"""
    projected = _CJK_RE.sub(r" \1 ", text or "")
    return " ".join(projected.split())


def project_query(query: str) -> str:
    """把用户查询转为 FTS5 短语条件（每词一段，多词 AND）。"""
    terms: list[str] = []
    for word in (query or "").split():
        projected = cjk_space(word)
        if projected:
            terms.append(f'"{projected.replace(chr(34), chr(34) * 2)}"')
    return " AND ".join(terms)


def _raw_context(raw: str, query: str, window: int = _CONTEXT_WINDOW) -> str:
    """回读原文，在首个命中词周围截取上下文窗口。"""
    raw = raw or ""
    anchor = -1
    for word in _MATCH_RE.findall(query):
        anchor = raw.find(word)
        if anchor >= 0:
            break
    if anchor < 0:
        return raw[: window * 2]
    start = max(0, anchor - window)
    end = min(len(raw), anchor + len(query) + window)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(raw) else ""
    return f"{prefix}{raw[start:end]}{suffix}"


class StoryIndex:
    """基于请求级 ``AsyncSession`` 的故事检索投影。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _ensure_table(self) -> None:
        try:
            await self.db.execute(sa.text(_DDL))
        except Exception as exc:  # noqa: BLE001
            raise StoryIndexUnavailable(
                f"FTS5 不可用：{exc}"
            ) from exc

    async def reindex(self, novel_id: uuid.UUID) -> int:
        """重建某本小说的投影（先删后插），返回索引行数。"""
        await self._ensure_table()
        await self.db.execute(
            sa.text("DELETE FROM story_fts WHERE novel_id = :nid"),
            {"nid": str(novel_id)},
        )

        rows: list[dict[str, str]] = []

        novel = await self.db.get(Novel, novel_id)
        if novel is None:
            return 0

        chapters = await self.db.execute(
            sa.select(NovelChapter)
            .where(NovelChapter.novel_id == novel_id)
            .order_by(NovelChapter.chapter_number.asc())
        )
        for chapter in chapters.scalars().all():
            rows.append(
                {
                    "source": "chapter",
                    "ref_id": str(chapter.id),
                    "title": f"第{chapter.chapter_number}章 {chapter.title}".strip(),
                    "content": chapter.body or "",
                }
            )

        state_result = await self.db.execute(
            sa.select(StoryState).where(StoryState.novel_id == novel_id)
        )
        state = state_result.scalars().first()
        if state is not None:
            state_text = json.dumps(
                {
                    "tracking": state.tracking,
                    "characters": state.characters,
                    "goals": state.goals,
                },
                ensure_ascii=False,
            )
            rows.append(
                {
                    "source": "state",
                    "ref_id": str(state.id),
                    "title": "故事状态卡",
                    "content": state_text,
                }
            )
            for item in state.foreshadowing or []:
                rows.append(
                    {
                        "source": "foreshadowing",
                        "ref_id": str(item.get("id") or ""),
                        "title": f"伏笔 {item.get('id')}",
                        "content": " ".join(
                            str(item.get(k) or "")
                            for k in (
                                "id",
                                "content",
                                "planted_at",
                                "planned_resolution",
                                "status",
                                "keyword",
                            )
                        ),
                    }
                )

        for row in rows:
            await self.db.execute(
                sa.text(
                    "INSERT INTO story_fts(novel_id, source, ref_id, content) "
                    "VALUES (:nid, :source, :ref_id, :content)"
                ),
                {
                    "nid": str(novel_id),
                    "source": row["source"],
                    "ref_id": row["ref_id"],
                    "content": cjk_space(row["content"]),
                },
            )
        await self.db.commit()
        return len(rows)

    async def search(
        self,
        novel_id: uuid.UUID,
        query: str,
        *,
        limit: int = 5,
        source: str | None = None,
        reindex_first: bool = True,
    ) -> list[dict[str, Any]]:
        """BM25 检索，返回命中片段（回读原文截窗，非投影文本）。"""
        if not (query or "").strip():
            return []
        if reindex_first:
            await self.reindex(novel_id)

        match = project_query(query)
        if not match:
            return []

        sql = (
            "SELECT source, ref_id, content, bm25(story_fts) AS rank "
            "FROM story_fts WHERE story_fts MATCH :match AND novel_id = :nid"
        )
        params: dict[str, Any] = {"match": match, "nid": str(novel_id)}
        if source:
            sql += " AND source = :src"
            params["src"] = source
        sql += " ORDER BY rank LIMIT :lim"
        params["lim"] = limit

        result = await self.db.execute(sa.text(sql), params)
        hits = result.mappings().all()

        raw_by_ref = await self._load_raw(novel_id)
        max_rank = max((abs(h["rank"]) for h in hits), default=1.0) or 1.0

        out: list[dict[str, Any]] = []
        for hit in hits:
            ref_key = (hit["source"], hit["ref_id"])
            raw, title = raw_by_ref.get(ref_key, ("", ""))
            out.append(
                {
                    "source": hit["source"],
                    "ref_id": hit["ref_id"],
                    "title": title,
                    "snippet": _raw_context(raw, query),
                    "score": round(1.0 - abs(hit["rank"]) / max_rank, 3),
                }
            )
        return out

    async def _load_raw(
        self, novel_id: uuid.UUID
    ) -> dict[tuple[str, str], tuple[str, str]]:
        raw: dict[tuple[str, str], tuple[str, str]] = {}
        chapters = await self.db.execute(
            sa.select(NovelChapter).where(NovelChapter.novel_id == novel_id)
        )
        for chapter in chapters.scalars().all():
            raw[("chapter", str(chapter.id))] = (
                chapter.body or "",
                f"第{chapter.chapter_number}章 {chapter.title}".strip(),
            )
        state_result = await self.db.execute(
            sa.select(StoryState).where(StoryState.novel_id == novel_id)
        )
        state = state_result.scalars().first()
        if state is not None:
            state_text = json.dumps(
                {
                    "tracking": state.tracking,
                    "characters": state.characters,
                    "goals": state.goals,
                },
                ensure_ascii=False,
            )
            raw[("state", str(state.id))] = (state_text, "故事状态卡")
            for item in state.foreshadowing or []:
                raw[("foreshadowing", str(item.get("id") or ""))] = (
                    str(item.get("content") or ""),
                    f"伏笔 {item.get('id')}",
                )
        return raw
