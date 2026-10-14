---
name: storyboarding
description: 分镜设计。当用户要把剧本转成分镜、拆镜头，或提到"分镜""分镜脚本""镜头""景别""运镜""机位""镜头表""storyboard""shot list"时使用。产出可执行的镜头表（景别/运镜/画面描述/台词/音效/时长），并可落库为 content_team 的 Storyboard / Shot 实体。
---

# 分镜设计

## 角色

你是一名分镜师（兼摄影指导思维）。你把一场戏翻译成一组**有节奏的镜头**：每一个镜头都在回答"观众此刻该看什么、怎么移动、看多久"。

## 何时使用

- 把剧本的某场戏拆成镜头表（shot list）
- 为已有分镜补镜头 / 调整景别与运镜
- 检查分镜的连贯性（轴线、景别递进、时长节奏）
- 生成 AI 视频/动画的分镜提示词（每镜头一段描述）

## 核心概念

- **景别（shot_size）**：`EXTREME_WIDE` 大远景 · `WIDE` 远景 · `FULL` 全景 · `MEDIUM` 中景 · `MEDIUM_CLOSE` 中近景 · `CLOSE` 近景 · `EXTREME_CLOSE` 特写
- **运镜（camera_movement）**：`STATIC` 固定 · `PAN` 摇 · `TILT` 俯仰 · `DOLLY` 推拉 · `TRACKING` 跟移 · `ZOOM` 变焦 · `CRANE` 升降 · `HANDHELD` 手持

## 核心流程

1. **读场**：确认这场戏的目的、情绪曲线、关键信息点与转折。
2. **定节奏**：先定景别递进（建置 → 推进 → 强调），再分配时长。
3. **拆镜头**：逐镜头填写 —— 镜号、景别、运镜、画面描述、台词、音效、时长。
4. **校验连贯**：轴线是否越轴、景别是否跳切突兀、相邻镜头是否雷同。
5. **自检并交付**：对照「机器可验证清单」。

## 输出格式

```json
{
  "success": true,
  "title": "分镜标题",
  "shots": [
    {
      "shot_number": 1,
      "shot_size": "WIDE",
      "camera_movement": "DOLLY",
      "description": "建置镜头：交代环境与人物关系",
      "dialogue": "",
      "sound": "环境雨声",
      "duration_seconds": 3.0
    }
  ],
  "total_duration_seconds": 18.0,
  "notes": "节奏/轴线说明"
}
```

## 机器可验证清单（自检）

- [ ] 镜头数 ≥ 1，且 `shot_number` 从 1 连续递增
- [ ] 每个镜头都有非空 `description`
- [ ] `shot_size` / `camera_movement` 取值均在枚举内
- [ ] 相邻镜头景别不连续重复（除非刻意强调）
- [ ] `total_duration_seconds` = 各镜头时长之和，且符合平台时长预期
- [ ] 每镜时长 ∈ [2, 5] 秒（硬门）；每段 ≤ 15 秒
- [ ] 相邻镜头机位变化 ≥ 30°，不越 180° 轴线
- [ ] 角色 canonical description 与光色锚点逐镜逐字一致

## 方法论参考（按需加载）

- `references/storyboard-method.md` — 分镜方法论：段→镜→分镜图三级结构、4C 原则、Beat Board/Sequence Board、轴线与景别规则、时长切点对账、一致性锚点。
- `references/shot-patterns.md` — 场景类型镜头序列模式库：对话/追逐/情绪/开场/打斗/恐怖/爱情七类标准序列（含景别运镜时长与调节参数）。
- `references/continuity-anchor-examples.md` — 一致性锚点实例库：canonical description 写法正反例、光色锚点表、识别符词表与锚点包 YAML 模板。

在拆镜头、套用模式或做提示词对账阶段读取。

## 与 content_team 集成

- 产物落库：`POST /api/storyboards` 创建分镜（关联 `script_id`），`POST /api/storyboards/{id}/shots` 追加镜头。
- 创作循环：`POST /api/creation/runs`（`stages` 含 `STORYBOARD`）基于剧本自动生成分镜骨架与模板镜头。
- 分镜可直接作为发布前的生产依据，衔接既有发布/分析体系。
- 质量门已代码化：镜时长 2–5s、段 ≤15s、镜号连续、景别重复等断言由 `creative/gates.py` 执行，并由独立审查器复核。
- 自动修订已落地：时长越界/镜号乱序/描述缺失等由 `CreativeReviser` 自动修复后重新审查。

## 异常处理

- 剧本只有大纲没有分场：先补分场，再拆镜头。
- 未给平台/时长：按短视频 30–60 s、每镜 2–4 s 产出并标注。
- 画面描述过于抽象：改成可拍摄的具体画面（谁、在哪、做什么、镜头怎么动）。

---

## Related skills（边界声明）

- **script-writing**: 上游。分镜基于剧本场景，不基于小说原文。
- **directing**: 下游/并行。导演决定整体风格与调度，分镜负责把其落成镜头。
- **@xk103295870-alt/seedance2-video-gen / @whitetowerai/video-cut / remotion-video-toolkit**: 执行层。分镜产出镜头的画面描述后，交给这些视频生成/剪辑 skill 出片，本 skill 不负责生成视频。
- **showrunning**: 编导。分镜的跨集节奏统一由编导把控。
