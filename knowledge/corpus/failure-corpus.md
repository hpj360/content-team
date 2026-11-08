# 失败案例集（跨阶段）

> 汇总**跨阶段**的失败模式（症状 → 机制 → 修复），与 `skills/directing/references/failure-casebook.md`
> 的 F 编码互补：本文件偏**叙事/流程**层，F 编码偏**生成/镜头**层。
> 按 `case-breakdown.md` 的"失败记录"要求沉淀，避免重复踩坑。

## 失败编码总索引

| 编码 | 适用层 | 入口文件 |
|---|---|---|
| F1–F10 | 导演/风格层 | `skills/directing/references/failure-casebook.md` |
| SB1–SB8 | 分镜/镜头层 | `skills/storyboarding/references/storyboard-failure-casebook.md` |
| N-FAIL/P-FAIL | 叙事/流程层 | 本篇 |
| V-F1–V-F10 | 竖屏剧集/转化层 | `failure-vertical-drama.md` |
| AI-F1–AI-F10 | AI 生成内容层 | `failure-ai-drama.md` |
| ST/SC/SE 标红信号 | 稿件诊断层 | `skills/script-writing/references/revision-diagnosis.md` |

同层找对应入口；新增失败库须先在此登记。

## 一、叙事层

### N-FAIL-1 挖坑不填

- **症状**：读者反馈"作者忘了那个信物/伏笔"。
- **机制**：伏笔只存在于作者脑中，未落 `StoryState.foreshadowing`。
- **修复**：所有伏笔登记 `id/content/planted_at/planned_resolution/status`；
  `gate_foreshadowing_lifecycle`（L001/L004/L005）在埋设章与回收章做跨表校验。

### N-FAIL-2 人设漂移

- **症状**：主角性格在中段突变，读者不认。
- **机制**：角色状态未落盘，长篇跨会话丢失。
- **修复**：角色四维状态（能力/心理/关系/目标）逐卷记录；`gate_story_state` 校验完整性。

### N-FAIL-3 节奏塌陷

- **症状**：连续 4+ 章没有爽点，追读断崖。
- **机制**：只有"压"没有"还"，欠—还结构断裂。
- **修复**：拆文统计"压:爆比"（健康区间约 2:1–3:1）；连续受压不超过 3 章。

## 二、流程层

### P-FAIL-1 AI 味外泄

- **症状**：平台判定 AI 内容 / 读者吐槽"一股 AI 味"。
- **机制**：生成文本未经去 AI 味 pass 直接发布。
- **修复**：去 AI 味是**出口门**（落库前强制，`deai.apply_de_ai_pass`）；
  `gate_script` 的 S005/S006 双检。

### P-FAIL-2 幻觉设定

- **症状**：模型写出与既有设定冲突的情节。
- **机制**：写时不提供既有上下文（无检索、无状态注入）。
- **修复**：A1 一致性检索接线——写前把状态卡/待回收伏笔/近章摘要注入 builder
  （`make_retrieval_planner`）。

### P-FAIL-3 格式不达标

- **症状**：稿子贴到平台要重新排版，或超字数被截断。
- **机制**：生成时未绑定平台规格。
- **修复**：按平台库（`platform-playbooks.md`）设定字数/节奏；
  导出走 `creative/exporters.py`（分章 TXT/EPUB/红果剧本）。

### P-FAIL-4 预算失控

- **症状**：批量生成把 token 额度跑光。
- **机制**：无用量记账与熔断。
- **修复**：`cost.UsageTracker` 记账 + `budget_tokens` 护栏；超限 LLM 角色自动降级模板。

## 三、沉淀规范

新增失败案例时补齐四段：**症状 / 机制 / 修复 / 复发条件**，
并在修复落点标注对应的门禁编码或模块（便于回归验证）。
