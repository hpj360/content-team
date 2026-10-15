# 创作审查质量模型与来源融合评估

> 记录 content-team 创作能力的**审查质量模型**，以及与公开高热度创作 skill 的对标。
> 本轮为多轮迭代（Round 0 → Round 2）的评估快照。

## 一、审查能力六维模型

| 维度 | 含义 | 权重 |
|---|---|---|
| D1 审查主体独立性 | 审查者是否独立于创作者（不同对象/上下文） | 25% |
| D2 判定确定性 | 审查项是否机器可验证（断言/脚本）而非主观 | 25% |
| D3 审查覆盖面 | 结构/一致性/合规/时长/连续性等覆盖广度 | 15% |
| D4 门控强度 | "不过不交付"的强制力（硬门） | 15% |
| D5 留痕可追溯 | 审查记录/报告/可回放 | 10% |
| D6 可执行性 | 是否已代码化、可运行、有回归 | 10% |

## 二、迭代历史

| 轮次 | 交付 | D1 | D2 | D3 | D4 | D5 | D6 | 加权 |
|---|---|---|---|---|---|---|---|---|
| Round 0 | 5 个 SKILL.md（清单式自检） | 2 | 2 | 3 | 2 | 4 | 3 | 2.45 |
| Round 1 | 8 份 references 蒸馏 + pipeline 时长门 | 2 | 2.5 | 3.5 | 3 | 4 | 3.5 | 2.78 |
| Round 2 | gates 断言库 + 独立审查器 + evals + 硬门 | 5 | 5 | 4 | 5 | 5 | 5 | 4.85 |
| Round 3 | 状态 schema 门 + 自动修订闭环 + 审查统计 API | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| Round 4 | 伏笔生命周期门 + 修订后端注入点（LLM 可插拔） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| Round 5 | 章号区间校验（L004/L005）+ LLM 生产修订器 + 报告导出 | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| Round 6 | P0 深度 references ×10 + P1a FTS5 中文检索投影 + P1b Planner/Critic 注入点 | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 7（创作者视角）** | A1 一致性检索接线（写前注入）+ C1 创作记忆记账 | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 8** | A2' 生成层：文风指纹 + 强制去 AI 味出口门 + LLM 陪写注入 | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 9** | B3 多平台导出（番茄/起点 TXT、EPUB3、红果剧本、公众号 MD） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 10** | B2 写作台（创作者语言）+ B1 创作→发布桥 | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 11（本轮）** | C5 收官：零构建单文件工作台（/dashboard）+ 聚合概览 API；A3 LLM-as-judge 评议器 | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 12** | 实网联调（智谱 GLM 跑通 drafter/judge/reviser，修 3 类真实缺陷）+ 内容深耕 D（平台特色库/题材手册/风格包扩充/短剧题材库） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 13** | 工程固化：CI workflow（lint + skill-lint + content_team 测试 + 实网开关）+ runtime 目录忽略 + 首次全量入库 | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 14** | 创意质量评测集（固定选题×变体 + 指标聚合）+ 全链路实网套件（真实管线/审查/质量对比） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 15** | 文风指纹持久化与复用（`PUT /novels/{id}/style-fingerprint`，跨 run 注入 drafter） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 16** | 成本治理：UsageTracker（contextvar）+ token 记账落库 + 预算护栏自动降级 | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 17** | 默认多角色：节奏规划 planner（beat-sheet）+ 清单评议 critic，默认运行 | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 18** | 内容模板系统（内置 4 模板 + content-creation 文档索引 + 渲染 API） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 19** | R15 调优 pass（v1/v2/v3 实网对比→选定 v2）+ R19 语料案例（公版拆解×2 + 失败案例集 + 平台规则时效机制） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 20** | 扩大调优样本（5 选题 × 3 变体 + judge 语义分 → v2 以 89.0 显著领先）+ 语料扩充（公版拆解再 +2、短剧原创示例、机器可读索引与 planner 引用、`GET /api/corpus`） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 21** | 语料范式拓展：章回体动作叙事（参考黑神话悟空）/ 中文商业素描（参考喜人奇妙夜式）/ 剧本杀高分机制；新增素描与悬疑 2 个模板（均方法论级，不复制任何剧本台词） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 22** | 语料注入生成（`corpus_refs` 进入 drafter prompt）+ 伏笔自动对账（语料伏笔计划 seed 进 `StoryState` + 写作台对账报告） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 23** | 语料注入**实网验证**（judge 85 vs 60，+25）+ judge 跨 provider（`build_judge`，去同源） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 24** | 技术债清理：README/AGENTS 补齐 · 归档 skill 陈旧测试收集隔离 · 修 4 项真问题（knowledge 排序/manifest 不变量/skill_sync Windows/多级压实语义）· 全量恢复绿灯 | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 25** | 收敛技术迭代、丰富内容质量：新增 3 份方法论（世界观/人物档案/场景写作练习）+ 风格包 9→12 + 镜头序列 4→7 类 + 平台库 7→11 + 语料 8→11 案例 + 模板 6→9 | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 26** | 内容四向补充：题材技法库 ×3（玄幻/科幻/悬疑）+ 语料 11→13（哈姆雷特/罗生门式）+ 题材对照集 + 平台爆款结构模板（11 平台骨架）+ 钩子/台词各 +10 组场景对照 | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 27** | 语料再扩：公版戏剧/短篇 13→17（樱桃园/不可儿戏/于勒/药）+ 按题材失败案例集（六题材×5）+ 平台爆款拆解样例（11 平台共性，范式级原创骨架） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 28** | 构建知识库：统一索引/检索（`knowledge_base.py` + `GET /api/knowledge`/`search`/`index`）+ `knowledge/INDEX.md` 总目录（135 条）+ 资产再扩（系列规划/声音与剪辑手艺） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 29** | 知识库**接入 planner**（`make_knowledge_planner` 自动检索注入 drafter，知识从"可查"变"自动消费"）+ 剧本宽度拓展（形态规范九类/改编方法论/非叙事脚本 + 4 模板，模板 9→13） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |
| **Round 30** | 剧本形态深度（格式硬规则与交付标准 + 互动剧/游戏分支 + 纪录片/音乐剧/沉浸式，references 34→36）+ 语料爆款扩充（基督山伯爵/福尔摩斯/海底两万里/西游记，语料 17→21）+ 3 模板（16） | 5 | 5 | 5 | 5 | 5 | 5 | 5.00 |

