# 写小说时怎么用这套方法论（操作手册）

> 面向"我自己动手写"的场景。方法论分三层取用，**不必全读**——按写前/写中/写后各查 1–3 份即可。
> 与 `creative-methodology-overview.md`（总纲，讲骨架）配对：总纲回答"叙事有什么零件"，本手册回答"我此刻该翻哪一页"。

> **定位**：操作手册——写小说时"翻哪一页、跑哪条命令"。
> **受众**：正在写小说的人（动手阶段）。
> **权威口径**：流程与命令以本文为准。
> **不做什么**：不讲原理（→ `creative-methodology-overview.md`）、不列全部资产（→ `knowledge/asset-map.md`）。

## 一、资产地图（三层 + 语料）

| 层 | 用途 | 文件 |
|---|---|---|
| **原理层**（R43） | 解释"为什么有效/何时失效"，用于诊断与设计决策 | `narratology-toolbox.md`（视角/距离/时序/速度）· `hook-mechanics.md`（四机制×13式）· `theme-engineering.md`（控制性观念/命题三拍）· `scene-engineering.md`（价值翻转/删除测试）· `revision-diagnosis.md`（三层体检 24 信号） |
| **招式层**（既有） | 直接照做的清单/模板 | `web-fiction-craft.md`（黄金三章/去 AI 味）· `hook-library.md`（13 式实例）· `beat-sheets.md`（三幕 15 拍/8 拍）· `scene-writing-drills.md`（八类场景）· `worldbuilding-guide.md`（五层/规则即代价）· `character-bible.md`（四维状态）· `genre-*.md`（题材技法 ×3）· `genre-playbooks.md`（七题材手册）· `story-state-and-continuity.md`（伏笔/时间线） |
| **连续性层**（本次蒸馏） | 章与章之间不断线 | `chapter-continuity.md`（转场七法/叙述五层/语者恒定/体量呼吸）· `rule-horror-techniques.md`（规则三构成/三级披露/理解成本转移） |
| **语料与参考** | 对标真实作品与失败模式 | `knowledge/corpus/`：公版拆解、范式工程、导演五件套、全拆、热梗库、失败库（含竖屏/AI）、`corpus-coverage-audit.md` |

> 全量资产与任务路由见 `knowledge/asset-map.md`（本表只列写作主路径）。

> 取用顺序建议：**先语料（找对标）→ 再原理（定策略）→ 后招式（抄清单）**。反过来容易写成"招式堆砌"。

## 二、写前（30–60 分钟，一次成套）

按任务选读，不要全量加载：

| 你要做的事 | 读这几份 | 产出 |
|---|---|---|
| 开新书 | `web-fiction-craft.md` + `genre-playbooks.md`（对应题材）+ `theme-engineering.md` | 一句话主题（控制性观念）+ 前三章钩子清单（每钩标机制类型） |
| 搭世界观 | `worldbuilding-guide.md`；若规则怪谈加 `rule-horror-techniques.md` | 规则卡（触发/禁忌/后果）+ 三级披露表 |
| 立人物 | `character-bible.md` + `narratology-toolbox.md`（视角=信息权限） | 主角/对手/陪衬三档 + 每人识别符 2 件 + 缺陷根源 |
| 选题对标 | `GET /api/corpus?genre=悬疑`、`GET /api/knowledge/search?q=规则怪谈` | 2–3 个对标案例的"可迁移结论"行 |

**写前 4 张卡**（缺一不开写）：主题卡、规则/金手指卡、人物卡、钩子清单（预登记 `planted_at`/`planned_resolution`）。

## 三、写中（每章循环：五道门）

沿用你已有的门禁体系，现在每道门都有对应文件：

