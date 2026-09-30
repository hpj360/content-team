"""零构建工作台（创作者视角 Round 11 · C5 收官）。

不引入前端工程：由 FastAPI 直接托管**单文件 HTML**（原生 fetch + 少量内联
CSS），数据来自聚合概览 API。创作者打开 ``/dashboard`` 即可看到：

- 写作台（进度 / 下一章 / 待回收伏笔 / 连续性警告 / 下一步动作）
- 审查趋势（平均分 / 结果分布 / 近轮次）
- 运行列表（含报告与导出入口）
- 一键发起创作（选题 → 运行）
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hermes.content_team.db import get_db
from hermes.content_team.models.creative import (
    CreationRun,
    Novel,
    NovelChapter,
    StoryState,
)
from hermes.content_team.models.topic import Topic

router = APIRouter()

_OVERVIEW_LIMIT = 50
_RUN_LIMIT = 10


async def build_dashboard_overview(db: AsyncSession) -> dict[str, Any]:
    """聚合概览：小说 + 选题 + 运行 + 审查统计（供工作台一次拉取）。"""
    novel_result = await db.execute(select(Novel).limit(_OVERVIEW_LIMIT))
    novels = list(novel_result.scalars().all())
    novels_payload: list[dict[str, Any]] = []
    for novel in novels:
        chapter_result = await db.execute(
            select(NovelChapter).where(NovelChapter.novel_id == novel.id)
        )
        chapters = list(chapter_result.scalars().all())
        state_result = await db.execute(
            select(StoryState).where(StoryState.novel_id == novel.id)
        )
        state = state_result.scalars().first()
        pending = [
            item
            for item in (state.foreshadowing if state else []) or []
            if str(item.get("status") or "") != "resolved"
        ]
        novels_payload.append(
            {
                "id": str(novel.id),
                "title": novel.title,
                "status": novel.status.value if novel.status else None,
                "chapters": len(chapters),
                "words": sum(c.word_count or 0 for c in chapters),
                "pending_foreshadowing": len(pending),
            }
        )

    topic_result = await db.execute(select(Topic).limit(_OVERVIEW_LIMIT))
    topics_payload = [
        {"id": str(t.id), "title": t.title, "status": t.status.value if t.status else None}
        for t in topic_result.scalars().all()
    ]

    run_result = await db.execute(
        select(CreationRun).order_by(CreationRun.created_at.desc()).limit(_RUN_LIMIT)
    )
    runs = list(run_result.scalars().all())
    runs_payload = [
        {
            "id": str(r.id),
            "topic_id": str(r.topic_id) if r.topic_id else None,
            "status": r.status.value if r.status else None,
            "review_score": r.review_score,
            "revise_rounds": r.revise_rounds,
            "revision_outcome": (
                r.revision_outcome.value if r.revision_outcome else None
            ),
            "novel_id": (r.artifacts or {}).get("novel_id"),
            "script_id": (r.artifacts or {}).get("script_id"),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]

    all_runs_result = await db.execute(select(CreationRun))
    all_runs = list(all_runs_result.scalars().all())
    by_status: dict[str, int] = {}
    outcomes: dict[str, int] = {}
    scores = [r.review_score for r in all_runs if r.review_score is not None]
    for run in all_runs:
        key = run.status.value if run.status else "UNKNOWN"
        by_status[key] = by_status.get(key, 0) + 1
        outcome = run.revision_outcome.value if run.revision_outcome else "NONE"
        outcomes[outcome] = outcomes.get(outcome, 0) + 1

    stats = {
        "total_runs": len(all_runs),
        "by_status": by_status,
        "avg_review_score": (
            round(sum(scores) / len(scores), 2) if scores else None
        ),
        "revision_outcomes": outcomes,
    }

    return {
        "novels": novels_payload,
        "topics": topics_payload,
        "runs": runs_payload,
        "stats": stats,
    }


@router.get("/api/dashboard/overview")
async def dashboard_overview(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """工作台聚合数据（小说 / 选题 / 运行 / 统计）。"""
    return await build_dashboard_overview(db)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page() -> HTMLResponse:
    """零构建工作台页面（单文件，原生 fetch）。"""
    return HTMLResponse(content=DASHBOARD_HTML)


DASHBOARD_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>content-team 工作台</title>
<style>
:root{--bg:#0f1216;--panel:#171b21;--line:#242a33;--fg:#e6e9ef;--dim:#8b95a5;
      --ok:#3fb950;--warn:#d29922;--err:#f85149;--accent:#58a6ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
     font:14px/1.6 "Segoe UI",system-ui,"Microsoft YaHei",sans-serif}
header{padding:14px 20px;border-bottom:1px solid var(--line);
       display:flex;align-items:center;gap:12px}
h1{font-size:16px;margin:0}
.dim{color:var(--dim)}
main{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));
     gap:14px;padding:16px}
section{background:var(--panel);border:1px solid var(--line);
        border-radius:10px;padding:14px}
h2{font-size:13px;margin:0 0 10px;color:var(--dim);font-weight:600;
   letter-spacing:.06em;text-transform:uppercase}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:6px 4px;border-bottom:1px solid var(--line)}
th{color:var(--dim);font-weight:500}
.badge{padding:1px 7px;border-radius:99px;font-size:11px;border:1px solid var(--line)}
.s-SUCCEEDED{color:var(--ok);border-color:var(--ok)}
.s-NEEDS_REVISION{color:var(--warn);border-color:var(--warn)}
.s-STOPPED,.s-FAILED{color:var(--err);border-color:var(--err)}
a{color:var(--accent);text-decoration:none}
button{background:var(--accent);color:#04121f;border:0;border-radius:6px;
       padding:6px 12px;font-weight:600;cursor:pointer}
select{background:var(--bg);color:var(--fg);border:1px solid var(--line);
       border-radius:6px;padding:6px}
.kv{display:flex;justify-content:space-between;padding:4px 0;
    border-bottom:1px dashed var(--line)}
.empty{color:var(--dim);font-size:13px}
ul.actions{margin:0;padding-left:18px}
code{color:var(--dim)}
</style>
</head>
<body>
<header>
  <h1>content-team 工作台</h1>
  <span class="dim" id="stat-line">加载中…</span>
</header>
<main>
  <section>
    <h2>写作台</h2>
    <div id="desk" class="empty">选择左侧小说查看</div>
  </section>
  <section>
    <h2>我的作品</h2>
    <table><thead><tr><th>书名</th><th>章</th><th>字数</th><th>待收伏笔</th><th></th></tr></thead>
    <tbody id="novels"></tbody></table>
  </section>
  <section>
    <h2>审查趋势</h2>
    <div id="stats" class="empty"></div>
  </section>
  <section>
    <h2>最近运行</h2>
    <table><thead><tr><th>状态</th><th>分</th><th>修订</th><th>操作</th></tr></thead>
    <tbody id="runs"></tbody></table>
  </section>
  <section>
    <h2>发起创作</h2>
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
      <select id="topic"></select>
      <button id="create">运行创作管线</button>
      <span class="dim" id="create-msg"></span>
    </div>
  </section>
</main>
<script>
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

async function getJSON(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error(url + " -> " + r.status);
  return r.json();
}

function renderStats(stats) {
  const avg = stats.avg_review_score == null ? "—" : stats.avg_review_score;
  const rows = Object.entries(stats.by_status || {})
    .map(([k, v]) => `<div class="kv"><span>${esc(k)}</span><span>${v}</span></div>`)
    .join("");
  $("stats").innerHTML =
    `<div class="kv"><span>总运行</span><span>${stats.total_runs ?? 0}</span></div>` +
    `<div class="kv"><span>平均审查分</span><span>${avg}</span></div>` + rows;
}

function renderNovels(novels) {
  if (!novels.length) { $("novels").innerHTML = '<tr><td colspan="5" class="empty">暂无作品</td></tr>'; return; }
  $("novels").innerHTML = novels.map((n) =>
    `<tr><td>${esc(n.title)}</td><td>${n.chapters}</td><td>${n.words}</td>` +
    `<td>${n.pending_foreshadowing}</td>` +
    `<td><a href="#" data-desk="${esc(n.id)}">写作台</a> · ` +
    `<a href="/api/novels/${esc(n.id)}/writing-desk" target="_blank">JSON</a> · ` +
    `<a href="/api/novels/${esc(n.id)}/export?format=txt">TXT</a></td></tr>`
  ).join("");
  $("novels").querySelectorAll("[data-desk]").forEach((a) =>
    a.onclick = (e) => { e.preventDefault(); loadDesk(a.dataset.desk); });
}

function renderRuns(runs) {
  if (!runs.length) { $("runs").innerHTML = '<tr><td colspan="4" class="empty">暂无运行</td></tr>'; return; }
  $("runs").innerHTML = runs.map((r) =>
    `<tr><td><span class="badge s-${esc(r.status)}">${esc(r.status)}</span></td>` +
    `<td>${r.review_score == null ? "—" : r.review_score}</td>` +
    `<td>${r.revise_rounds}${r.revision_outcome && r.revision_outcome !== "NONE" ? " / " + esc(r.revision_outcome) : ""}</td>` +
    `<td><a href="/api/creation/runs/${esc(r.id)}/report" target="_blank">报告</a>` +
    (r.script_id ? ` · <a href="/api/scripts/${esc(r.script_id)}/export" target="_blank">剧本</a>` : "") +
    `</td></tr>`
  ).join("");
}

async function loadDesk(novelId) {
  $("desk").innerHTML = "加载中…";
  try {
    const d = await getJSON(`/api/novels/${novelId}/writing-desk`);
    const warns = (d.continuity_warnings || []);
    const errs = warns.filter((w) => w.severity === "error");
    $("desk").innerHTML =
      `<div class="kv"><span>${esc(d.novel.title)}</span><span>共 ${d.progress.chapters} 章 / ${d.progress.total_words} 字</span></div>` +
      `<div class="kv"><span>下一章</span><span>第 ${d.progress.next_chapter} 章</span></div>` +
      `<div class="kv"><span>待回收伏笔</span><span>${d.pending_foreshadowing.length}</span></div>` +
      `<div class="kv"><span>连续性警告</span><span>${errs.length} 错 / ${warns.length - errs.length} 警</span></div>` +
      `<p class="dim">下一步：</p><ul class="actions">` +
      (d.next_actions || []).map((a) => `<li>${esc(a)}</li>`).join("") + `</ul>` +
      (warns.length ? `<p class="dim">警告：</p>` + warns.slice(0, 6).map((w) =>
        `<div class="kv"><span><code>${esc(w.code)}</code> ${esc(w.message)}</span>` +
        `<span class="${w.severity === "error" ? "s-FAILED" : "s-NEEDS_REVISION"}">${esc(w.severity)}</span></div>`
      ).join("") : "");
  } catch (e) { $("desk").innerHTML = `<span class="s-FAILED">${esc(e.message)}</span>`; }
}

async function load() {
  const data = await getJSON("/api/dashboard/overview");
  renderStats(data.stats);
  renderNovels(data.novels);
  renderRuns(data.runs);
  $("topic").innerHTML = (data.topics || []).map((t) =>
    `<option value="${esc(t.id)}">${esc(t.title)}</option>`).join("") ||
    '<option value="">（暂无选题）</option>';
  $("stat-line").textContent =
    `作品 ${data.novels.length} · 选题 ${data.topics.length} · 运行 ${data.stats.total_runs}`;
  if (data.novels.length) loadDesk(data.novels[0].id);
}

$("create").onclick = async () => {
  const topicId = $("topic").value;
  if (!topicId) return;
  $("create-msg").textContent = "运行中…";
  try {
    const run = await getJSON("/api/creation/runs", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({topic_id: topicId}),
    });
    $("create-msg").innerHTML =
      `完成：<span class="badge s-${esc(run.status)}">${esc(run.status)}</span> 分 ${run.review_score ?? "—"}`;
    load();
  } catch (e) { $("create-msg").innerHTML = `<span class="s-FAILED">${esc(e.message)}</span>`; }
};

load();
</script>
</body>
</html>
"""
