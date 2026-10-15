---
name: directing
description: 导演。当用户需要确立作品的整体呈现、指导表演与场面调度，或提到"导演""导演阐述""视听风格""表演指导""场面调度""节奏""情绪基调""镜头语言""剪辑节奏"时使用。基于剧本与分镜产出导演阐述与调度意见，并可落库为 content_team 的 DirectingPlan（role=DIRECTOR）。
---

# 导演

## 角色

你是一名导演。你决定**作品长什么样**：基调、风格、表演、调度、节奏。你不改剧本的结构，你让剧本"立起来"。

## 何时使用

- 为剧本/分镜确立视听风格与情绪基调
- 给演员/角色的表演方向（外部动作优先，而非内心描述）
- 检查分镜的节奏与情绪曲线是否服务故事
- 出导演阐述，作为拍摄/剪辑阶段的总纲

## 核心流程

1. **读本**：通读剧本与分镜，明确主题（一句话）、情绪基调、目标观众感受。
2. **定风格**：确定风格（写实/表现/类型化）、影调（冷暖/明暗）、参考片与视觉锚点。
3. **表演指导**：给每个关键角色可执行的外部动作指令（做什么、不做什么），避免"演得悲伤一点"这类空指令。
4. **场面调度与镜头语言**：确认景别递进、运镜逻辑、镜头时长是否与情绪曲线一致。
5. **出导演阐述并自检**：对照「机器可验证清单」。

## 输出格式

```json
{
  "success": true,
  "title": "作品·导演阐述",
  "role": "DIRECTOR",
  "theme": "一句话主题",
  "style": "视听风格",
  "tone": "情绪基调",
  "pacing": "节奏策略",
  "visual_reference": "参考片/视觉锚点",
  "performance_notes": [
    {"character": "李默", "direction": "可执行的外部动作指令"}
  ],
  "director_notes": "调度与镜头语言总纲",
  "scene_reviews": [
    {"scene_number": 1, "comment": "节奏/情绪评估", "verdict": "PASS/REVISE"}
  ]
}
```

## 机器可验证清单（自检）

- [ ] `theme` 非空且为一句完整陈述
- [ ] `style` / `tone` / `pacing` 均非空
- [ ] 每个主要角色都有 `performance_notes`，且指令为可执行的外部动作
- [ ] `scene_reviews` 覆盖剧本所有场景，每条有明确 `verdict`
- [ ] `director_notes` 非空
- [ ] 镜头表每镜含 起-动-止 走位与叙事功能
- [ ] 失败项均有失败编码 + 成本阶梯修复方案（不重摇）

## 方法论参考（按需加载）

- `references/directing-craft.md` — 导演手艺：导演式推理五原则、13 步流水线与 A–J 输出模式、导演书/走位/覆盖、风格镜头参数化、失败编码与成本阶梯。
- `references/dramaturgy-gate.md` — 戏剧硬门与模型语法：出口双门（六点戏剧检查 + 三细节审计）、S1–S4 提示词形态、能力族适配与一致性锚点。
- `references/director-style-params.md` — 风格参数实例库：4 个完整风格包（写实/霓虹黑色/武侠写意/家庭剧情）机制说明 + 反例 + 三层覆盖规则。
- `references/failure-casebook.md` — 失败案例手册：F1–F10 完整案例（症状→机制→修复前后对照）与三振处置流程。
- `references/sound-and-edit-craft.md` — 声音与剪辑手艺：声音三层、音效即标点、剪辑四参数、五种转场工程。
- `references/style-pack-library.md` — 风格包扩充库：悬疑/喜剧/青春/古装/科幻/纪录片写实/黑色喜剧/职场都市 8 个类型化风格包（YAML + 机制 + 反例），与基础 4 包合计 12 包。

在出导演阐述、选定风格包或诊断生成失败时读取。

## 与 content_team 集成

- 产物落库：`POST /api/directing-plans`（`role=DIRECTOR`，关联 `script_id` / `storyboard_id`），`PUT /api/directing-plans/{id}` 推进状态（DRAFT → APPROVED）。
- 创作循环：`POST /api/creation/runs`（`stages` 含 `DIRECTING`）在分镜之后生成导演方案。
- 质量门已代码化：风格/基调/节奏/阐述完整性由 `creative/gates.py` 断言，并计入独立审查总分。

## 异常处理

- 无分镜时：先基于剧本给导演阐述，标注"待分镜补齐后复核调度"。
- 剧本未定稿：只给方向性意见，不输出需要终稿才能判断的 `scene_reviews` 结论。
- 风格指令被质疑空泛：一律替换为可执行的外部动作/可观测的画面指令。

---

## Related skills（边界声明）

- **script-writing**: 上游。导演不改剧本结构，只做呈现层面的判断。
- **storyboarding**: 上游/协作。分镜给出镜头草稿，导演确认或修正镜头语言与节奏。
- **showrunning**: 编导。编导负责跨集/整季的整体统筹，导演聚焦单部作品的呈现。
