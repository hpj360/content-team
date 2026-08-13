# Content-Team Implementation Plan

> Status: APPROVED
> Source: .claude/artifacts/designs/content-team.md
> Mode: default
> Iterations: 1 / 3
> Author: User
> Last updated: 2026-08-06

## Requirements summary

为小型自媒体团队（1-5人）构建 Web 管理后台，覆盖选题管理、内容创作、发布分发、数据分析四模块，跑通选题→创作→发布的核心内容管线。基于 hermes v0.6.0 框架复用 scheduler/DAG/orchestrator/skills 体系。

## Acceptance criteria

- AC-1 用户可以创建选题卡片（标题、描述、目标平台、优先级），选题池中可见 → 选题管理可用
- AC-2 用户可以在富文本编辑器中创建图文内容，保存草稿，查看历史版本 → 内容创作可用
- AC-3 用户可以绑定微信公众号/视频号/抖音/小红书/B站账号（OAuth） → 账号管理可用
- AC-4 用户可以选择已完成的图文内容，一键分发到已绑定的目标平台 → 发布分发可用
- AC-5 用户可以查看已发布内容在各平台的核心数据（阅读量、互动率） → 数据分析可用
- AC-6 团队成员可以共享选题池，查看和领取选题 → 轻量协作可用
- AC-7 用户可以设置定时发布，到时间自动推送到目标平台 → 定时发布可用
- AC-8 选题评分模型可以基于输入的参数给出推荐分数 → 选题评分可用

## RALPLAN-DR

### Principles

1. **继承 hermes 框架**：后端继续用 Python (FastAPI)，保持 `hermes` 包名，在内部新增 `content_team` 子模块
2. **最小可行管线**：先跑通选题→创作→发布的核心流，数据分析后续迭代
3. **渐进式平台对接**：先对接 API 最成熟的平台（微信公众号），半自动模式兜底其他平台
4. **hermes 调度复用**：定时发布直接复用 hermes scheduler，分发编排复用 DAG/orchestrator
5. **前后端分离**：后端 FastAPI + 前端 Next.js，独立部署

### Decision drivers

1. **团队熟悉度**：hermes 全栈 Python，已有 scheduler/DAG/orchestrator
2. **上线速度**：一期优先跑通核心管线，不做过度架构
3. **平台 API 可用性**：微信公众号 API 最成熟，抖音/小红书有限制

### Viable options

**Option A: Python 全栈（FastAPI + hermes 框架）+ Next.js 前端** ⬅ Chosen
- 实现思路：后端 FastAPI 复用 hermes 框架（保持包名），前端 Next.js 独立项目
- 改动文件：`src/hermes/content_team/` 新增模块，`frontend/` 新建 Next.js 项目
- Pros: 最大化复用 hermes 已有代码（scheduler, DAG, orchestrator, skills），前端体验达标
- Cons: 前后端分属不同语言生态，需要额外部署前端

**Option B: Python 后端 + htmx 服务端渲染**
- 实现思路：后端 FastAPI，前端嵌入 hermes workbench dashboard，用 Jinja2 + htmx
- 改动文件：`src/hermes/workbench/dashboard.py` 扩展
- Pros: 单体部署，无需独立前端项目
- Cons: **富文本编辑器和数据可视化体验极差**，无法满足 AC-2/AC-5 的交互需求，中期必撞墙

**Invalidation rationale for Option B**: spec 的 AC-2 明确要求富文本编辑器（TipTap/ProseMirror 级别），AC-5 要求数据可视化图表，这两项在 htmx 单体架构下体验远不达标。1-5 人团队不需要 K8s 级运维，前后端分离的部署成本可接受。

## Implementation steps

### Phase 1: 项目骨架 + 选题管理（对应 AC-1, AC-6, AC-8）

1. 新增 content_team 子包 — `src/hermes/content_team/__init__.py`
2. 新增数据模型层 — `src/hermes/content_team/models/__init__.py`, `src/hermes/content_team/models/topic.py` (Topic, TopicScore), `src/hermes/content_team/models/member.py` (TeamMember)
3. 新增数据库连接 — `src/hermes/content_team/db.py` (SQLAlchemy async + PostgreSQL), `alembic/` 迁移目录, `alembic/env.py`
4. 新增 API 层 — `src/hermes/content_team/api/__init__.py`, `src/hermes/content_team/api/topics.py` (CRUD + 评分), `src/hermes/content_team/api/router.py` (聚合路由)
5. 新增 FastAPI app 入口 — `src/hermes/content_team/app.py` (挂载 hermes config + content_team router)
6. 初始化前端项目 — `frontend/` Next.js 14 (App Router) + Tailwind CSS + shadcn/ui
7. 选题管理前端页面 — `frontend/app/topics/page.tsx` (选题池), `frontend/components/TopicCard.tsx`, `frontend/components/TopicScoreForm.tsx`
8. 轻量协作 — `src/hermes/content_team/api/members.py` (共享选题池 + 领取), `frontend/components/TopicAssignDialog.tsx`
9. 测试 — `tests/content_team/test_topic_api.py`, `tests/content_team/test_topic_model.py`

### Phase 2: 内容创作（对应 AC-2）

10. 内容模型 — `src/hermes/content_team/models/content.py` (Content, ContentVersion), `alembic/versions/002_content.py`
11. 内容 API — `src/hermes/content_team/api/content.py` (CRUD + 版本管理)
12. 富文本编辑器前端 — `frontend/components/Editor.tsx` (TipTap), `frontend/app/content/[id]/edit/page.tsx`
13. 内容与选题关联 — API 支持从选题创建内容草稿, `frontend/app/topics/[id]/create-content/page.tsx`
14. 测试 — `tests/content_team/test_content_api.py`