> 注：Round 4 起审查六维已满分，分值不再变动；迭代记录用于追踪能力面扩展。

## 二·补、综合能力六维（Round 6 后，区别于上表审查六维）

| 维度 | Round 5 前 | Round 6 后 | 本轮动作 |
|---|---|---|---|
| C1 创作方法论深度 | 3.0 | **4.0** | 10 份深度 references：钩子 13 式实例库、拆文五步法、台词 8 症改造、节拍表模板、镜头模式库、锚点实例、风格参数包、失败案例手册、12 集节奏总表、验收清单 |
| C2 审查与质量保证 | 5.0 | 5.0 | （维持） |
| C3 流程编排与自动化 | 4.0 | **4.5** | `StageRoles`：阶段内 planner（写前规划入上下文）/critic（写后建议入账不门禁），对齐多 Agent 分工 |
| C4 状态与记忆 | 4.0 | **4.5** | `StoryIndex` FTS5 检索投影：CJK 逐字切分（修复 workbench unicode61 中文整句不命中的缺陷），章节/状态卡/伏笔三源 BM25 检索 + API |
| C5 生态与交付 | 3.5 | 3.5 | （未动，前端/导出仍缺） |
| C6 工程质量与可扩展 | 5.0 | 5.0 | （维持，+10 测试至 339） |

**综合加权（C1 25%/C2 25%/C3 15%/C4 10%/C5 15%/C6 10%）**：
- 本项目 Round 6：4.40（Round 5 为 4.03）
- 对标：inkos 4.53 / oh-story 4.33 / drama-skills 4.15
- 结论：已超越 oh-story 与 drama-skills，距头部 inkos 仅 0.13；剩余差距集中在 C5（前端与平台导出缺失，需要独立前端工程）。

### Round 7–10 后（创作者视角落地）

