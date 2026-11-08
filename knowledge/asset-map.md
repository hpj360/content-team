# 资产总图（Asset Map）——唯一任务路由入口

> 作用：回答"**我现在的任务该看哪一份文件**"。本图只做**路由与权责声明**，不复制 INDEX 的
> 全量条目（目录见 `knowledge/INDEX.md`）、不复制方法论正文。
> 最近核对：2026-11-09（三路审计后的整合批次）。维护规则见文末。

## 一、五个入口的分工（谁看哪份）

| 入口 | 回答什么问题 | 读者 |
|---|---|---|
| `creative-methodology-overview.md`（总纲） | "叙事有哪些零件、为什么有效"（体系骨架） | 建立全局认知 |
| `usage-writing-with-content-team.md`（手册） | "我写小说时按什么流程、用什么命令" | 正在写的人 |
| **本图 asset-map** | "这个任务/问题该翻哪一份资产" | 找文件的人 |
| `knowledge/INDEX.md` | "一共有哪些资产"（生成式全量目录） | 检索与盘点 |
| `corpus/README.md` | "语料库怎么分族、同 IP 怎么分工" | 用案例对标的人 |

规则：规矩条文（引用分级）以 `AGENTS.md` #3 为准；失败编码总表以 `corpus/failure-corpus.md` 为准。

## 二、六道门 → 权威文件（写中流程）

| 门 | 权威文件 | 辅助 |
|---|---|---|
| ① 黄金三章 | `novel-writing/references/web-fiction-craft.md` | `hook-library.md` |
| ② 钩子登记 | `novel-writing/references/hook-library.md`（招式）+ `hook-mechanics.md`（机制） | `beat-sheets.md` S 系列 |
| ③ 去 AI 味 | `web-fiction-craft.md`（词表） | `creative/deai.py` 口径 |
| ④ 转场门 | `novel-writing/references/chapter-continuity.md`（七法/五层） | `script-writing/references/scene-engineering.md`（过渡四类） |
| ⑤ 连贯门 | `chapter-continuity.md`（叙述五层/语者恒定） | `narratology-toolbox.md`（视角/距离/时序/速度） |
| ⑥ 细节维度门 | `scene-detail-engineering.md`（物理层）+ `emotion-conflict-externalization.md`（情感层） | 模板 `scene-detail-expansion` / `emotion-curve-card` |

写后：三层体检 `script-writing/references/revision-diagnosis.md`；伏笔对账 `GET /api/novels/{id}/story-state`。

## 三、问题 → 文件路由（速查）

| 问题 | 权威文件 |
|---|---|
| 开篇不抓人 / 章尾无钩 | `web-fiction-craft.md` → `hook-mechanics.md` |
| 中段塌陷 / 节奏失衡 | `beat-sheets.md`（**拍位时长唯一权威**） |
| 场景像流水账 | `scene-engineering.md`（价值翻转/删除测试）；物理细节 → `scene-detail-engineering.md` |
| 情感直述 / 冲突靠对话 | `emotion-conflict-externalization.md` |
| 人物扁平 / 台词同腔 | `character-bible.md` + `dialogue-examples.md` |
| 世界观漏气 | `worldbuilding-guide.md`（通用五层）；题材参数 → `genre-*-techniques.md` |
| 规则怪谈不会写规则 | `rule-horror-techniques.md` |
| 视角漂 / 距离忽远忽近 | `narratology-toolbox.md` |
| 主题说不清 / 结尾空 | `theme-engineering.md` |
| 章与章断线 / 转场生硬 | `chapter-continuity.md` |
| 改稿不知从哪下手 | `revision-diagnosis.md` |
| 题材怎么选/雷区 | `genre-playbooks.md`（速查层，数值以 techniques 为准） |
| 编剧结构 / 九形态格式 | `screenwriting-craft.md` / `screenplay-formats.md` |
| 短剧节奏 | `short-drama-playbook.md`（**节奏数值以 beat-sheets 为准**） |
| 平台怎么发 | `platform-playbooks.md`（**数值权威**）；骨架 → `platform-structure-templates.md` |
| 多季/系列规划 | `series-planning.md`；交接 → `production-contract.md` |
| 风格包 / 导演流水线 | `director-style-params.md` / `style-pack-library.md` / `directing-craft.md` |
| 分镜镜头序列 | `storyboard-method.md` / `shot-patterns.md` / `vertical-shot-grammar.md` |
| 剪辑切点/声画 | `edit-rhythm-and-transition.md` / `sound-and-edit-craft.md` |
| AI 视频分镜提示词 | `ai-video-storyboard-prompting.md` |
| 改编（小说↔剧本） | `adaptation-guide.md` |

