# 导演风格参数实例库

> `directing` 按需加载参考。4 个完整风格包（可机器读取的 `风格参数` YAML + 机制说明 + 反例），选风格 = 加载一个参数块覆盖默认值。

## 01 写实主义（生活流）

```yaml
风格参数:
  lens_kit_mm: [35, 50]
  allowed_moves: [static, slow_dolly, handheld]
  forbidden_moves: [whip_pan, crane, zoom]
  motion_budget: low            # 每镜至多一处运动
  key_light_ratio: "4:1"
  palette: ["自然肤色", "低饱和环境色"]
  avg_shot_length_s: 4.0
  sound_policy: "同期声优先，无配乐或单乐器点缀"
  negative_prompt_additions: ["didynamic", "color_grading_heavy", "hero_angle"]
```

- **机制**：低运动预算 + 中焦段 + 4:1 光比 → 观众注意力落在表演而非镜头。
- **反例 / 这不是什么**：不是"平拍记录"。它的调度仍在（前景遮挡、门框纵深），
  只是**不让观众察觉**调度。与"手持纪录片感"的区别：本风格手持仅用于跟移，
  不制造晃动焦虑。

## 02 霓虹黑色（城市夜罪）

```yaml
风格参数:
  lens_kit_mm: [28, 40]
  allowed_moves: [slow_push, lateral_track]
  forbidden_moves: [handheld]
  motion_budget: medium
  key_light_ratio: "16:1"
  palette: ["霓虹青", "品红", "沥青黑"]
  avg_shot_length_s: 3.0
  sound_policy: "低频持续底噪 + 孤立音效放大（脚步/雨滴）"
  negative_prompt_additions: ["daylight", "warm_tone", "crowd_cheer"]
```

- **机制**：高对比 + 双色分离打光 → 把人脸一半交给色块，制造道德暧昧。
- **反例**：不是"下 rain 就完事"。雨只是实用光反射体；无雨版本靠湿地面反光成立。
  与"赛博朋克"的区别：本风格**不堆全息广告**，霓虹只作为光源不作为布景。

## 03 武侠写意（留白东方）

```yaml
风格参数:
  lens_kit_mm: [50, 85]
  allowed_moves: [static, arc_track, tilt]
  forbidden_moves: [handheld, zoom]
  motion_budget: medium
  key_light_ratio: "8:1"
  palette: ["绢白", "黛青", "朱砂点"]
  avg_shot_length_s: 5.0
  sound_policy: "环境留白，动作音后置半拍，一击定音"
  negative_prompt_additions: ["fast_cut", "modern_props", "oversaturation"]
```

- **机制**：长焦浅景 + 长镜头均值 → 打斗的"留白"比交锋多，力量感来自**停顿**。
- **反例**：不是慢动作堆砌。写意 = 结果省略（一招定胜负切出），而非过程拖长。

## 04 家庭剧情（室内情感）

```yaml
风格参数:
  lens_kit_mm: [40, 65]
  allowed_moves: [slow_dolly, static]
  forbidden_moves: [crane, whip_pan]
  motion_budget: low
  key_light_ratio: "3:1"
  palette: ["钨丝暖黄", "米白", "木质棕"]
  avg_shot_length_s: 6.0
  sound_policy: "同期声 + 极简钢琴，人声永远高于乐"
  negative_prompt_additions: ["wide_angle_distortion", "handheld_shake", "cold_tone"]
```

- **机制**：6s 均长 + 近焦集中 → 情绪在桌面细节（手/杯/合照）间流动，冲突靠沉默。
- **反例**：不是煽情特写连发。爆发前必须有 ≥ 2 个 6s 的"无事发生"镜头蓄压。

## 选用与组合规则

1. **一场一风格**：同场戏内禁止混风格包；转场即换包（风格也是节奏标点）。
2. 参数覆盖顺序：`风格参数` > 场景锚点 > 全局默认（三层，逐层覆盖）。
3. 与 `references/dramaturgy-gate.md` 的出口双门配合：风格参数放宽的不门禁不放宽。

## 与本项目集成

- 风格包 YAML 直接写入创作循环 `options.style_pack`；`_build_directing` 将
  `style/tone/pacing` 落入 `DirectingPlan`，供 `gate_directing`（D001–D004）校验完整性。
