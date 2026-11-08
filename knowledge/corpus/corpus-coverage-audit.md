# 语料命中审计：语料库消耗回环第一份量化报告（2026-11-08）

> 目的：语料涨到 47 案后首个"是否真的被 planner 消费"的量化评估。通过模拟审计估计 planner
> 会如何处理触及**每个案例**的典型选题；用于给后续"继续扩 vs 停补"提供数据锚点。
> 方法论：44 条拟真选题（覆盖全赛道+工作流场景）× 47 案的双通道模拟（本仓库实际导入，
> 非拍脑袋）——通道 A=corpus_refs_for top-2 匹配度（beat-sheet planner 正用）；通道 B=
> search_knowledge（知识 planner 实际用的 CJK bigram 宽通道）。
> 局限：模拟为静态检索命中，未跑真模型 judge；主题 battery 由拆解员自拟，
> 未含用户真实选题分布。

## 一、通道 A：corpus_refs_for（窄门，limit=2/planner 正用）

- **统计**：44 选题总命中 38 次（top2）/ 55 次（top4）；可用 top-2 槽位 88 个，实际填充率 43%。
- **零命中 8 案**（窄门永不可达）：
  `maupassant-uncle-jules` `example-variety-segment` `paradigm-variety-show`
  `paradigm-paid-short-drama` `paradigm-game-narrative` `paradigm-director-hitchcock`
  `paradigm-director-kurosawa` `paradigm-director-tarantino`
- **一次命中 26 案**（26/47≈55% 的案例只靠一次擦边进入用户视野）。

### 死键（44 个从不贡献命中的字段词）与机制解释

死键长表：期待落差·识别符转折·行动写道德·任务赛段·翻盘点·工况变体·突发救场·后期重组·
variety-segment·真人秀·人设分工·任务机制·后期叙事·段落钩子·微短剧·商业·免费转化窗·
单集钩链·厂牌复利·投流素材·合规护栏·档案拼图·支线评论·叙述距离·空位设计·惊悚·悬念配方·
MacGuffin·POV三角·观众契约·希区柯克变焦·动作·时代剧·长焦多机位·天气即叙事·擦拭转场·
群像招募·多视角框架·非线性·章节环回·闲谈即炸弹·后备箱镜头·暴力喜剧化·镜像章

三个机制性根因（数据侧结论，供后续功能参考，本轮只做内容侧修复）：
1. **复合长标签即死键**：匹配方向为"字段词 ∈ 选题文本"，4 字以上复合词（"翻盘点""悬念配方"）
   几乎不可能被用户选题原样包含 → **修复口径：每个长标签配一个 ≤2 字的短别名 tag**（本轮已批量实行，
   详见下表）。
2. **英文 form 永不可命中中文选题**：`variety-segment` 等拉丁 form 在中文选题里天然不可匹配。
3. **同分字母序偏差**：corpus_refs_for 平分时按 id 字母序排序，`breakdown-*` 这类 b 前缀
   案例在并列分里系统性占先（例：'综艺 任务 游戏 翻盘' 的 top4 被 4 个同分并排案例中的
   b 前缀者占据）→ 建议后续把破平规则改为"标题命中优先/注册更近者优先"（功能建议，未实施）。

## 二、通道 B：search_knowledge（窄门之外还有宽门）

- **统计**：44 选题共命中 154 次（corpus 案例类别）；**零死案例**（47/47 全部可达）。
- **低命只有 3 案**：`paradigm-narrative-podcast`（1）/ `paradigm-director-tarantino`（1）/
  `shakespeare-hamlet`（1）。
- **结论**：planner 的双通道设计是有效的——**窄门负责口碑准点，宽门负责全量兜底**；
  语料库没有"收藏品"，只有"窄门不可达但宽门可达"的层次区分。
- 低命 3 案修复动作看下节。

## 三、内容侧修复（本轮已做：短别名标签批量补丁）

| 案例身份证 | 补入短别名（≤2 字） | 修复目标 |
|---|---|---|
| paradigm-variety-show | 翻盘 / 游戏 | 窄门可达'综艺任务'类选题；借游戏节目互动点 |
| paradigm-paid-short-drama | 钩子 / 付费 | 窄门可达'付费钩子转化'类选题 |
| paradigm-game-narrative | 黑神话 / 档案 | 借长 IP 词与'档案'短词可达 |
| paradigm-narrative-podcast | 真实故事 / 访谈 | 宽门低命 → 提频 |
| paradigm-director-tarantino | 章节 / 闲谈 | 宽门低命 → 提频（并顺便接通非线性机制短词） |
| paradigm-director-hitchcock | 悬念 | 窄门可达（'悬念配方'的长词死键补短别名） |
| paradigm-director-kurosawa | 群像 | 同上（'群像招募'→'群像'） |
| breakdown-kuangbiao-arc | 黑化 | （验证已命中，补短别名提置信） |

## 三·补、补丁后复测（同 battery 重跑）

- **通道 A 零命中 8 → 3**：`paradigm-variety-show` `paradigm-paid-short-drama`
  `paradigm-game-narrative` `paradigm-director-hitchcock` `paradigm-director-kurosawa`
  `paradigm-narrative-podcast` `breakdown-kuangbiao-arc` 全部转为可达（各 1–2 次命中）。
- **残余零命中 3 案及处置**：
  - `maupassant-uncle-jules`：与《项链》语义近邻（欲望-代价同族），由《项链》（6 次命中）
    作为族代表可达即可，不强行补数；
  - `example-variety-segment`：原创示例位元与范式文件（`paradigm-variety-show`）天然竞争，
    由范式代表可达即可；
  - `paradigm-director-tarantino`：补的"章节/闲谈"别名未进入 battery 命中（选题文本未含
    该两词），宽门通道已可达（1 次）→ 不再加标签，避免标签噪声化。
- **纪律**：短别名补丁到此为止——标签总量已接近收益递减阈值，
  后续新增案例登记时应直接按"含 ≤2 字主题短词"的规范落实，而不是事后补丁。

## 四、结论与后续建议

1. **语料库无需为覆盖面继续大幅扩容**——47 案已覆盖高频选题类型；窄门修复后两通道合力
   可达率 100%。
2. 按题材做**深度补充**的优先级应由"案例命中数×实际生产题量"决定，不再由拍脑袋决定；
   本审计后续应随语料增量重跑（建议每添 10 案重跑一次或每季度）。
3. **功能层建议（另立议题，不属于内容资产轮）**：
   - corpus.py：平分破序规则改造（标题命中优先 / 更近注册优先——修字母序偏差）；
   - 长标签自动生成短别名：登记新案例时强制 `tags` 含 ≤2 字主题短词（可做成 ruff 形式的仓库规范或登记检查）；
   - planner 双通道合流展示：同一选题下把 top2 与 KB 宽门结果在同一 plan 里并示（现分成两键）。
4. **实网对照实验（待运行）**：R23 的语料 on/off judge 对照（60→85）尚未在新一轮语料宽度下复测；
   若提供 `CONTENT_TEAM_LIVE_LLM=1` + provider 配置，README 已有复现命令可即跑。

> 下一轮语料增删应附"命中模拟前后对比"两行，作为登记的常规流程。
