# AGENTS.md — 本仓库的协作约定

面向在此仓库工作的 AI agent / 开发者。项目背景见 `CONTEXT.md`，能力总览见 `README.md`。

## 环境与命令

```powershell
$env:PYTHONPATH="src"                       # 运行前必须设置（包在 src/ 下）
py -3.12 -m pytest tests/content_team tests/test_creative_skills.py -q   # 本项目套件（应全绿）
py -3.12 -m pytest -q                                                    # 全量
py -3.12 -m ruff check --isolated --select E4,E7,E9,F --line-length 100 src/hermes/content_team tests/content_team
```

- Python 3.11/3.12；本机使用 `py -3.12`。
- **实网 LLM 测试默认跳过**，需显式 `CONTENT_TEAM_LIVE_LLM=1` + provider 配置（见 README）。

## 硬性约定

1. **不要用 shell 写文件**（PowerShell `Set-Content`/`Out-File` 会把 UTF-8 中文写成乱码/非法字符）。
   一律使用编辑器工具读写文件。曾因此损坏过源码，需从 git 恢复。
2. **不改动 hermes core**（`src/hermes/*.py` 非 content_team 部分），业务只落在 `src/hermes/content_team/`。
   例外：确有必要的最小修复需在提交信息中说明理由（如 `skills.py` 的稳定排序）。
3. **不复制受版权内容**：`knowledge/corpus/` 与技能 references 只做**方法论/结构**分析，
   禁止复制剧本、台词、原文、美术资产；范式分析文件须保留顶部版权声明。
4. **提交**：仅在被明确要求时提交；消息用中文、约定式前缀（`feat/fix/docs/chore`）。
   作者身份沿用仓库既有 `Hermes Agent <hermes@agent.dev>`（用 `git -c user.name/email` 内联，勿改全局配置）。

## 测试与已知隔离

- 收集阶段隔离（`tests/conftest.py::collect_ignore_glob`）：
  `tests/skills/*`、`test_mattpocock_skills.py`、`test_grounded_citations_skill.py`、
  `test_skill_consolidation.py` —— 均为 **fork 前归档 skill 的陈旧测试**，与本项目形态无关。
- 条件跳过：
  - `tests/test_skill_sync.py` 2 例（Windows 无符号链接权限）
  - `tests/workbench/test_server.py::test_tasks_create_and_run`（workbench 侧历史遗留）
- 已知**偶发**（Windows 并发/线程，workbench 侧，非本项目）：`test_atomic_append_jsonl_concurrent_writes`、
  `test_concurrent_writes_no_loss`、`test_ping_local_success`、`test_execute_single_job_succeeds`、
  `test_sync_memory_between_projects` —— 隔离复跑可通过。

## 代码约定

- 中文 docstring/注释；`from __future__ import annotations`；SQLAlchemy 2.0 `Mapped[...]`。
- 门禁/质量逻辑集中在 `creative/gates.py`（纯函数，可离线测试）；审查/修订/编排分层清晰：
  builder（生成）· checker（门禁）· reviewer（独立审查）· reviser（修订）· planner/drafter/critic（角色）。
- 新增能力必须带离线测试；涉及 LLM 的路径用 `tests/content_team/_fakes.FakeLlmClient` 注入。

## 目录速查

| 路径 | 内容 |
|---|---|
| `src/hermes/content_team/creative/` | 创作域核心（gates/reviewer/revision/pipeline/planner/drafter/corpus/...） |
| `src/hermes/content_team/api/` | FastAPI 路由 |
| `skills/<name>/` | 技能（SKILL.md + references/） |
| `knowledge/` | 质量模型、调优报告、语料库、ADRs 之外的沉淀 |
| `tests/content_team/` | 本项目测试（含实网 opt-in 套件） |