### Phase 3: 发布分发（对应 AC-3, AC-4, AC-7）

15. 平台账号模型 + OAuth — `src/hermes/content_team/models/platform.py` (PlatformAccount), `src/hermes/content_team/api/accounts.py` (OAuth callback), `src/hermes/content_team/publish/oauth.py`
16. 发布任务模型 — `src/hermes/content_team/models/publish.py` (PublishTask), `alembic/versions/003_publish.py`
17. 发布编排 — `src/hermes/content_team/publish/dispatcher.py` (复用 `hermes.workbench.dag` 做 fan-out), `src/hermes/content_team/publish/adapters/base.py` (适配器基类)
18. 微信公众号适配器 — `src/hermes/content_team/publish/adapters/wechat.py` (复用 `skills/wechat-reader` 的 API 知识)
19. 抖音/小红书/B站适配器 — `src/hermes/content_team/publish/adapters/douyin.py` 等（半自动模式：生成内容 + 跳转链接）
20. 定时发布 — 复用 `src/hermes/workbench/scheduler.py` 的 ScheduledJob + WorkerPool
21. 发布前端 — `frontend/app/publish/page.tsx`, `frontend/app/accounts/page.tsx`, `frontend/components/PublishDialog.tsx`
22. 测试 — `tests/content_team/publish/test_dispatcher.py`, `tests/content_team/publish/test_wechat.py`

### Phase 4: 数据分析（对应 AC-5）

23. 数据采集定时任务 — `src/hermes/content_team/analytics/collector.py` (复用 scheduler 定时拉取各平台数据)
24. 指标模型 — `src/hermes/content_team/models/metrics.py` (ContentMetric), `alembic/versions/004_metrics.py`
25. 数据 API — `src/hermes/content_team/api/analytics.py` (按内容/时间段筛选)
26. 数据可视化前端 — `frontend/app/analytics/page.tsx`, `frontend/components/MetricsChart.tsx` (Recharts)
27. 测试 — `tests/content_team/analytics/test_collector.py`

## Workspace setup

- Run `git status --short` and `git branch --show-current` before implementation.
- 当前项目为空仓库（仅 .git + 已复制的文件），建议在 main 分支上直接开发。
- 如需隔离开发，可创建 worktree：`git worktree add -b codex/phase1-topic-mgmt ../content-team-phase1`

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| 平台 API 限制（如视频号不支持直接发布） | 适配器模式 + 半自动降级：生成内容副本 + 跳转手动发布 |
| OAuth Token 过期导致分发失败 | Token 过期前 24h 预警 + 状态页醒目提示重新授权 |
| 内容格式各平台不同（字数/图片尺寸） | 发布前自动校验 + 格式转换提示，超出限制标红 |
| 数据回采延迟（各平台数据非实时） | 前端明确标注数据更新时间，定时采集 T+1 |
| hermes 包内模块间 import 耦合 | content_team 作为独立子包，不修改 hermes core 代码 |
| 前端项目独立部署增加运维 | Docker Compose 一键部署后端 + 前端 + PostgreSQL + Redis |

## Verification steps

- AC-1: `POST /api/topics` 创建选题 → `GET /api/topics` 返回含新建选题 → 前端选题池页面可见
- AC-2: `POST /api/content` 创建草稿 → `PUT /api/content/{id}` 保存 → `GET /api/content/{id}/versions` 返回版本列表 → 前端编辑器可用
- AC-3: OAuth 回调绑定成功 → `GET /api/accounts` 返回已绑定平台 → 前端账号页可见
- AC-4: `POST /api/publish` 分发 → 适配器调用外部 API → `GET /api/publish/{id}` 返回成功状态
- AC-5: `GET /api/analytics?content_id=X` 返回各平台指标 → 前端图表渲染
- AC-6: 成员 B 可见成员 A 创建的选题 → `POST /api/topics/{id}/claim` 领取成功
- AC-7: `POST /api/publish` with `scheduled_at` → scheduler 触发 → 状态变为 PUBLISHED
- AC-8: `POST /api/topics/{id}/score` → 返回 heat/expertise/timeliness/total 分数

## ADR

- **Decision**: Python FastAPI (hermes 框架) + Next.js 前端，前后端分离架构
- **Drivers**: 团队熟悉度（Python 全栈）、hermes 框架复用度、前端交互需求（富文本+图表）
- **Alternatives considered**:
  - Option A (Chosen): FastAPI + Next.js — 复用 hermes 核心 + 前端体验达标
  - Option B (Rejected): FastAPI + htmx 单体 — 部署简单但富文本和图表体验差
- **Why chosen**: hermes 已提供 scheduler/DAG/orchestrator 等核心能力可直接复用，前后端分离满足 spec 对富文本编辑器和数据可视化的交互需求，1-5 人团队部署成本可接受
- **Consequences**:
  - 正：最大化复用 hermes 已有代码，前端体验好，模块解耦清晰
  - 负：需维护两个项目，部署需 Docker Compose 编排，CORS 需配置
  - 约束：content_team 子包不得修改 hermes core 代码
- **Follow-ups**:
  - AI 辅助创作（选题推荐 / 写作辅助）→ 二期
  - 时序数据库（TimescaleDB）→ 数据量大时迁移
  - RBAC 角色权限体系 → 团队规模超过 5 人时

## Review trail

- Planner draft v1: 4 Phase 渐进实施方案，21 步具体实施
- Architect challenge v1: steelman Option B 单体架构，但承认富文本体验不达标；tradeoff tension: 开发速度 vs 前端体验
- Critic verdict v1: APPROVED — reservation: 保持 hermes 包名不变，在内部新增 content_team 子模块
- Final iterations: 1 / 3