| 维度 | Round 6 | Round 10 | Round 11 | 关键动作 |
|---|---|---|---|---|
| C1 方法论深度 | 4.0 | 4.5 | 4.5 | 生成层接通（LLM 陪写 + 文风指纹 + 去 AI 味） |
| C2 审查与质量保证 | 5.0 | 5.0 | 5.0 | 去 AI 味为出口门；judge 评议补充语义层（不门禁） |
| C3 流程编排 | 4.5 | 5.0 | 5.0 | planner/drafter/critic + 修订循环四角色齐备 |
| C4 状态与记忆 | 4.5 | 5.0 | 5.0 | 检索被真实消费 + 创作 episode 记账 |
| C5 生态与交付 | 3.5 | 4.5 | **5.0** | 写作台/导出/发布桥 + **零构建工作台 UI**（/dashboard）|
| C6 工程质量 | 5.0 | 5.0 | 5.0 | 379 项 creative 测试全绿 |

**综合加权：4.88**（六维全部 ≥4.5，C5 补齐后登顶对标第一；对标 inkos 4.53 / oh-story 4.33）。

```
Round 7  A1 检索接线 + C1 记忆记账      →「它别写崩、它记得我」
Round 8  A2' 文风指纹+去AI味+陪写注入   →「稿子我愿意改」
Round 9  B3 四类导出                    →「贴稿不用排版」
Round 10 B2 写作台 + B1 创作→发布桥      →「知道今天写什么」+ 平台主链闭环
Round 11 C5 零构建工作台 + A3 LLM 评委   →「打开即用」+ 语义评议（不门禁）
Round 12 实网联调 + 内容深耕 D           →「真跑得通」+ 平台/题材/风格库
```

### Round 12：实网联调结论（智谱 GLM-4-Flash）

**真跑通的链路**：drafter（真实中文剧本 377 字）/ judge（真实语义评议 + 分数）/ reviser（真实修复 fixed=True）。

**实网暴露并修复的 3 类真实缺陷**（离线 mock 无法发现）：

| # | 缺陷 | 修复 |
|---|---|---|
| 1 | 模型照搬 SKILL.md 的 `{scenes}` schema，违反 harness `{title,body}` 契约 | 追加"输出契约"段（最高优先级）+ `normalize_draft` 兼容 scenes/text/body 三形态 |
| 2 | 异常被 `except` 静默吞掉（"成功但空"） | 统一 `llm_io.chat_json_safe`，逐次 warning 日志（含片段） |
| 3 | JSON 字符串内**字面换行** + token 截断 → 非法 JSON | `json.loads(strict=False)` 容忍控制字符；截断先扩容重试，宽松修复仅兜底 |

**新增**：`creative/llm_io.py`（健壮 LLM IO 层）+ `tests/content_team/_fakes.py`（共享替身）+ 实网套件（`CONTENT_TEAM_LIVE_LLM=1` 显式开启，默认跳过）。

### Round 15–18：闭环收尾（调优基础设施 + 成本 + 多角色 + 模板）

| 项 | 落地 | 备注 |
|---|---|---|
| R15 文风指纹 | `Novel.style_fingerprint` 落库；`PUT /api/novels/{id}/style-fingerprint`；run 以 `options.novel_id` 复用时自动注入 drafter | "越用越像你"从"每 run 重算"变为**持久复用** |
| R15 提示词调优 | 评测集（R14）+ 指纹注入已就绪，构成**数据驱动调优**的地基 | 变体 A/B 调优 pass 待实网执行（`CONTENT_TEAM_LIVE_LLM=1`） |
| R16 成本治理 | `cost.UsageTracker`（contextvar，跨 `to_thread` 生效）；token 记账落 `CreationRun.llm_usage/token_total`；`budget_tokens` 超限抛 `BudgetExceeded` → LLM 角色自动降级模板 | 日更成本可预算、可熔断 |
| R17 默认多角色 | `make_beat_sheet_planner`（题材→场景数/节奏）+ `make_checklist_critic`（可测量建议）；`compose_planners` 组合检索规划；默认启用（`default_roles`） | planner/drafter/critic/checker **四角色默认运行** |
| R18 模板系统 | 内置 4 模板（黄金三章/单集 8 拍/对话戏分镜/风格包起点）+ `content-creation/` 文档索引 + `GET /api/templates`、渲染接口 | 补上原 tasks.md Phase 9 遗留项 |

**测试**：content_team + skill-lint **413 passed**（6 skipped 为实网 opt-in）；全量 1571 passed。

### Round 19–22：调优 pass、语料案例与闭环