## 四、题材簇权责（审计确认的三份散点已归位）

| 层 | 文件 | 权责 |
|---|---|---|
| 选题速查层 | `novel-writing/references/genre-playbooks.md` | 读者期待/爽点节奏/雷区；**数值以参数层为准** |
| 参数层 | `genre-xuanhuan-techniques.md` / `genre-scifi-techniques.md` / `genre-mystery-techniques.md` | 境界/三律/诡计的专属参数 |
| 短剧题材层 | `script-writing/references/short-drama-genres.md` | 竖屏六题材爽点链 |
| 案例对照 | `corpus/genre-comparison.md` | 只做案例横向对照与组合推荐 |
| 平台共性 | `corpus/platform-hits-patterns.md` | 11 平台爆款共性/翻车点 |
| 题材失败 | `corpus/failure-by-genre.md` | 六题材高频失败 |

## 五、语料簇分工（同 IP 多文件，不重复同一机制）

| 簇 | 主文件（机制权威） | 从文件（实证/编排） |
|---|---|---|
| 黑神话四件 | `paradigm-game-narrative.md`（叙事系统定义） | `deconstruction-chapter-form-wukong.md`（章回体范式）、`breakdown-blackmyth-yingshentu.md`（档案条目实证）、`breakdown-black-myth-wukong.md`（六章编排） |
| 竖屏三件 | `paradigm-vertical-interactive.md`（互动分支机制） | `paradigm-paid-short-drama.md`（赛道/变现/投流）、`breakdown-fanxiangzhidi.md`（AI 生产样本） |
| 喜剧两件 | `paradigm-sketch-competition.md`（赛制+逐案） | `deconstruction-comedy-sketch.md`（仅结构范式） |
| 误会两型 | `paradigm-modern-romance.md`（分层信息差型，权威入口） | `deconstruction-wilde-earnest.md`（装置型，不可互替） |
| 狂飙两件 | `breakdown-kuangbiao-arc.md`（弧线级） | `paradigm-urban-business.md`（商战范式挂锚） |
| 失败六库 | `corpus/failure-corpus.md`（**总索引+沉淀规范**） | `failure-by-genre.md`、`failure-vertical-drama.md`、`failure-ai-drama.md`、`skills/directing/references/failure-casebook.md`、`skills/storyboarding/references/storyboard-failure-casebook.md`、`revision-diagnosis.md` |

**项目工作区（`content-creation/novel/`）方法资产**：16/22/23/24/25/27 号与 44 号已蒸馏进上述 references（映射表见 `content-creation/novel/00-资产总览.md` 末节）；工作区文件保留项目侧执行细节，方法论冲突时以 references 为准。

## 六、references 全清单（50 份，按簇分组；★=簇主文件）

**novel-writing（17）**：★`web-fiction-craft`（商业/开篇）· `hook-library`/`hook-mechanics`（招式/机制配对）· ★`narratology-toolbox`（叙述原理）· ★`chapter-continuity`（章际）· ★`theme-engineering` · ★`worldbuilding-guide` · ★`character-bible` · `genre-playbooks`（速查）· `genre-xuanhuan-techniques` / `genre-scifi-techniques` / `genre-mystery-techniques`（参数）· ★`rule-horror-techniques` · ★`scene-detail-engineering` · ★`emotion-conflict-externalization` · `story-state-and-continuity` · `case-breakdown`

