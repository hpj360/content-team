# 语料库（Corpus）

> 真实作品与公开内容的**结构化拆解**，供 `novel-writing` / `script-writing`；`showrunning` 可迁移。
> 用于喂给拆文工作流（`case-breakdown.md`）与钩子库，方法论级 / 引用分级纪律见文末。
> 检索入口：`GET /api/corpus`（题材/技法筛选）· planner 自动引用（`corpus_refs_for`）。

## 语料地图（2026-11-08 整理）

| 族 | 数量 | 形态（form） | 一句话定位 |
|---|---|---|---|
| A. 公版经典拆解 | 20 | short-story / stage-play / novel / chapter-novel / multi-perspective 等 | 公版作品逐例拆解：反转/突转/误会/复仇/单元剧等母题库（含中式戏曲三案补缺） |
| B. 创作实战示例 | 3 | short-drama / variety-segment / animation-episode | 自产逐拍级示例（外卖逆袭/迷宫情报战/信使与灯塔） |
| C. 结构与机制范式 | 3 | sketch / mystery-game / structure-analysis | 跨题材通用机制：素描结构、剧本杀、章回体 |
| D. 题材赛道范式 | 8 | structure-analysis | 言情/商战/综艺/动画/竖屏互动/付费微短剧/叙事播客/游戏叙事 |
| E. 长篇双轨范式 | 2 | novel-paradigm | 冰与火之歌多线史诗、网文爆款引擎（六作逐案） |
| F. 导演方法论 | 5 | director-paradigm | 希区柯克/王家卫/黑泽明/昆汀/诺兰（T1–T8 深度档） |
| G. 喜剧双赛道 | 2 | comedy-competition | 素描竞赛工程、单口竞技工程（含逐案拆解） |
| H. 全拆与档案拆解 | 7 | beat-breakdown / archive-breakdown | 节拍级/弧线级/档案级单案深拆 |
| — 索引与工具文档 | 8 | —（非 case） | genre-comparison / hot-quotes-memes / failure-corpus / failure-by-genre / platform-hits-patterns / 新赛道失败库×2 / 命中审计 |

## 目录

### A. 公版经典拆解（20）

| 文件 | 作品 | 类型 | 可迁移点 |
|---|---|---|---|
| `deconstruction-chekhov-chameleon.md` | 契诃夫《变色龙》 | 短篇 | 单一场景人物立场翻转、对话驱动 |
| `deconstruction-luxun-kongyiji.md` | 鲁迅《孔乙己》 | 短篇 | 旁观者视角、细节复沓、悲剧留白 |
| `deconstruction-ohenry-gift.md` | 欧·亨利《麦琪的礼物》 | 短篇 | 双向牺牲、镜像结构、结尾反转 |
| `deconstruction-ibsen-dollhouse.md` | 易卜生《玩偶之家》 | 话剧 | 三幕突转、以声收尾、觉醒靠一个反问 |
| `deconstruction-maupassant-necklace.md` | 莫泊桑《项链》 | 短篇 | 欲望代价、假象道具、时间跳跃、结尾反转 |
| `deconstruction-sophocles-oedipus.md` | 索福克勒斯《俄狄浦斯王》 | 悲剧 | 调查即自证、命运反讽、象征动作 |
| `deconstruction-poe-telltale-heart.md` | 爱伦·坡《泄密的心》 | 恐怖 | 不可靠叙述、感官放大、声音恐怖 |
| `deconstruction-shakespeare-hamlet.md` | 莎士比亚《哈姆雷特》 | 悲剧 | 复仇延宕、戏中戏、代价具象化 |
| `deconstruction-akutagawa-rashomon.md` | 芥川龙之介《罗生门》式多视角 | 多视角 | 多版本自利叙述、真相不可知 |
| `deconstruction-chekhov-cherry-orchard.md` | 契诃夫《樱桃园》 | 戏剧 | 无反派悲剧、象征物、幕外转折、以声收尾 |
| `deconstruction-wilde-earnest.md` | 王尔德《不可儿戏》 | 喜剧 | 误会引擎、机锋对白、荒诞成真 |
| `deconstruction-maupassant-uncle-jules.md` | 莫泊桑《我的叔叔于勒》 | 短篇 | 期待落差、识别符转折、行动写道德 |
| `deconstruction-luxun-medicine.md` | 鲁迅《药》 | 短篇 | 双线并置、象征蒙太奇、看客群像 |
| `deconstruction-dumas-monte-cristo.md` | 大仲马《基督山伯爵》 | 长篇 | 复仇范式、马甲分层、延迟满足 |
| `deconstruction-doyle-holmes.md` | 柯南·道尔《福尔摩斯探案》 | 短篇系列 | 单元剧系列化、稳定模板、复盘揭示 |
| `deconstruction-verne-twenty-thousand-leagues.md` | 凡尔纳《海底两万里》 | 长篇 | 奇观悬念双引擎、知识型爽感 |
| `deconstruction-wu-journey-west.md` | 吴承恩《西游记》 | 章回体 | 任务型单元剧、群像分工、反派分层 |
| `deconstruction-dou-e-yuan.md` | 关汉卿《窦娥冤》 | 元杂剧 | 三桩誓愿=超自然验证装置、诉冤三层递进、六月飞雪公共词 |
| `deconstruction-mudanting.md` | 汤显祖《牡丹亭》 | 明传奇 | 生死双段结构、梦前置合法化、物证对账、园林情绪地形 |
| `deconstruction-honglou-meng.md` | 曹雪芹《红楼梦》判词系统 | 章回体 | 档案先于剧情、草蛇灰线伏笔登记、空间=性格、账本叙事 |

