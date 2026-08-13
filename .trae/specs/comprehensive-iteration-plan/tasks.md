# Tasks

## 一、Hermes 剩余能力移植（与 Phase 1 并行）

- [x] Task 1: 启用三层记忆系统 — 在 content_team 中集成 `workbench/memory.py`，配置 L1/L2/L3 存储路径
  - [x] SubTask 1.1: 创建 `src/hermes/content_team/memory.py`，初始化 MemoryService 并绑定存储目录
  - [x] SubTask 1.2: 在 content_team app 入口注入 MemoryService 单例
  - [x] SubTask 1.3: 为 Topic 模型添加 memory hook（创建/评分时写 episode）
  - [x] SubTask 1.4: 测试 `tests/content_team/test_memory.py` — 验证 L1 读写、L2 追加、L3 更新

- [x] Task 2: 启用结构化日志 + 链路追踪 — 集成 `workbench/structured_logging.py` 和 `workbench/tracing.py`
  - [x] SubTask 2.1: 在 content_team app 启动时调用 `configure_logging(level, json=True)`
  - [x] SubTask 2.2: 为 API 请求中间件添加 trace_id 注入（每个请求生成 trace_id）
  - [x] SubTask 2.3: 在 Topic/Content/PublishTask API 中添加 `log_context` 绑定
  - [x] SubTask 2.4: 测试 `tests/content_team/test_observability.py` — 验证 trace_id 传播和日志格式

- [x] Task 3: 启用崩溃恢复 — 集成 `workbench/recovery.py`
  - [x] SubTask 3.1: 在 content_team app 启动流程中调用 `RecoveryManager.recover()`
  - [x] SubTask 3.2: 配置环境变量 `CONTENT_TEAM_SCHEDULER_RECOVERY` 开关
  - [x] SubTask 3.3: 测试 `tests/content_team/test_recovery.py` — 模拟崩溃后重启恢复

- [x] Task 4: 启用 Cron 定时触发器 — 集成 `workbench/triggers.py`
  - [x] SubTask 4.1: 创建 `src/hermes/content_team/triggers.py`，注册内容相关 Cron 触发器
  - [x] SubTask 4.2: 实现每日数据采集触发器（默认 9:00 执行）
  - [x] SubTask 4.3: 实现定时发布触发器（支持 Cron 表达式自定义）
  - [x] SubTask 4.4: 测试 `tests/content_team/test_triggers.py` — 验证 Cron 解析和触发