| 门 | 什么时候过 | 依据文件 | 判定 |
|---|---|---|---|
| ① 黄金三章 | 开书前 3 章 | `web-fiction-craft.md` | 首 500 字有钩、金手指出场、章尾强钩 |
| ② 钩子登记 | 每章 | `hook-mechanics.md` + `hook-library.md` | 章首/章尾各 1 钩、标机制类型、**同时只欠 3 个钩** |
| ③ 去 AI 味 | 每章 | `web-fiction-craft.md`（AI 腔词表）+ `deai.py` 口径 | 无排比腔/无解释性旁白/无"仿佛"密度 |
| ④ 转场门 | 每章 | `chapter-continuity.md`（七法） | 章内冷切有桥、同章 ≤3 种桥法、A 出=B 进 |
| ⑤ 连贯门 | 每章 | `chapter-continuity.md`（叙述五层）+ `narratology-toolbox.md` | 视角不漂、回场概念半句重注、因果有由头、主线 6:3:1、语者恒定 |
| ⑥ 细节维度门 | 重点场景（冲突/情感转折） | `scene-detail-engineering.md`（五维+具体化四阶+事件/影响） + `emotion-conflict-externalization.md` | 先用模板 `detail-audit-sheet` 体检（五维各 3 问+影响四通道+档位评级）→ `scene-detail-expansion` 补写 → `emotion-curve-card` 分配情感；判定：五维至少 3 维、档位到 3/4、密度 3-5 个、情感不直述、冲突至少两维推进 |

**章卡模板**（每章一行，写完即填）：

```
章号｜主功能（推进/揭示/关系/情绪）｜进出价值（±→±）｜出钩类型（机制）｜伏笔登记（keyword→预计回收集）｜字数
```

**卡文三分钟急救**：先查 `failure-corpus.md` / `failure-by-genre.md` 对应条目 → 再用 `hook-mechanics.md` 的"失效条件"定位（是缺口太大？未完成动作重复？违背无解释？）→ 最后才动结构。

## 四、写后（每 5–10 章一次）

1. **三层诊断**（`revision-diagnosis.md`）：结构 → 场景 → 句子，**一轮只修一层，先删后加**；24 个标红信号当体检表。
2. **伏笔对账**：`GET /api/novels/{id}/story-state`（或 `writing-desk` 看"今天该写什么"）——检查 `planted/resolved`；欠钩 > 3 先还债再开新钩。
3. **跑自动审查（可选，只审不代写）**：
   - `POST /api/creation/runs`（`stages: ["NOVEL"]`）→ `GET /api/creation/runs/{id}/report`
   - 看什么：gates 断言结果（硬伤）、五维分（结构/合规/一致性/节奏/技法）、修订日志
   - 注意：报告里的"修订"是机制性的（补字段/补段落），**内容质量仍需你按三层诊断人工过**
4. **修订台账**（`chapter-continuity.md` 第六节格式）：每笔改动记"位置/修订/所用法条/性质"，便于回滚和复盘。

## 五、接管线：三种用法，按需升级

**A. 纯手册用法**（你现在的做法）：references 当写作手册，全部人工。成本最低，最适合长篇连载。

**B. 半自动**：模板 + 检索 + 人工（含场景扩写模板 / 情感曲线卡）。
```powershell
$env:PYTHONPATH="src"; uvicorn hermes.content_team.app:app --reload
# 取模板（新增 scene-detail-expansion / emotion-curve-card）
curl http://127.0.0.1:8000/api/templates
curl -X POST http://127.0.0.1:8000/api/templates/novel-golden-three/render -H "Content-Type: application/json" -d '{"variables":{"书名":"x","主角":"y","核心卖点":"z","金手指":"w","初始冲突":"v"}}'
# 检索方法论与语料
curl "http://127.0.0.1:8000/api/knowledge/search?q=转场&category=skill-reference"
curl "http://127.0.0.1:8000/api/corpus?genre=悬疑"
```