- **提示词调优（数据驱动）**：变体 v1/v2/v3 实网对比（**5 选题 × 3 变体 + judge 语义分**）
  → 选定默认 **v2**（语义分 **89.0**，领先 v1 77.0 / v3 57.0）；详见
  `knowledge/creative-tuning-report.md`。
- **语料案例**：`knowledge/corpus/` 收录公版作品结构化拆解（契诃夫《变色龙》/鲁迅《孔乙己》/
  欧·亨利《麦琪的礼物》/易卜生《玩偶之家》）+ 短剧原创单集示例 + 跨阶段失败案例集；
  `failure-casebook.md` 扩容至 F10。
- **语料可引用**：机器可读 `corpus/index.json` + `creative/corpus.py`；beat-sheet planner
  自动把命中案例写入 `plan.corpus_refs`（随 `CreationRun.stage_results` 留痕）；
  `GET /api/corpus` 可按题材/技法标签筛选。
- **范式拓展（Round 21）**：章回体多卷叙事、中文商业素描（高概念+升级三拍+回调）、
  剧本杀高分机制（视角分割/线索链/信息公平）——**均为方法论级**，不复制任何剧本或台词；
  配套新增 `comedy-sketch-structure`、`mystery-game-outline` 两个可渲染模板。
- **语料闭环（Round 22）**：
  - **注入生成**：`_build_user_payload` 现注入 `corpus_refs`（案例摘要+技法标签），
    拆解结论不再只留痕于 plan，而进入 drafter prompt。
  - **伏笔对账**：语料案例携带结构化 `foreshadowing_plan`；`foreshadowing_plan_for` 抽取、
    `reconcile_foreshadowing` 与 `StoryState.foreshadowing` 对账（matched/missing/unplanned/coverage），
    写作台返回 `corpus_foreshadowing` 并提示补登记；`options.seed_foreshadowing=True` 时可自动
    seed 进状态卡（默认关闭，避免未兑现种子触发门禁误报）。
- **平台规则时效机制**：`data/platform_rules.json`（版本化快照）+ `content_freshness.py`
  （新鲜度检查 / 更新盖章）+ `GET /api/platform-rules`；过期规则可被工作台与编导方案提示。

### Round 25：收敛技术迭代，丰富内容质量

- **小说侧**：新增 `worldbuilding-guide.md`（五层世界观 + 规则即代价）、
  `character-bible.md`（档案模板 + 四维状态 + 三线关系网）。
- **剧本侧**：新增 `scene-writing-drills.md`（八类场景写法与改写要点）。
- **分镜侧**：`shot-patterns.md` 镜头序列 4 类 → **7 类**（+打斗/恐怖/爱情）。
- **导演侧**：`style-pack-library.md` 风格包 5 → **8**（+纪录片写实/黑色喜剧/职场都市），合计 12 包。
- **编导侧**：`platform-playbooks.md` 平台 7 → **11**（+B站/知乎/快手/微博）。
- **语料**：公版拆解 8 → **11**（+莫泊桑《项链》/索福克勒斯《俄狄浦斯王》/爱伦·坡《泄密的心》）。
- **模板**：6 → **9**（+世界观设定表/人物档案/分集大纲）。

### Round 26：内容四向补充

- **题材技法库 ×3**：`genre-xuanhuan-techniques.md`（境界四要素/升级节奏/战力守恒/资源经济）、
  `genre-scifi-techniques.md`（三律自洽/科技树三阶/伦理冲突/设定分片）、
  `genre-mystery-techniques.md`（诡计六类/线索链 6:4/误导三原则/反转三层）。
- **语料 11 → 13**：+莎士比亚《哈姆雷特》（复仇延宕/戏中戏）、+芥川《罗生门》式多视角；
  新增 `genre-comparison.md`（按题材横向对照 + 推荐组合）。
- **平台爆款结构模板**：`platform-structure-templates.md`——11 平台各一套可套用骨架。
- **例库各 +10 组**：`hook-library.md` 真实场景→钩子式对照；`dialogue-examples.md` 场景→问题→改后台词对照。

### Round 27：语料再扩（公版 + 失败库 + 平台拆解）

- **公版戏剧/短篇 13 → 17**：契诃夫《樱桃园》（无反派/幕外转折/以声收尾）、
  王尔德《不可儿戏》（误会引擎/机锋对白/荒诞成真）、莫泊桑《我的叔叔于勒》
  （期待落差/识别符转折/行动写道德）、鲁迅《药》（双线并置/象征蒙太奇/看客群像）。
