# Checklist

## Hermes 剩余能力移植

- [x] 三层记忆系统已集成，content_team 可写入/读取 L1 facts、L2 episodes、L3 profile
- [x] MemoryService 在 app 启动时初始化为单例
- [x] Topic 创建/评分时自动写入 memory episode
- [x] 结构化日志已启用，日志输出为 JSON 格式，包含 timestamp/level/trace_id/event 字段
- [x] API 请求自动生成 trace_id 并通过 log_context 传播到下游
- [x] 崩溃恢复管理器在进程启动时执行 recover()，QUEUED 任务重入队、RUNNING 标记 ABANDONED
- [x] Cron 定时触发器可解析标准 Cron 表达式并创建 ScheduledJob
- [x] 每日数据采集触发器和定时发布触发器已注册
- [x] content-creation 目录已移植，冷启动计划已解析为结构化模板
- [x] skill-creator 已从 _archive 提升为活跃 skill
- [x] manifest.json 已更新活跃/归档 skill 列表

## 一期功能实现

- [x] AC-1: 用户可创建选题卡片，选题池中可见
- [x] AC-2: 用户可在富文本编辑器中创建图文内容，保存草稿，查看历史版本
- [x] AC-3: 用户可绑定微信公众号/视频号/抖音/小红书/B站账号
- [x] AC-4: 用户可选择已完成内容一键分发到目标平台
- [x] AC-5: 用户可查看已发布内容在各平台的核心数据
- [x] AC-6: 团队成员可共享选题池，查看和领取选题
- [x] AC-7: 用户可设置定时发布，到时间自动推送
- [x] AC-8: 选题评分模型可基于输入参数给出推荐分数

## 后续迭代

- [ ] Phase 5: AI 选题推荐可调用 LLM 生成建议并去重
- [ ] Phase 5: AI 写作辅助可调用 LLM 生成内容并质量评估
- [ ] Phase 6: 内容审核 builder 可生成检查项（敏感词、格式、字数）
- [ ] Phase 6: 内容审核 checker 可逐项验证，通过自动放行，失败标记待人工
- [ ] Phase 7: 灵感检索 API 可基于 TF-IDF + 余弦相似度返回关联选题
- [ ] Phase 7: 用户擅长领域画像可从历史行为自动更新
- [ ] Phase 8: 全链路 trace_id 可从 API 传播到 Scheduler 到 Adapter
- [ ] Phase 8: 结构化日志可按 trace_id/event/platform 筛选
- [ ] Phase 9: 模板系统可加载冷启动计划模板
- [ ] Phase 9: 编辑器可预填充模板框架

## 架构约束

- [x] content_team 子包未修改 hermes core 代码
- [x] 所有 hermes 模块通过依赖注入接入，非硬编码
- [x] content_team 的数据模型独立于 hermes workbench 模型
- [x] 定时任务复用 hermes scheduler，未自行实现调度逻辑
- [x] 发布编排复用 hermes scheduler/triggers，定时发布通过 Cron 触发器实现