**C. 全自动跑管线**（要先配 LLM provider，否则角色降级为模板）：
```powershell
$env:HERMES_LLM_PROVIDER="zai"; $env:HERMES_LLM_MODEL="glm-4-flash"; $env:ZAI_API_KEY="..."
# 1) 建选题 → 2) 建小说 → 3) 跑创作
curl -X POST http://127.0.0.1:8000/api/topics -H "Content-Type: application/json" -d '{"title":"规则怪谈·雨夜楼道","description":"大学生坠入反相空间"}'
curl -X POST http://127.0.0.1:8000/api/creation/runs -H "Content-Type: application/json" -d '{"topic_id":"<uuid>","stages":["NOVEL"],"options":{"corpus_injection":true,"budget_tokens":200000}}'
# 4) 取报告 / 写作台 / 伏笔状态
curl http://127.0.0.1:8000/api/creation/runs/<run_id>/report
curl http://127.0.0.1:8000/api/novels/<novel_id>/writing-desk
```

> 全自动适合"出骨架 + 出草稿"，**不适合直接定稿**——你上一批稿子的经验是：机制层（规则/条目/对账）可以自动化，语感与情绪仍要人工。

## 六、决策速查表（遇到问题先翻哪页）

| 症状 | 先翻 |
|---|---|
| 开篇不抓人 / 前三章留不住 | `web-fiction-craft.md` → `hook-mechanics.md`（缺口机制） |
| 章尾没钩 / 读者不追更 | `hook-library.md` + `hook-mechanics.md`（蔡格尼克）+ 欠钩检查 |
| 中段塌陷 / 不知道写什么 | `beat-sheets.md`（15 拍定位）+ `failure-corpus.md`（中段病） |
| 人物扁平 / 说话一个腔调 | `character-bible.md`（四维/缺陷根源）+ `dialogue-examples.md`（8 症）+ `theme-engineering.md`（立场） |
| 世界观漏气 / 规则随便改 | `worldbuilding-guide.md`（规则即代价）+ `rule-horror-techniques.md`（三构成） |
| 转场跳跃 / 章节之间断线 | `chapter-continuity.md`（七法/五层） |
| 读者说"看不懂/太累" | `rule-horror-techniques.md`（理解成本转移七条） |
| 场景像流水账 / 单薄无细节 | `scene-engineering.md`（价值翻转/删除测试）→ `scene-detail-engineering.md`（五维+具体化四阶+事件/影响），模板 `detail-audit-sheet` 体检后 `scene-detail-expansion` 补写 |
| 情感直述 / 冲突全靠对话推 | `emotion-conflict-externalization.md`（四通道外化 + 五维冲突） |
| 改稿不知从哪下手 | `revision-diagnosis.md`（三层体检→手术顺序） |
| 主题说不清 / 结尾空 | `theme-engineering.md`（控制性观念/三拍/漂移检测） |
| 视角飘 / 距离忽远忽近 | `narratology-toolbox.md`（五形态/五档） |

## 七、节奏建议与常见误用

**节奏**：每章过六道门（10–15 分钟，第 6 门只过重点场景）；每 5–10 章做一次三层诊断；每卷做一次伏笔总对账 + 主题漂移检测；每书完稿做一次全量修订台账。

**三个常见误用**：
1. **一次加载全部 references** → 上下文膨胀、写出来像教科书。按需读 2–3 份。
2. **每章都做全量诊断** → 改稿疲劳。三层诊断是"批次作业"，不是日常作业。
3. **把机制逐句套模板** → 算法感。机制用于**诊断与修补**，不用于逐句生成。

## 八、局限

- 本手册基于本仓库当前方法论资产（R31–R44）编写；新增 references 后应同步更新速查表。
- 全自动管线依赖 LLM provider 配置与预算，产出需人工把关；实网联动见 README 的 `CONTENT_TEAM_LIVE_LLM=1` 说明。
- 规则怪谈/悬疑类方法论权重最高，言情/都市类以 `paradigm-modern-romance.md` 的误会引擎为主轴。