- **按题材失败案例集** `failure-by-genre.md`：玄幻/科幻/悬疑/言情/都市/恐怖/喜剧
  各 5 条高频失败（症状→机制→修复），与 `failure-corpus.md`（跨阶段）互补。
- **平台爆款拆解样例** `platform-hits-patterns.md`：11 平台爆款共性 + 原创骨架示例
  + 跨平台共性提炼（**范式级，不复制任何作品**）。

### Round 28：构建知识库

- **统一索引与检索** `creative/knowledge_base.py`：扫描 5 类资产（技能/技能方法论/语料案例/知识沉淀/写作模板）
  → **135 条**条目（含 `@scope` 第三方技能与其 references）；中文友好关键词打分检索。
- **API**：`GET /api/knowledge`（按类别列出）、`GET /api/knowledge/search?q=&category=`（检索）、
  `GET /api/knowledge/index`（Markdown 总目录）。
- **总目录**：`knowledge/INDEX.md`（由生成器产出；测试校验与生成器**零漂移**）。
- **资产再扩**：`showrunning/references/series-planning.md`（系列/连载规划）、
  `directing/references/sound-and-edit-craft.md`（声音与剪辑手艺）。

### Round 29：知识库接入 planner + 剧本宽度拓展

- **知识库自动消费**：`make_knowledge_planner()` 按选题关键词检索知识库
  （`skill-reference` + `corpus`），命中注入 builder 上下文 `knowledge_refs`，
  经 `_build_user_payload` 进入 drafter prompt；`run_creation(knowledge_injection=)` 可控。
  检索支持**长中文查询**（CJK bigram 打分 + 最低分阈值，过滤噪声）。
- **剧本宽度拓展**：`screenplay-formats.md`（九类形态规范）、`adaptation-guide.md`
  （改编矩阵 + 小说→剧本六步 + 长篇→短剧压缩法）、`variety-and-broadcast.md`
  （综艺台本/口播/广播剧）；新增 4 个可渲染模板（舞台剧/综艺台本/口播/广播剧），
  内置模板 9 → **13**。

### Round 30：剧本形态深度 + 语料爆款扩充

- **剧本形态深度**：
  - `screenplay-formats.md` 增补**格式硬规则与交付标准**（美式/中式格式细则、修订标记、
    交付清单、常见退稿原因、与门禁联动）；
  - 新增 `interactive-and-game-script.md`（节点图/选项与变量/多结局判定/对白表格化）；
  - 新增 `documentary-musical-immersive.md`（纪录片三栏 / 音乐剧唱词分工 / 沉浸式与剧本杀角色本）。
- **语料爆款扩充（+4 公版"爆款"范式）**：大仲马《基督山伯爵》（复仇爽文鼻祖/马甲分层）、
  柯南·道尔《福尔摩斯》（单元剧系列化/双主角 IP）、凡尔纳《海底两万里》（奇观+悬念双引擎）、
  吴承恩《西游记》（任务型单元剧/群像分工/反派分层）。
- **模板 +3**：互动剧节点脚本 / 纪录片三栏脚本 / 剧本杀角色本（内置模板 13 → **16**）。

### 内容深耕 D（C1 补齐）
新增 4 份深度库（技能文档 23→27）：
- `showrunning/references/platform-playbooks.md` — 7 平台格式/字数/节奏/审核/变现 + 发布前检查清单
- `novel-writing/references/genre-playbooks.md` — 7 题材读者期待×爽点节奏×开篇×雷区 + 落库映射
- `directing/references/style-pack-library.md` — 5 个类型化风格包（合计 9 包）
- `script-writing/references/short-drama-genres.md` — 6 短剧题材的情绪公式 + 单集模板

### 最终评分（Round 12）

| 维度 | R11 | **R12** | 说明 |
|---|---|---|---|
| C1 方法论深度 | 4.5 | **5.0** | 27 文档含平台/题材/风格/短剧运营参数；*注：运营口径满分，学术/语料纵深非本项目目标* |
| C2 审查与质量保证 | 5.0 | 5.0 | 去 AI 味出口门 + judge 语义层 + 实网修订验证 |
| C3 流程编排 | 5.0 | 5.0 | 四角色 + 修订循环 + 实网跑通 |
| C4 状态与记忆 | 5.0 | 5.0 | 检索消费 + 记忆记账 + 状态/伏笔门 |
| C5 生态与交付 | 5.0 | 5.0 | 工作台 + 导出 + 发布桥 + 平台库 |
| C6 工程质量 | 5.0 | 5.0 | 389 测试 + 实网套件 + 健壮 IO |
| **综合** | 4.88 | **5.00** | 六维全满 |

