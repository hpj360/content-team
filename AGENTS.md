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
3. **内容引用分级纪律**（R34 起，替代原"完全不引用台词"口径）：
   `knowledge/corpus/` 与技能 references 保持**方法论/结构分析**为主体；
   允许为沉淀热门语采用以下引用层级，超出即违规：
   - **允许**：热梗/梗名/名场面**现象名**（不自带长台词）；
     台词**短引用 ≤2 句**（须标作品与年份）；公开报道与统计口径（标来源）。
   - **禁止**：成段台词/原文/美术资产照录；无出处标注的引用；
     版权期作品的整情节细节复述。范式分析文件须保留版权声明。
   - 成段素材入库的替代路径：素材由仓库所有者以**本地文档**提供，再做结构化摘录（摘要+要点，
     不逐字成段照录）。引用时效按 `content_freshness` 口径复审。
4. **提交**：仅在被明确要求时提交；消息用中文、约定式前缀（`feat/fix/docs/chore`）。
   作者身份沿用仓库既有 `Hermes Agent <hermes@agent.dev>`（用 `git -c user.name/email` 内联，勿改全局配置）。

## 测试与已知隔离

- 收集阶段隔离（`tests/conftest.py::collect_ignore_glob`）：
  `tests/skills/*`、`test_mattpocock_skills.py`、`test_grounded_citations_skill.py`、
  `test_skill_consolidation.py` —— 均为 **fork 前归档 skill 的陈旧测试**，与本项目形态无关。
- Windows 下整体跳过 `tests/workbench/`（`tests/workbench/conftest.py`）：
  该目录验证继承自 hermes 的运行时（并发写入/线程池/端口探测/递归深度等），
  在 Windows 上时序普遍偶发、每轮失败项不同；**非 Windows（含 CI）完整运行**。
- 条件跳过：
  - `tests/test_skill_sync.py` 2 例（Windows 无符号链接权限）
  - `tests/test_eval_client.py::...::test_explicit_path_checks_executable_bit`（POSIX 可执行位）
  - `tests/workbench/test_server.py::test_tasks_create_and_run`（workbench 侧历史遗留）
- 实网 LLM 套件默认跳过（`CONTENT_TEAM_LIVE_LLM=1` 显式开启）。

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
