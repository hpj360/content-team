# Content-Team 综合运营平台 Spec

> Status: DRAFT
> Author: User
> Last updated: 2026-08-06

## Background

小型自媒体团队缺乏一个统一的运营管理工具，选题、创作、发布、数据分析分散在不同平台和工具中，导致效率低下、协作困难。Content-Team 旨在提供一站式的自媒体综合运营平台，覆盖从选题到发布再到数据复盘的完整内容管线。

## In scope

### 一期核心模块（按 MVP 优先级排列）

1. **选题管理** — 选题库、灵感记录、选题排期、选题评分
2. **内容创作** — 文章/图文编辑器、视频内容创建、版本管理
3. **发布分发** — 多平台一键分发、定时发布、发布状态追踪、账号管理
4. **数据分析** — 阅读量、互动率、粉丝增长等数据可视化

### 平台对接

- 微信生态：微信公众号、视频号
- 短视频/种草平台：抖音、小红书、B站

### 协作能力

- 轻量协作：共享选题库、基础任务指派
- 不做严格的角色权限体系（后续迭代）

### AI 辅助（Optional）

- AI 选题推荐
- AI 写作辅助 / 内容润色
- 视一期带宽决定是否纳入

## Out of scope

- 社群运营 / 私域管理 / 粉丝社群
- 商业化变现 / 广告投放 / 订单管理
- 版权保护 / 素材溯源 / 水印管理
- 严格的 RBAC 角色权限体系
- 移动端原生 App

## Assumptions

- 目标用户为 1-5 人的小型自媒体团队，主理人亲自参与创作和运营
- 平台形态为 Web 管理后台，PC 为主
- 一期优先跑通选题→创作→发布的完整管线
- 外部平台 API 对接存在限制，部分平台可能只能做到半自动（如手动跳转发布）
- 用户已有各外部平台的账号，平台不负责账号注册

## Solution

### 整体架构

Web 管理后台（B/S 架构），前后端分离：

- **前端**：React/Next.js 管理后台，富文本编辑器（TipTap / ProseMirror）
- **后端**：Python (FastAPI) 或 TypeScript (NestJS) API 服务
- **数据库**：PostgreSQL + Redis
- **第三方对接**：各平台开放 API，通过 OAuth 授权管理

### 核心流程

```
选题创建/评分 → 内容创建(编辑器) → 审核(轻量) → 多平台分发 → 数据回采分析
```

### 选题管理

- 选题池：支持手动创建、灵感快速记录
- 选题卡片：标题、描述、目标平台、优先级、状态（待定/进行中/已发布）
- 选题评分：基于热度、团队擅长度、时效性的简易评分模型

### 内容创作

- 富文本编辑器：支持图文混排、Markdown 导入
- 多格式支持：文章（图文）、视频脚本
- 版本管理：内容草稿的保存和历史版本查看

### 发布分发

- 账号管理：OAuth 绑定各平台账号
- 一键分发：选择目标平台后同步发布
- 定时发布：设置发布时间，到时自动推送
- 状态追踪：各平台发布成功/失败状态

### 数据分析

- 数据采集：通过各平台 API 拉取内容数据
- 核心指标：阅读量、点赞/评论/转发、粉丝增减
- 可视化：图表展示，支持按内容/时间段筛选

## Edge cases & risks

| Category | Notes |
|---|---|
| 平台 API 限制 | 部分平台 API 能力有限（如视频号可能不支持直接发布），需降级为半自动模式 |
| OAuth 授权过期 | Token 过期需提醒用户重新授权，否则分发失败 |
| 内容格式适配 | 不同平台对内容格式、字数、图片尺寸要求不同，需做格式适配 |
| 数据回采延迟 | 各平台数据接口有延迟，需明确数据时效性预期 |
| 多人并发编辑 | 轻量协作下不做实时协同编辑，使用乐观锁避免冲突 |
| 内容安全 | 发布前需基础的内容合规检查（敏感词等） |

## Acceptance criteria

- AC-1 用户可以创建选题卡片（标题、描述、目标平台、优先级），选题池中可见 → 选题管理可用
- AC-2 用户可以在富文本编辑器中创建图文内容，保存草稿，查看历史版本 → 内容创作可用
- AC-3 用户可以绑定微信公众号/视频号/抖音/小红书/B站账号（OAuth） → 账号管理可用
- AC-4 用户可以选择已完成的图文内容，一键分发到已绑定的目标平台 → 发布分发可用
- AC-5 用户可以查看已发布内容在各平台的核心数据（阅读量、互动率） → 数据分析可用
- AC-6 团队成员可以共享选题池，查看和领取选题 → 轻量协作可用
- AC-7 用户可以设置定时发布，到时间自动推送到目标平台 → 定时发布可用
- AC-8 选题评分模型可以基于输入的参数给出推荐分数 → 选题评分可用

## Open questions

- AI 辅助创作是否纳入一期？如果是，优先做选题推荐还是写作辅助？
- 后端技术选型：Python (FastAPI) 还是 TypeScript (NestJS)？
- 数据库：是否需要时序数据支持（用于数据趋势分析）？

## Core entities (ontology)

| Entity | Type | Key fields | Relationship |
|---|---|---|---|
| Topic | 核心实体 | id, title, description, priority, status, score, target_platforms | → Content (1:N) |
| Content | 核心实体 | id, type, body, versions, status, author_id | → Topic (N:1), → PublishTask (1:N) |
| PublishTask | 核心实体 | id, content_id, platform, account_id, scheduled_at, status | → Content (N:1), → PlatformAccount (N:1) |
| PlatformAccount | 核心实体 | id, platform, auth_token, user_info | → PublishTask (1:N) |
| ContentMetric | 核心实体 | id, content_id, platform, views, likes, comments, shares, date | → Content (N:1) |
| TeamMember | 协作实体 | id, name, role, email | → Topic (assigned_to) |
| TopicScore | 计算实体 | id, topic_id, heat, expertise, timeliness, total | → Topic (1:1) |

## Interview metadata

- Mode: default
- Waves: 3
- Final ambiguity: 23.5%
- Status: PASSED

### Clarity breakdown

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| Goal | 0.85 | 0.43 | 0.366 |
| Scope | 0.75 | 0.28 | 0.210 |
| AC | 0.65 | 0.29 | 0.189 |
