# 各阶段验收清单实例

> `showrunning` 按需加载参考。编导分派任务时的**验收标准**实例（assignment.acceptance 的填法），四阶段各一份，均与 content_team 门禁编码对齐。

## 使用方式

编导方案（role=SHOWRUNNER）的 `assignment` 字段示例：

```json
{
  "stage": "SCRIPT",
  "owner_skill": "script-writing",
  "acceptance": "AC-S：logline≤200字；场景≥3且场场有价值转折；S005/S006/S007 零命中；单集折算时长±10%"
}
```

验收 = 人工抽查 + 门禁自动校验双轨；门禁编码即下表编号。

## AC-N 小说阶段（owner: novel-writing）

- [ ] N001/N002：logline 非空且 ≤ 200 字，含主角+欲望+障碍
- [ ] N003：书名非空且不与拆文库对标重名
- [ ] N004/N005：≥ 1 章正文非空；首章前 500 字出现主角与冲突/卖点
- [ ] N006：章字数落在 500–8000（或项目约定区间）
- [ ] T001–T007：状态卡 7 栏齐全；主要角色四维状态完整；伏笔含计划回收位置
- [ ] L001–L005：已埋伏笔在埋设章可命中；resolved 伏笔在回收章可命中
- [ ] 去 AI 味 pass 已执行（S006 词表零命中）
- **人工抽检**：黄金三章读感——第 3 章末是否产生"必须看第 4 章"的冲动

## AC-S 剧本阶段（owner: script-writing）

- [ ] S001/S002：logline 非空 ≤ 200 字
- [ ] S003/S004：正文非空；场景 ≥ 3，每场 slugline/purpose 齐全
- [ ] 每场"价值转折"：进场价值 ≠ 出场价值（人工逐场标注）
- [ ] S005：无旁白式心理描写（他心里/心想…）
- [ ] S006：AI 套路词零命中（不由得/顿时/心中暗道…）
- [ ] S007：合规阻断词零命中
- [ ] 时长折算：单集字数 / 4.2 字每秒，落在目标 ±10%
- [ ] 对手有明确动机与威胁
- **人工抽检**：任意 3 场台词读出声——腔调可区分、无解释性台词

## AC-B 分镜阶段（owner: storyboarding）

- [ ] B001/B002：镜头 ≥ 1，描述全部非空且为可拍画面
- [ ] B003：镜号从 1 连续递增
- [ ] B004：单镜 2–5s，段和 ≤ 15s
- [ ] B005：相邻镜头景别不重复；30° 规则 / 180° 轴线不越
- [ ] 锚点包三件套齐全：角色 canonical description / 光色锚点 / 识别符词表
- [ ] 与伏笔对账：识别符 = 状态卡 foreshadowing.keyword（可命中）
- **人工抽检**：任取 2 镜——说得出"观众此刻比一秒前多懂了什么"

## AC-D 导演阶段（owner: directing）

- [ ] D001–D004：style/tone/pacing/director_notes 全部非空
- [ ] 风格包已选定且 `风格参数` YAML 字段完整（镜头包/运动预算/光比/色板/均长/声音策略）
- [ ] 每镜含 起-动-止 走位与叙事功能标注
- [ ] 六点戏剧检查留痕（scene formula / three details / three jobs / motivated camera / readable geometry / five anchors）
- [ ] 失败项均有 F 编码 + 成本阶梯修复记录，无"重摇三次"未升级项
- **人工抽检**：风格参数是否真的改变了镜头（对照反例清单，不是"加个滤镜"）

## 编导侧全局验收（self）

- [ ] `positioning/format/style` 非空；episode_plan 每集 hook/cliffhanger 非空
- [ ] consistency_rules 三类（人物/世界观/视觉）非空且逐集复用
- [ ] assignment 四阶段全覆盖、acceptance 可验证
- [ ] 独立审查记录存在（非本版创作者上下文）
- [ ] `GET /api/creation/runs/stats`：近 5 run 平均分 ≥ 80 且无 EXHAUSTED 未处置
- [ ] 交付门声明：是否有生成工具 / 是否 dry-run