**script-writing（13）**：★`screenwriting-craft` · ★`beat-sheets`（**拍位时长唯一权威**）· `short-drama-playbook`（表达层）· `short-drama-genres` · ★`scene-engineering`（判定）· `scene-writing-drills`（素材）· ★`dialogue-examples` · ★`revision-diagnosis` · `screenplay-formats`（要点）· `variety-and-broadcast`（三形态完整模板）· `documentary-musical-immersive` · `interactive-and-game-script` · `adaptation-guide`

**showrunning（7）**：★`platform-playbooks`（**平台数值权威**）· `platform-structure-templates`（骨架）· `platform-rule-maintenance` · ★`series-planning` · `episode-rhythm-examples`（实例，口径同 beat-sheets）· ★`production-contract` · `acceptance-checklists`

**directing（6）**：★`directing-craft`（五原则/流水线）· ★`director-style-params`（YAML 字段权威）· `style-pack-library`（8 风格包）· `dramaturgy-gate`（戏剧硬门）· ★`failure-casebook`（F1–F10）· ★`sound-and-edit-craft`

**storyboarding（7）**：★`storyboard-method` · ★`shot-patterns` · `vertical-shot-grammar` · ★`continuity-anchor-examples` · ★`edit-rhythm-and-transition`（镜头层切点）· `storyboard-failure-casebook`（SB1–SB8）· `ai-video-storyboard-prompting`

**转场分层**（四套分类各司其职）：叙事层 `scene-engineering.md` 四类 → 章际层 `chapter-continuity.md` 七法 → 镜头层 `edit-rhythm-and-transition.md` 四类 → 成片层 `sound-and-edit-craft.md`（声音/剪辑，编号以镜头层为准）。

## 七、模板 id 路由（22 个内置）

| 场景 | 模板 id |
|---|---|
| 网文开书 | `novel-golden-three` · `worldbuilding-sheet` · `character-profile` · `romance-misunderstanding-engine` |
| 竖屏短剧 | `short-drama-episode-8beat`（90s）· `vertical-two-minute-episode`（120s）· `storyboard-vertical-scene`（竖屏 9:16） |
| 脚本/戏剧 | `comedy-sketch-structure` · `mystery-game-outline` · `stage-play-script` · `variety-script` · `oral-broadcast-script` · `audio-drama-script` · `interactive-node-script` · `documentary-script` · `jubensha-character-book` |
| 长篇/系列 | `series-episode-outline` · `animation-unit-episode` |
| 分镜/导演 | `storyboard-dialogue-scene`（横屏 16:9）· `directing-style-pack-starter` |
| **细节扩写（R45）** | `scene-detail-expansion`（物理层）· `emotion-curve-card`（情感层）——两者配合使用 |

## 八、失败编码总览（细节见各文件）

F1–F10 导演层（`directing/references/failure-casebook.md`）· SB1–SB8 分镜层（`storyboard-failure-casebook.md`）· N-FAIL/P-FAIL 叙事流程层（`corpus/failure-corpus.md`，**总索引在此**）· V-F1–F10 竖屏层（`corpus/failure-vertical-drama.md`）· AI-F1–AI-F10 生成内容层（`corpus/failure-ai-drama.md`）· ST/SC/SE 稿件诊断层（`script-writing/references/revision-diagnosis.md`）。

## 九、维护规则（防止本图漂移）

1. 新增/改名任何 references、corpus 案例、内置模板 → **必须同步本图对应小节**；
2. 测试 `tests/content_team/test_asset_integrity.py` 校验：本图覆盖全部 50 份 references 文件名、全部内置模板 id、六套失败编码、`style-pack-library` 实数一致；
3. 同 IP 新增拆解文件时，先在本图第五节登记"主/从"关系，再写文件；
4. 本图**不承载正文**——方法论描述留在各文件，避免第二份真相。
