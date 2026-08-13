# Context

## Project

Content-Team: 自媒体综合运营平台，服务于小型自媒体团队（1-5人），提供选题→创作→发布→数据分析的完整管线。

## Glossary

| Term | Meaning | Notes |
|---|---|---|
| Topic | 选题，内容创作的起点 | 包含标题、描述、目标平台、优先级、状态和评分 |
| Content | 内容实体，选题的具体创作产出 | 支持图文/视频脚本，有版本管理 |
| PublishTask | 发布任务，将内容分发到特定平台 | 包含定时发布和状态追踪 |
| PlatformAccount | 平台账号，绑定的外部自媒体账号 | 微信公众号/视频号/抖音/小红书/B站 |
| ContentMetric | 内容指标，已发布内容在各平台的数据 | 阅读量、互动率、粉丝增长 |
| TeamMember | 团队成员 | 轻量协作，共享选题池 |
| TopicScore | 选题评分，基于热度/擅长度/时效性 | 辅助选题决策 |
| ScheduledJob | 定时任务（继承自 hermes） | 用于定时发布、数据回采等周期性任务 |
| Loop | 执行循环（继承自 hermes） | builder/checker 模式，L1/L2/L3 三阶段自治 |
| Skill | 可复用的能力单元（继承自 hermes） | 三级加载：discovery/activation/execution |
| Orchestrator | 子 Agent 编排器（继承自 hermes） | fan-out/fan-in，用于多平台分发等并行任务 |

## Architecture

基于 hermes v0.6.0 框架：
- **核心层**: config → skills → loop → orchestrator
- **调度层**: scheduler (APScheduler) + DAG (任务依赖图)
- **持久层**: persistence (SQLite/JSON) + memory
- **Skill 体系**: 13 个活跃 skill + 28 个归档 skill
