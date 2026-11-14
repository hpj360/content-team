# 技能总图（Skills Map）

> 作用：回答"**这个任务该用哪个技能**"。本文件是技能的**唯一路由入口**（不是技能本体，
> 不参与技能发现/加载）。方法论路由见 `knowledge/asset-map.md`；全量资产目录见 `knowledge/INDEX.md`。
> 最近核对：2026-11-14（R51 技能整合批次）。共 25 个技能目录 = 5 创作 + 14 继承 + 6 外部 scope。

## 一、创作技能（本项目核心，5 个）

| 技能 | 职责（一句话） | 触发词（节选） | 上游/下游 |
|---|---|---|---|
| [novel-writing](novel-writing/SKILL.md) | 小说创作：构思/写作/续写/改写/评估 | 小说、大纲、人物小传、章节、世界观、开篇钩子 | 下游 → script-writing |
| [script-writing](script-writing/SKILL.md) | 剧本创作：电影/短剧/舞台/综艺/互动等形态 | 剧本、分场、台词、三幕、短剧、分集 | 上游 ← novel-writing；下游 → storyboarding |
| [storyboarding](storyboarding/SKILL.md) | 分镜设计：剧本 → 镜头表（景别/运镜/时长） | 分镜、镜头、景别、运镜、机位、shot list | 上游 ← script-writing；下游 → directing/视频生成 |
| [directing](directing/SKILL.md) | 导演：整体呈现、表演指导、场面调度、风格包 | 导演、导演阐述、视听风格、剪辑节奏 | 上游 ← 剧本/分镜；横切单集 | 
| [showrunning](showrunning/SKILL.md) | 编导：整季/整部策略、栏目设计、多平台运营 | 编导、总编导、内容统筹、分集节奏、系列规划 | **横切统筹**全部创作技能（多集/多平台） |

**创作链**：`novel-writing → script-writing → storyboarding → directing`（线性加工），
`showrunning` 在整季/整平台层横切调度。五技能之间以 SKILL.md「Related skills」互为边界声明，
references 不跨技能重复（映射见 `knowledge/method-distillation-log.md`）。

内部分工速查（与 `knowledge/asset-map.md` 一致）：
- 结构/拍位 → script-writing 的 `beat-sheets`（唯一权威）
- 场景判定/素材/细节 → script-writing `scene-engineering` / `scene-writing-drills` / novel `scene-detail-engineering`
- 叙述原理 → novel `narratology-toolbox`；章际 → novel `chapter-continuity`
- 事件弧 → novel `event-conflict-arc`；情感/冲突 → novel `emotion-conflict-externalization`
- 风格包 → directing `style-pack-library`（12 包全库）；分镜镜头 → storyboarding `shot-patterns`

## 二、继承技能（14 个，来自 hermes fork，非创作链）

### 2.1 检索与信息（5 个——选型规则见下）
| 技能 | 用途 |
|---|---|
| [brave-search](brave-search/SKILL.md) | Brave API 搜索 + 页面内容提取（**默认搜索**） |
| [tavily-search](tavily-search/SKILL.md) | Tavily API 搜索（AI 优化结果；需要"直接可用的摘要式结果"时用） |
| [research](research/SKILL.md) | 后台研究 agent：读源码/文档/issue 深挖一个研究问题 |
| [agent-browser](agent-browser/SKILL.md) | 浏览器自动化：需要**交互**的页面（登录/点击/渲染后内容） |
| [summarize](summarize/SKILL.md) | 对**单个** URL/文件（PDF/音视频/YouTube）做摘要 |

**选型规则（避免五选一混乱）**：
1. 普通查资料 → `brave-search`；要 AI 友好摘要 → `tavily-search`；
2. 深挖代码库/文档、需要多跳阅读 → `research`；
3. 页面必须交互才能取 → `agent-browser`；
4. 已有具体链接/文件要摘要 → `summarize`（**不要**先搜索再摘要）。

### 2.2 平台阅读器（3 个——按 URL 域路由）
| 技能 | 适用域 |
|---|---|
| [wechat-reader](wechat-reader/SKILL.md) | `mp.weixin.qq.com` 公众号文章 |
| [douyin-reader](douyin-reader/SKILL.md) | `douyin.com` / `v.douyin.com` 抖音视频转文字 |
| [youtube-watcher](youtube-watcher/SKILL.md) | YouTube 字幕/转录摘要 |

### 2.3 协作与项目（3 个）
| 技能 | 用途 |
|---|---|
| [notion](notion/SKILL.md) | Notion 页面/数据库/块 API |
| [trello](trello/SKILL.md) | Trello 看板/列表/卡片 REST API |
| [product-manager](product-manager/SKILL.md) | 产品方法论（发现/优先级/路线图/指标），非工具 API |

### 2.4 运维与自改进（3 个）
| 技能 | 用途 |
|---|---|
| [self-improving-agent](self-improving-agent/SKILL.md) | 学习/纠错沉淀（lessons、错误归档） |
| [skill-creator](skill-creator/SKILL.md) | 创建/修改/评测 skill（本仓库新技能走它） |
| [aipm-news-digest](aipm-news-digest/SKILL.md) | RSS 聚合的 AI 产品日报（**定期 digest**，与 summarize 的单条摘要不同） |

## 三、外部 scope 技能（6 个，`@scope` 形式，不注册 manifest）

| 技能 | 用途 |
|---|---|
| `@heygen-com/media-use` | 媒体素材使用规范 |
| `@lijiazhen0623/media-generation` | 媒体生成（图/视频） |
| `@root/hyperframes` | 页面/分镜级视觉生成 |
| `@shreefentsar/remotion-video-toolkit` | Remotion 代码化视频 |
| `@whitetowerai/video-cut` | 视频剪辑 |
| `@xk103295870-alt/seedance2-video-gen` | Seedance 视频生成 |

这些是执行层技能：分镜/导演产出镜头描述后交给它们出片（storyboarding SKILL.md 已声明边界），
不承担创作方法论，不参与 manifest 注册。

## 四、边界速查（易混技能对）

| 易混对 | 判据 |
|---|---|
| novel-writing ↔ script-writing | 文体=叙述体 → novel；场次/台词体 → script；改编走 script 的 `adaptation-guide` |
| script-writing ↔ storyboarding | 写"发生什么" → script；写"怎么拍（镜/景/运/时）" → storyboarding |
| directing ↔ showrunning | 单集/单场的呈现 → directing；整季/整平台策略与排期 → showrunning |
| brave-search ↔ tavily-search | 通用检索 → brave；要 AI 优化摘要 → tavily |
| summarize ↔ aipm-news-digest | 单链接/单文件摘要 → summarize；定期资讯聚合 → aipm-news-digest |
| describe 与 `_archive` | `skills/_archive/` 为 fork 前归档，不加载、不维护；相关陈旧测试已在收集阶段隔离 |

## 五、新增/变更技能规则

1. 新技能目录必须在 `manifest.json` 的 `skills` 数组注册（`@scope` 外部技能除外）；
2. 同步更新本图对应分组与边界表；
3. 创作技能须含「## 角色 / ## 方法论参考 / ## Related skills」三节（`tests/test_creative_skills.py` 校验）；
4. 方法论类内容写进 references（不放 SKILL.md），references 路由登记到 `knowledge/asset-map.md`。