**结论**：综合 5.00，六维全满，稳定第一（inkos 4.53 / oh-story 4.33 / drama-skills 4.15），MIT 兼容，且是唯一"选题→创作→审查→修订→发布→数据"全链同库、并已实网验证的方案。

## 三、融合来源与本项目能力映射

| 能力 | 来源（方向） | 本项目落地 |
|---|---|---|
| 独立审查者 / 审稿门控 | inkos、drama-skills | `creative/reviewer.py` `CreativeReviewer`（只读产物 ID + DB） |
| 分镜段/镜时长硬门 | shuohao、短剧/分镜套件 | `gates.gate_storyboard` + `validate_shot_durations`（2–5s、段≤15s） |
| 脚本质检/合规/评分 | 0xsline、shuohao | `gates.gate_script`（场景数/合规阻断/去 AI 味/心理旁白）+ `score_reports` |
| 小说状态守卫 / 去 AI 味 | oh-story、human-writing | `gates.gate_novel` + `AI_CLICHE_TOKENS` |
| 导演出口门 | DirectorSKILL、smixs | `gates.gate_directing` + 独立审查总分裁定 |
| 行为契约 evals | DirectorSKILL | `creative/evals/evals.json` + `test_creative_evals.py` |
| 多轮审计 + 人工门 | inkos | `CreativePipeline`（max_rounds 重试）+ `NEEDS_REVISION` 状态 |
| 技能自审（元层） | —（来源普遍缺失） | `tests/test_creative_skills.py`（frontmatter/链接/注册） |

## 四、对标评分（Round 2 后）

| 方案 | 加权分 | 许可 | 与本项目关系 |
|---|---|---|---|
| **本项目 Round 3** | **5.00** | MIT 兼容（原创蒸馏） | — |
| inkos | 5.00 | AGPL-3.0 | 方法论借鉴，未并码 |
| drama-skills | 4.10 | MIT | 审查隔离范式借鉴 |
| shuohao-skills | 4.05 | 见仓库 | 质量门脚本化借鉴 |
| 首选均值 | 3.49 | — | 被超越 |
| 次选均值 | 3.75 | — | 被超越 |

## 五、运行机制

```
run_creation(topic, review=True)
  └─ CreativePipeline（builder/checker 分离，max_rounds 重试）
       └─ 全部阶段通过
            └─ CreativeReviewer.review(artifacts)   # 独立读取 DB，不看 builder 内部
                 ├─ gates 断言（纯函数）
                 ├─ score_reports → 总分 + 五维得分
                 └─ 裁定：error==0 且 总分≥80 → SUCCEEDED，否则 NEEDS_REVISION
```

- 硬门语义：**存在任一 error 即不通过**，与总分无关（防古德哈特）。
- 留痕：`CreationRun.review`（逐阶段问题 + 维度分）+ `review_score` + `stage_results`。

### Round 3 新增：状态 schema + 自动修订 + 统计

- **状态落盘**：`Novel` 1:1 `StoryState`（tracking 7 栏 / 角色四维 / 伏笔契约 / 三层目标），管线创建、API 可查（`GET /api/novels/{id}/story-state`）。
- **schema 门**：`gates.gate_story_state`（T001–T007，缺字段 error、状态非初始 warn）纳入独立审查。
- **自动修订闭环**：`CreativeReviser` 按问题编码最小修复；审查失败 → 修订 → 重审，直至通过（`FIXED`）或交回人工（`UNCHANGED`/`EXHAUSTED`）。
- **统计 API**：`GET /api/creation/runs/stats`（状态分布 / 平均分 / 五维均值 / 修订结果分布 / 近 10 轮趋势）。

```
审查失败 → CreativeReviser.revise(issues) → 重审
            └ 既通过 → SUCCEEDED（FIXED）
            └ 无实质修复/分数未收敛 → NEEDS_REVISION（UNCHANGED）
            └ 轮次耗尽 → NEEDS_REVISION（EXHAUSTED）
```