### B. 创作实战示例（3，皆为 content-team 原创）

| 文件 | 作品 | 类型 | 可迁移点 |
|---|---|---|---|
| `short-drama-example-waimai.md` | 外卖员逆袭（单集结构示例） | 竖屏单集 | 8 拍落地、卡点、悬念进状态卡 |
| `example-variety-segment.md` | 综艺任务赛段《迷宫情报战》 | 综艺 | 4 站位+四要素机制、拍 1–8 逐拍实录、三工况变体 |
| `example-animation-unit.md` | 动画单元集《信使与灯塔》 | 动画 | 拍 1–12 双引擎逐拍、作画工况分级、复合工况配比微调 |

### C. 结构与机制范式（3）

| 文件 | 主题 | 类型 | 可迁移点 |
|---|---|---|---|
| `deconstruction-comedy-sketch.md` | 中文商业素描结构（参考喜人奇妙夜式） | 素描 | 高概念前提、升级三拍、回调、笑中带泪 |
| `deconstruction-mystery-game.md` | 剧本杀高分机制 | 剧本杀 | 视角分割、线索链、信息公平、反转重估 |
| `deconstruction-chapter-form-wukong.md` | 章回体动作叙事范式（参考《黑神话：悟空》） | 章回体 | 档案式世界观、对手即主题、多结局 |

### D. 题材赛道范式（8）

| 文件 | 赛道 | 锚点 | 可迁移点 |
|---|---|---|---|
| `paradigm-modern-romance.md` | 现代言情 | 《后会友期》/《再见爱人》/《玫瑰的故事》 | 三层误会递进、戳破时机、体面化解红线 |
| `paradigm-urban-business.md` | 都市商战 | 《繁花》/《狂飙》 | 资源差攻防三段、玻璃房子里的暴力、规则内反杀 |
| `paradigm-variety-show.md` | 综艺段落 | 《后会友期》/《种地吧》/《歌手 2024》 | 站位分工、任务机制四要素、直播/录播/户外工况 |
| `paradigm-animation-series.md` | 动画番剧 | 《哪吒之魔童闹海》/《浪浪山小妖怪》 | 单元/主线双引擎配比、辨识度资产、两入两出 |
| `paradigm-vertical-interactive.md` | 竖屏互动 | 《盛夏芬德拉》/《逃出大英博物馆》 | 两分钟内核、选择即代价、分支回收对账 |
| `paradigm-paid-short-drama.md` | 付费微短剧 | 《盛夏芬德拉》/ 红果十亿俱乐部 | 免费转化窗、钩链卡点、投流=高潮切片、厂牌复利 |
| `paradigm-narrative-podcast.md` | 叙事播客 | 通用形态（公开方法论口径） | 5 秒时刻、张力六工具、悬崖钩 80–95% 位、周更复利 |
| `paradigm-game-narrative.md` | 游戏叙事 | 《黑神话：悟空》影神图体系 | 档案拼图、支线评论、叙述距离分层、空位设计 |

### E. 长篇双轨范式（2）

| 文件 | 赛道 | 对象 | 可迁移点 |
|---|---|---|---|
| `paradigm-western-epic-asoiaf.md` | 西式多线史诗 | 《冰与火之歌》口径 | POV 章节制、家族线账本、低魔计价、事件代词 |
| `paradigm-webnovel-hit-masters.md` | 网文爆款 | 十日终焉/斩神/我不是戏神/剑来/持械入宋/悟空传 | 数值化目标、轮回记忆账、文化规则库、语录体、AI 合规案例 |

### F. 导演方法论（5，含 R36 深化档）

| 文件 | 导演 | 可迁移点 |
|---|---|---|
| `paradigm-director-hitchcock.md` | 希区柯克 | 悬念vs惊吓、MacGuffin、POV 三角、观众契约背叛 |
| `paradigm-director-wongkarwai.md` | 王家卫 | 独白驱动、抽格慢门、前景遮挡、"条件虚拟句式" |
| `paradigm-director-kurosawa.md` | 黑泽明 | 长焦多机位、天气=叙事力、擦拭转场、群像招募 |
| `paradigm-director-tarantino.md` | 昆汀 | 章节非线性、闲谈即炸弹、后备箱镜头、暴力喜剧化 |
| `paradigm-director-nolan.md` | 诺兰 | 谜题盒结构、层级规则先行、三时轴收束、实拍物理感 |