- [x] Task 5: 移植 content-creation 内容模板
  - [x] SubTask 5.1: 复制 `D:\Hermes\hermes-temp\content-creation\` 到 `content-creation/`
  - [ ] SubTask 5.2: 解析 90 天冷启动计划为结构化模板数据（JSON）
  - [ ] SubTask 5.3: 解析选题库为结构化模板数据

- [x] Task 6: 提升 skill-creator 为活跃 skill
  - [x] SubTask 6.1: 将 `skills/_archive/skill-creator/` 移动到 `skills/skill-creator/`
  - [x] SubTask 6.2: 更新 `manifest.json` 活跃/归档列表

## 二、一期功能实现（Phase 1-4，来自 dev-plan）

- [x] Task 7: Phase 1 — 项目骨架 + 选题管理（AC-1, AC-6, AC-8）
  - [x] SubTask 7.1: 新增 content_team 子包结构
  - [x] SubTask 7.2: 数据模型层（Topic, TopicScore, TeamMember）
  - [x] SubTask 7.3: 数据库连接（SQLAlchemy async + SQLite）
  - [x] SubTask 7.4: API 层（topics CRUD + 评分 + members）
  - [x] SubTask 7.5: FastAPI app 入口
  - [ ] SubTask 7.6: 前端 Next.js 初始化 + 选题池页面
  - [x] SubTask 7.7: 测试验证 AC-1/AC-6/AC-8（57 passed）

- [x] Task 8: Phase 2 — 内容创作（AC-2）
  - [x] SubTask 8.1: 内容模型（Content, ContentVersion）
  - [x] SubTask 8.2: 内容 API + 版本管理
  - [ ] SubTask 8.3: TipTap 富文本编辑器前端
  - [x] SubTask 8.4: 选题→内容关联
  - [x] SubTask 8.5: 测试验证 AC-2（20 tests passed）

- [x] Task 9: Phase 3 — 发布分发（AC-3, AC-4, AC-7）
  - [x] SubTask 9.1: 平台账号模型 + OAuth
  - [x] SubTask 9.2: 发布任务模型
  - [x] SubTask 9.3: 发布编排（dispatcher + adapters）
  - [x] SubTask 9.4: 微信公众号适配器
  - [x] SubTask 9.5: 抖音/小红书/B站适配器（半自动）
  - [x] SubTask 9.6: 定时发布（复用 scheduler + triggers）
  - [ ] SubTask 9.7: 发布前端
  - [x] SubTask 9.8: 测试验证 AC-3/AC-4/AC-7（32 tests passed）

- [x] Task 10: Phase 4 — 数据分析（AC-5）
  - [x] SubTask 10.1: 数据采集定时任务
  - [x] SubTask 10.2: 指标模型
  - [x] SubTask 10.3: 数据 API
  - [ ] SubTask 10.4: 数据可视化前端
  - [x] SubTask 10.5: 测试验证 AC-5（15 tests passed）

## 三、后续迭代（Phase 5-9）

- [ ] Task 11: Phase 5 — AI 辅助创作
  - [ ] SubTask 11.1: 启用 `workbench/goal.py` + `workbench/llm.py`
  - [ ] SubTask 11.2: 实现选题推荐 Goal（LLM 生成 + 去重验证）
  - [ ] SubTask 11.3: 实现写作辅助 Goal（LLM 生成 + 质量评估）
  - [ ] SubTask 11.4: 前端集成 AI 辅助入口

- [ ] Task 12: Phase 6 — 内容自动化循环
  - [ ] SubTask 12.1: 基于 `loop.py` 实现内容审核 builder/checker
  - [ ] SubTask 12.2: 敏感词检测 + 格式合规自动检查
  - [ ] SubTask 12.3: 发布前自动审核流程编排

- [ ] Task 13: Phase 7 — 内容知识库
  - [ ] SubTask 13.1: 基于 L1 facts 构建选题历史库
  - [ ] SubTask 13.2: 基于 L2 episodes 构建创作行为日志
  - [ ] SubTask 13.3: 基于 L3 profile 构建用户擅长领域画像
  - [ ] SubTask 13.4: 实现灵感检索 API（TF-IDF + 余弦相似度）

- [ ] Task 14: Phase 8 — 可观测性体系
  - [ ] SubTask 14.1: 全链路 trace_id 传播（API → Service → Scheduler）
  - [ ] SubTask 14.2: 结构化日志接入（JSON → Loki/ELK）
  - [ ] SubTask 14.3: 运维仪表盘（发布成功率、采集延迟、错误率）

- [ ] Task 15: Phase 9 — 内容模板系统
  - [ ] SubTask 15.1: 模板数据模型 + 存储
  - [ ] SubTask 15.2: 从冷启动计划提取模板
  - [ ] SubTask 15.3: 编辑器模板加载
  - [ ] SubTask 15.4: 模板管理 UI

# Task Dependencies

- Task 1 (memory) 无依赖，可与 Task 7 并行
- Task 2 (logging+tracing) 无依赖，可与 Task 7 并行
- Task 3 (recovery) 依赖 Task 7（需要 scheduler 运行环境）
- Task 4 (triggers) 依赖 Task 7（需要 scheduler 运行环境）
- Task 5 (content templates) 无依赖，可与 Task 7 并行
- Task 6 (skill-creator) 无依赖，可与 Task 7 并行
- Task 7 (Phase 1) 无依赖，优先启动
- Task 8 (Phase 2) 依赖 Task 7
- Task 9 (Phase 3) 依赖 Task 7, Task 8
- Task 10 (Phase 4) 依赖 Task 9
- Task 11 (Phase 5 AI) 依赖 Task 7, Task 1（需要 memory）
- Task 12 (Phase 6 审核循环) 依赖 Task 8, Task 9
- Task 13 (Phase 7 知识库) 依赖 Task 1, Task 7, Task 8
- Task 14 (Phase 8 可观测性) 依赖 Task 2
- Task 15 (Phase 9 模板) 依赖 Task 5, Task 8