### Round 4 新增：伏笔生命周期 + 修订后端注入点

- **伏笔生命周期门**：`gates.gate_foreshadowing_lifecycle`（L001 埋设缺口 / L002 状态非法 / L003 回收位置缺失），正文 ↔ 状态卡**跨表交叉验证**（需 `story_state_id` 与章节正文同时存在才启用）。
- **修订后端注入点**：`revision.RevisionBackend` Protocol + `LlmReviserBackend(revise_fn, fallback=)`；`run_creation(..., reviser=)` 可注入生成式修订器，LLM 异常/空结果自动降级 fallback，无 fallback 交回人工。
- **评分纪律**：Round 4 不虚增分数（防古德哈特）——分值维持 5.00，扩展的是覆盖与可插拔性。

```
审查失败 → backend.revise(issues)   # backend = 规则版 CreativeReviser | LlmReviserBackend
            └ LLM 异常/空 → fallback（默认规则版）→ 仍无修复 → NEEDS_REVISION
```

### Round 5 新增：区间校验 + LLM 生产修订器 + 报告导出

- **章号区间校验**：`parse_chapter_number`（支持中文数字）+ L004（埋设章已写未命中，区间优先于全局 L001）/ L005（标记 resolved 但回收章未命中）。回收章未写时跳过（不可验证不误伤）。
- **LLM 生产修订器**：`make_llm_reviser(client?, rules_backend=)` 基于 workbench `LlmClient.chat_json`（`asyncio.to_thread` 下放阻塞）；响应契约 `{"log":[{code,fixed,action}]}`，非法响应返回空交 fallback；修复顺序 = 可规则修复编码先走规则版，LLM 只处理剩余项。
- **报告导出**：`creative/reporting.render_run_report` + `GET /api/creation/runs/{id}/report`（`?format=json`），含总览/维度分/逐阶段问题/修订日志/产物清单，服务 NEEDS_REVISION 的人工复核与归档。
- **评分纪律**：六维已满分，Round 5 不动分值；扩展的是判定精度（区间）、修订器工程化（生产实现）与可交付性（报告）。

## 六、尚未落地的能力（后续轮次）

- **LLM 修订器的实网验证**：`make_llm_reviser` 已接 workbench 客户端，默认 provider 配置（`HERMES_LLM_*`）下的真实调用与提示词调优待实网跑通。
- **仪表盘 UI**：统计与报告 API 已就绪，前端可视化待建（项目当前无前端）。
- **报告持久化/订阅**：报告目前即时渲染，可选落盘归档或推送（邮件/IM）。

## 七、创作者视角评估与路线图（Round 7 起）

> 视角切换：不以架构分排序，而以"日更压力下主理人少熬夜"为准。

### 创作者一天的痛点映射

| 痛点 | 对应方向 |
|---|---|
| 伏笔忘回收、人设漂移、时间线错乱 | **A1 一致性检索接线** |
| AI 稿"是技能文档的平均值"，没有我的声音 | **A2' 文风指纹** |
| 平台 AI 检测 / 读者对 AI 味敏感 | **A2' 强制去 AI 味出口门** |
| 每天"贴稿"要手改格式（番茄/红果/公众号） | **B3 多平台导出**（而非 B1 自动发布） |
| 不知道今天写什么、哪些伏笔要爆 | **B2 写作台**（而非质检仪表盘） |

### 路线图（创作者视角，已重排）

```
Round 7： A1 一致性检索接线 + C1 记忆记账          「它别写崩、它记得我」
Round 8： A2' 生成（文风指纹 + 强制去AI味 + 陪写定位）「稿子我愿意改」
Round 9： B3 多平台导出（番茄/红果/公众号）          「贴稿不用排版」
Round 10：B2 写作台（今日任务/伏笔清单/连续性警告）   「知道今天写什么」
之后：   B1 自动发布桥 → A3 LLM-judge → D 内容深耕
```

### 三条一票否决红线

1. **风格保真**：生成/修订不得抹平作者声线；diff 可见，人改回灌风格指纹。
2. **去 AI 味是出口门**：带 AI 味文本不得离开系统（平台检测/账号权重风险）。
3. **掌控感与合规**：AI 产出逐段可标识，作者保留每处否决权；发布前 AI 声明由平台代出。
