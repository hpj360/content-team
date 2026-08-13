# Content-Team 全面迭代规划 Spec

## Why

Hermes 框架已复制到 content-team 项目，但仍有多个高价值能力模块尚未启用（三层记忆、崩溃恢复、链路追踪、结构化日志、Cron 触发器、Goal 循环）。同时，一期实施方案（4 Phase / 27 步）只覆盖了基础功能管线，缺少对后续迭代（AI 辅助、自动化循环、内容模板、可观测性）的系统性规划。本 spec 统一规划 hermes 剩余能力移植 + 后续迭代目标。

## What Changes

### 一、Hermes 剩余能力移植（高优先级）

- 启用 `workbench/memory.py` — 三层记忆系统（L1 facts / L2 episodes / L3 profile），用于内容知识沉淀、选题记忆、用户偏好
- 启用 `workbench/recovery.py` — 崩溃恢复管理器，保障定时发布任务在进程重启后自动恢复
- 启用 `workbench/tracing.py` — 链路追踪（trace_id），用于追踪选题→创作→发布的完整操作链
- 启用 `workbench/structured_logging.py` — JSON 结构化日志，用于生产环境可观测性
- 启用 `workbench/triggers.py` — Cron 定时触发器，扩展定时发布和数据采集能力
- 启用 `workbench/goal.py` — Goal 驱动循环（Planner/Generator/Evaluator），用于 AI 辅助创作
- 移植 `content-creation/` 目录 — 90 天冷启动落地计划、选题库模板，作为内容模板系统的基础

### 二、后续迭代目标规划

- **Phase 5: AI 辅助创作** — 基于 goal.py + LLM 实现选题推荐、写作辅助、内容润色
- **Phase 6: 内容自动化循环** — 基于 loop.py + builder/checker 模式实现选题调研、内容审核自动化
- **Phase 7: 内容知识库** — 基于 memory.py 三层记忆构建内容领域知识图谱
- **Phase 8: 可观测性体系** — 基于 tracing.py + structured_logging.py 构建全链路监控
- **Phase 9: 内容模板系统** — 基于冷启动计划模板沉淀可复用的内容生产模板

### 三、归档 Skill 评估与选择性启用

- **skill-creator**（HIGH）— 用于创建 content-team 专属 skill（如 topic-scorer, content-reviewer）
- **grounded-citations**（MEDIUM）— 用于内容发布前的事实核查
- **loop-engineering**（MEDIUM）— 用于构建内容自动化循环
- **to-spec / to-tickets**（MEDIUM）— 用于内容规划→任务拆解流程
- **domain-modeling**（MEDIUM）— 用于内容领域模型迭代

## Impact

- Affected specs: `.claude/artifacts/designs/content-team.md`, `.claude/artifacts/plans/content-team.md`
- Affected code:
  - `src/hermes/workbench/` — 启用 memory.py, recovery.py, tracing.py, structured_logging.py, triggers.py, goal.py
  - `src/hermes/content_team/` — 一期新增模块（待实现）
  - `content-creation/` — 移植内容模板
  - `skills/_archive/skill-creator/` — 提升为活跃 skill
  - `manifest.json` — 更新活跃/归档 skill 列表

## ADDED Requirements

### Requirement: 三层记忆系统启用
系统 SHALL 启用 hermes workbench 的三层记忆服务，为 content-team 提供内容知识沉淀能力。

#### Scenario: 选题记忆持久化
- **WHEN** 用户创建选题并评分
- **THEN** 选题信息写入 L1 facts，评分行为记录到 L2 episodes
- **AND** 用户偏好（如常选平台、选题偏好）更新到 L3 profile

#### Scenario: 发布链路可追溯
- **WHEN** 内容从创作到发布经过多个步骤
- **THEN** 每个步骤通过 trace_id 关联，可在日志中检索完整链路

### Requirement: 崩溃恢复
系统 SHALL 在进程重启后自动恢复非终态的定时发布任务。

#### Scenario: 发布任务崩溃恢复
- **WHEN** 进程在定时发布任务执行中崩溃
- **AND** 进程重新启动
- **THEN** QUEUED 状态的任务重新入队
- **AND** RUNNING 状态的任务标记为 ABANDONED
- **AND** 恢复操作记录到 L2 episode

### Requirement: Cron 定时触发器
系统 SHALL 支持 Cron 表达式触发定时任务，用于周期性数据采集和定时发布。

#### Scenario: 每日数据采集
- **WHEN** 设置 Cron 触发器 `0 9 * * *`（每天 9 点）
- **THEN** 触发器创建数据采集 ScheduledJob
- **AND** WorkerPool 消费并执行采集任务

### Requirement: AI 辅助创作（Phase 5）
系统 SHALL 基于 hermes Goal 循环和 LLM 提供选题推荐和写作辅助能力。

#### Scenario: AI 选题推荐
- **WHEN** 用户输入领域关键词和目标平台
- **THEN** Goal 循环调用 LLM 生成选题建议
- **AND** Evaluator 验证选题与历史选题不重复
- **AND** 推荐结果写入选题池

### Requirement: 内容自动化循环（Phase 6）
系统 SHALL 基于 Loop Engineering 的 builder/checker 模式实现内容审核自动化。

#### Scenario: 内容发布前自动审核
- **WHEN** 内容提交发布
- **THEN** builder 生成审核检查项（敏感词、格式合规、字数限制）
- **AND** checker 验证每项检查
- **AND** 全部通过后自动放行，否则标记待人工审核

### Requirement: 内容知识库（Phase 7）
系统 SHALL 基于三层记忆构建内容领域知识库，支撑选题决策和创作参考。

#### Scenario: 选题灵感检索
- **WHEN** 用户输入关键词
- **THEN** 系统从 L1 facts 检索历史选题和内容
- **AND** 从 L2 episodes 检索相关创作行为
- **AND** 从 L3 profile 匹配用户擅长领域
- **AND** 返回关联度最高的灵感建议

### Requirement: 可观测性体系（Phase 8）
系统 SHALL 提供全链路结构化日志和追踪能力。

#### Scenario: 发布失败排查
- **WHEN** 发布任务失败
- **THEN** 通过 trace_id 检索完整操作链日志
- **AND** 日志包含每步的 event, task_id, trace_id, timestamp
- **AND** 支持按平台、内容、时间范围筛选

### Requirement: 内容模板系统（Phase 9）
系统 SHALL 提供可复用的内容生产模板，基于冷启动计划沉淀最佳实践。

#### Scenario: 使用模板创建内容
- **WHEN** 用户选择「小红书种草文」模板
- **THEN** 系统加载模板结构（标题公式、正文结构、话题标签建议）
- **AND** 在编辑器中预填充模板框架
- **AND** 用户在框架内填充具体内容

## MODIFIED Requirements

### Requirement: Hermes 框架集成
一期实施方案中 Phase 1-4 的基础上，content_team 子包 SHALL 同时启用 hermes workbench 的高价值模块，而非仅复用 scheduler 和 DAG。

### Requirement: Skill 体系
活跃 skill 列表 SHALL 新增 skill-creator，用于创建 content-team 专属 skill。归档 skill 的启用需经过评估并在 manifest.json 中更新状态。