### G. 喜剧双赛道（2，含逐案拆解）

| 文件 | 赛道 | 对象 | 可迁移点 |
|---|---|---|---|
| `paradigm-sketch-competition.md` | 素描喜剧竞赛 | 《互联网体检》《少爷和我》《小品的世界》等 | 预制件强设定、三拍装载、元自反、句式骨架 |
| `paradigm-standup-competition.md` | 单口喜剧竞技 | 《脱口秀大会》系列（六人设） | 五分钟单元、callback 登记、短板货币化、议题合规护栏 |

### H. 全拆与档案级拆解（7）

| 文件 | 对象 | 级别 | 可迁移点 |
|---|---|---|---|
| `breakdown-internet-health-check.md` | 《互联网体检》（2021） | 节拍级（16 拍） | 逐拍表、三拍升级对账、笑点分型、舞台→竖屏换算 |
| `breakdown-inception.md` | 《盗梦空间》（2010） | 节拍级 | 四层规则×时间对照、规则卡十条、认知负载管理 |
| `breakdown-kuangbiao-arc.md` | 《狂飙》黑化三幕（2023） | 弧线级 | 权力道具演化、合法身份漂移、黑化机制学 |
| `breakdown-rear-window.md` | 《后窗》（1954） | 节拍级 | 窗对账表、四幕 POV 三角执行表、单机位写作 |
| `breakdown-fanxiangzhidi.md` | 《反相之地》（2026） | 节拍级 | 规则怪谈规则卡、单集双钩、AI 一致性锚定 |
| `breakdown-black-myth-wukong.md` | 《黑神话：悟空》六章（2024） | 节拍级 | 气象定调章名、双收束制、影神图二次叙事 |
| `breakdown-blackmyth-yingshentu.md` | 《黑神话：悟空》影神图（203 条） | 档案级 | 判词+志传条目公式、五样条实证、收集叙事账户 |

### 索引与工具文档（5，非案例条目）

| 文件 | 用途 |
|---|---|
| `genre-comparison.md` | 按题材归类已有案例 + 推荐组合 |
| `hot-quotes-memes.md` | 热梗/核心台词/名场面沉淀（L1/L2 分级引用，2026-11-04 校准） |
| `failure-corpus.md` | 跨阶段失败案例集（N-FAIL/P-FAIL，症状→机制→修复） |
| `failure-by-genre.md` | 六题材 ×5 高频失败模式 |
| `platform-hits-patterns.md` | 11 平台爆款共性 + 原创骨架示例（范式级） |
| `failure-vertical-drama.md` | 竖屏剧集失败模式库 V-F1–V-F10（转化窗/投流/合规红线，公开报道口径） |
| `failure-ai-drama.md` | AI 剧集失败模式库 AI-F1–AI-F10（一致性崩坏/融梗争议/更新失守，公开讨论口径） |
| `corpus-coverage-audit.md` | 语料命中审计（双通道模拟 + 死键机制 + 短别名补丁复测，2026-11-08） |

## 作品分工声明（同 IP 多文件不重复）

- **《黑神话：悟空》四件套**：`deconstruction-chapter-form-wukong.md`（原著章回体结构）
  → `paradigm-game-narrative.md`（影神图叙事体系的方法论框架）
  → `breakdown-blackmyth-yingshentu.md`（档案工程：203 条图鉴的条目公式与样条）
  → `breakdown-black-myth-wukong.md`（游戏成品：六章编排逐章拆）。
- **《狂飙》双件**：`paradigm-urban-business.md`（商战范式挂《狂飙》为锚）
  → `breakdown-kuangbiao-arc.md`（人物弧线级全拆）；两文件只在"规则内反杀"条目互引，不重复机制。
- **竖屏短剧三件**：`paradigm-vertical-interactive.md`（互动分支范式）
  → `paradigm-paid-short-drama.md`（付费/分账/投流商业层）
  → `breakdown-fanxiangzhidi.md`（AI 剧集生产管线样本）；机制分层不重叠。

## 版权与引用纪律（见 AGENTS.md #3 分级）

- 所选**公版**作品（作者逝世逾版权保护期）可做结构化拆解。
- **版权期作品**只做方法论级分析与原创改写；范式分析锚点选取现象级热门作品，
  仅对标公开讨论过的结构要点，不复制台词/素材/美术。
- **引用分级**：L1 现象/梗名优先；L2 台词短引 ≤2 句且标作品与年份；L3 成段照录禁止
  （段落级素材须以本地文档提交后做结构化摘录）。
- 热锚时效随时间衰减，使用前按 `content_freshness` 复审。**最近校准 2026-11-04**。

## 使用方式

1. 对照 `skills/novel-writing/references/case-breakdown.md` 的五步拆解法阅读；
2. 把可迁移结论回填到选题/模板（`GET /api/templates`）；
3. 拆解中的钩子式编号对应 `hook-library.md` 的 13 式；
4. 命中新案例时优先查**作品分工声明**，避免重复拆解同 IP。
