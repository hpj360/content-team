# 工作法蒸馏溯源（2026-11-08，R44）

> 目的：把 `content-creation/novel/` 里实战长出来的工作法（22–27 号）**蒸馏进仓库 references**，
> 消除"两套方法长期分叉"的风险，并留下"来源 → 目标 → 保留/合并/丢弃"的追溯记录。
> 原则：**只搬方法论增量**；与既有 references 重复的只保留交叉引用；具体作品设定与正文不入库。

> **定位**：工作法蒸馏溯源账本（来源 → 提炼 → 落点 → 处理方式）。
> **受众**：维护 references、追溯某条工作法出处的人。
> **权威口径（SSOT）**：工作法来源→落点映射以本表为准；质量模型中的 R44 记录仅做摘要指针。
> **不做什么**：不收录具体作品设定/正文；不重复 references 正文（重复内容只留交叉引用）。

## 一、映射总表

| 源文件（content-creation/novel/） | 提炼出的方法论 | 目标落点 | 处理方式 |
|---|---|---|---|
| `22-场景连续性工作法.md` | 三型跳跃诊断（章内冷切/世界级跳/案域跳）、转场七法（尾词复现·物件接力·声音桥·行走过渡·时间铆钉·回环句·制式桥）、分隔符纪律、章间/卷级桥三标配 | `skills/novel-writing/references/chapter-continuity.md` | 保留核心，过渡分类改为引 `scene-engineering.md` |
| `23-叙述连贯性工作法.md` | 叙述连贯五层（视角/信息/因果/支线/语感）、语者恒定（三句式正字法）、半句定理、补票法、支线预算 6:3:1、五道门口径 | 同上 | 保留；视角/距离理论部分改引 `narratology-toolbox.md` |
| `16-章节体量标准V3.md` | 章节体量 3600–3900 字、序章 1500、结构配额、呼吸位 | 同上（第五节） | 合并为"体量与呼吸"一节 |
| `27-写作方法落地-章节修订日志.md` | 修订归因台账格式（位置/修订/所用法条/性质/归因效果） | 同上（第六节） | 只提炼**格式**，具体 11 笔修订不入库 |
| `24-勘察组规则体系.md` | 规则三构成（触发/禁忌/后果）、两属性（不可协商/只约束在场者）、执法者位、条目清单卷宗体、正文植入位 ≤2 句 | `skills/novel-writing/references/rule-horror-techniques.md` | 保留结构法；鬼楼七条案例判词不入库 |
| `25-理解成本优化-规则的呈现改造.md` | 理解成本转移三定律 + 七条落地（术语免费期/一次一教/先后果/砍名留物/边缘注释/重复锚/延迟定义） | 同上 | 保留；三级渐进并入第二节披露表 |
| `00-资产总览.md`、`11-生产配方与正典名录.md` | AIGC 配方结构（人物立绘/出图模板）、正典名录合并法 | 暂不入库 | 属生产管线而非写作方法论；待后续"图/漫剧工作流"轮次处理 |

## 二、去重对照（重复内容只留交叉引用）

| 被去重的内容 | 已有归属 |
|---|---|
| 过渡四类（硬切/桥接/并置/叠化） | `skills/script-writing/references/scene-engineering.md` |
| 视角/距离/时序/速度五档、四维联动清单 | `skills/novel-writing/references/narratology-toolbox.md` |
| 拍长、节拍表、时长折算 | `skills/script-writing/references/beat-sheets.md` |
| 黄金三章、钩子 13 式、去 AI 味清单 | `skills/novel-writing/references/web-fiction-craft.md` |
| 伏笔/时间线/角色状态台账 | `skills/novel-writing/references/story-state-and-continuity.md`（"那张表记坑、本篇台账记改动"） |
| 规则即代价、五层世界观、能力层级 | `skills/novel-writing/references/worldbuilding-guide.md` |
| 诡计六类、线索链 6:4、真凶防空降 | `skills/novel-writing/references/genre-mystery-techniques.md` |
| 规则卡视听化、两分钟内核、分支回收 | `knowledge/corpus/paradigm-vertical-interactive.md`、`breakdown-fanxiangzhidi.md` |
| 锚点/识别符逐字复用纪律 | `skills/storyboarding/references/continuity-anchor-examples.md` |

## 三、蒸馏后未消化的存量（后续可做）

1. `11-生产配方与正典名录.md` 的 **AIGC 出图配方骨架**（人设立绘/场景图/负面清单）——属"图文双载体生产"，可另立一份 references（与 `ai-video-storyboard-prompting.md` 互补）。
2. `00-资产总览.md` 的**资产一致性审查报告法**（15 号）——与 `revision-diagnosis.md` 有交集，可做"跨文档资产对账"小节。
3. 22 号"转场七法"目前只在小说侧；`skills/storyboarding/references/edit-rhythm-and-transition.md` 里的转场四类是影视线性口径——后续可补一张"文学转场 ↔ 影视转场"对照表。

## 四、校验

- 两篇蒸馏文件已登记 `skills/novel-writing/SKILL.md` 方法论参考清单；
- 契约测试 `tests/content_team/test_creative_methodology_r44.py` 覆盖：七法/五层/三构成/三级披露/七条落地/去重交叉引用/手册可操作性；
- 使用手册 `knowledge/usage-writing-with-content-team.md` 已把两篇纳入"连续性层"与决策速查表。
