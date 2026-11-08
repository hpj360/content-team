# 风格包全库（01–12）

> `directing` 按需加载参考。12 包 = 4 个基础风格包（01–04，写实/霓虹黑色/武侠写意/家庭剧情）
> + 8 个类型风格包（05–12：悬疑/喜剧/青春/古装/科幻/纪录片写实/黑色喜剧/职场都市）。
> 字段定义与覆盖规则见 `director-style-params.md`；选用纪律：一场一包、参数三层覆盖；
> 单镜均长 ≤5s（硬门）。选风格 = 加载一个参数块覆盖默认值。

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
  avg_shot_length_s: 4.5
  sound_policy: "同期声 + 极简钢琴，人声永远高于乐"
  negative_prompt_additions: ["wide_angle_distortion", "handheld_shake", "cold_tone"]
```

- **机制**：4.5s 均长 + 近焦集中 → 情绪在桌面细节（手/杯/合照）间流动，冲突靠沉默。
- **反例**：不是煽情特写连发。爆发前必须有 ≥ 2 个 4.5s 的"无事发生"镜头蓄压（单镜上限 5s，均长不得超门）。

## 05 悬疑惊悚

```yaml
风格参数:
  lens_kit_mm: [28, 50]
  allowed_moves: [static, slow_push]
  forbidden_moves: [handheld, crane]
  motion_budget: low            # 不动=不安
  key_light_ratio: "32:1"
  palette: ["冷绿", "脏黄", "深黑"]
  avg_shot_length_s: 5.0
  sound_policy: "环境底噪放大，配乐极简；关键时刻留白"
  negative_prompt_additions: ["bright_key_light", "camera_shake", "cheerful_tone"]
```

- **机制**：高光比 + 长镜 + 不动 → 观众自己"找威胁"，恐惧来自缺失而非展示。
- **反例 / 这不是什么**：不是 jump scare 堆砌。悬疑靠"信息缺失"（画外/门后/反打），
  一旦把威胁拍全就变成恐怖片或动作片。与 noir 的区别：noir 展示道德，本包隐藏真相。

## 06 喜剧节奏

```yaml
风格参数:
  lens_kit_mm: [35, 50]
  allowed_moves: [static, snap_zoom, whip_pan]
  forbidden_moves: [slow_dolly]
  motion_budget: medium
  key_light_ratio: "3:1"        # 平光轻松
  palette: ["高饱和", "暖调", "明快"]
  avg_shot_length_s: 2.0        # 短镜=节奏
  sound_policy: "节奏音效点题；笑点后留 0.5s 静默"
  negative_prompt_additions: ["moody_lighting", "long_take", "melancholy"]
```

- **机制**：短镜 + 平光 + 音效强调 = 荒诞的"正经"。笑点来自**画面与台词的反差**。
- **反例**：不是"角色做鬼脸"。喜剧的调度要"太认真"——用正剧的严谨拍荒诞的事。
- 无条件：**笑点后必须留白**（剪辑不切、音效停），否则观众来不及笑。

## 07 青春校园

```yaml
风格参数:
  lens_kit_mm: [35, 85]
  allowed_moves: [slow_dolly, static, gentle_track]
  forbidden_moves: [crane, whip_pan]
  motion_budget: low
  key_light_ratio: "2:1"        # 通透
  palette: ["奶油白", "青草绿", "天光蓝"]
  avg_shot_length_s: 4.5
  sound_policy: "环境声 + 钢琴/吉他单线；蝉鸣/铃声作为时代锚"
  negative_prompt_additions: ["hard_shadow", "neon", "handheld_shake"]
```

- **机制**：高调低反差 + 长焦柔化 → 时间的"慢"。重点是把日常拍出仪式感。
- **反例**：不是加滤镜。要用**空镜与停顿**（走廊/课桌/粉笔灰）承载情绪，
  人物可以不说话。

## 08 古装 / 东方古典

```yaml
风格参数:
  lens_kit_mm: [35, 100]
  allowed_moves: [static, arc_track, tilt]
  forbidden_moves: [handheld, snap_zoom]
  motion_budget: low
  key_light_ratio: "8:1"
  palette: ["黛", "赭", "月白", "朱砂点"]
  avg_shot_length_s: 4.5
  sound_policy: "环境留白，弦乐/箫；人声克制，器乐先行"
  negative_prompt_additions: ["modern_props", "fast_cut", "neon", "hdr_harsh"]
```

- **机制**：对称构图 + 留白 + 长镜均值 → 礼制与时间的重量。
- **反例**：不是"慢=高级"。写意靠**省略**（一拜定终身切出），不靠拖长每一镜。
- 硬约束：道具/服饰/称谓/礼制不得穿模（守锚点包）。

## 09 科幻硬核

```yaml
风格参数:
  lens_kit_mm: [24, 40]
  allowed_moves: [slow_push, crane, lateral_track]
  forbidden_moves: [handheld_shake]
  motion_budget: medium
  key_light_ratio: "6:1"
  palette: ["冷白", "钢青", "橙红警示"]
  avg_shot_length_s: 4.0
  sound_policy: "低频嗡鸣常在；机械/数据音精确对位动作"
  negative_prompt_additions: ["warm_cozy", "organic_texture_heavy", "magic_glow"]
```

- **机制**：广角 + 对称 + 功能光源 → 尺度感与"工程可信度"。
- **反例**：不是堆满 UI 与全息投影。硬核科幻靠**功能可见**（每束光/每个接口有用途），
  而非装饰性炫技。与 cyberpunk 的区别：本包不默认雨夜霓虹。

## 10 纪录片写实

```yaml
风格参数:
  lens_kit_mm: [35, 85]
  allowed_moves: [handheld, follow, static]
  forbidden_moves: [crane, snap_zoom]
  motion_budget: medium
  key_light_ratio: "2:1"
  palette: ["自然光", "环境原色", "低饱和"]
  avg_shot_length_s: 4.5
  sound_policy: "同期声优先，无配乐；保留环境瑕疵"
  negative_prompt_additions: ["studio_lighting", "perfect_composition", "soundtrack"]
```

- **机制**：自然光 + 跟拍 + 同期声 → "未经编排"的可信感。
- **反例**：不是"晃=真实"。手持只用于跟随动作，不制造焦虑；构图仍需可读。

## 11 黑色喜剧

```yaml
风格参数:
  lens_kit_mm: [28, 50]
  allowed_moves: [static, slow_push]
  forbidden_moves: [whip_pan]
  motion_budget: low
  key_light_ratio: "8:1"
  palette: ["冷灰", "芥末黄", "血锈红点"]
  avg_shot_length_s: 3.5
  sound_policy: "轻松配乐与残酷画面对位（反差）；音效克制"
  negative_prompt_additions: ["slapstick", "bright_cheerful", "fast_cut"]
```

- **机制**：冷调 + 轻配乐 + 残酷内容 → 反差产生"笑着发冷"。
- **反例**：不是"把悲剧拍搞笑"。表演保持克制写实，荒诞来自处境而非表情。

## 12 职场都市

```yaml
风格参数:
  lens_kit_mm: [35, 65]
  allowed_moves: [static, lateral_track, slow_push]
  forbidden_moves: [crane, handheld_shake]
  motion_budget: low
  key_light_ratio: "5:1"
  palette: ["玻璃青", "冷白", "高级灰"]
  avg_shot_length_s: 3.5
  sound_policy: "键盘/空调/电梯提示音作节拍；配乐冷感合成器"
  negative_prompt_additions: ["warm_cozy", "nature_light", "romantic_glow"]
```

- **机制**：冷白 + 玻璃反光 + 低运动 → 秩序感与疏离（职场的"体面"）。
- **反例**：不是"办公室随手拍"。要用几何秩序（隔间/玻璃/会议桌对称）承载权力关系。

## 选用与组合规则（01–12 统一）

1. **一场一风格，禁止跨包混用**：同场戏内禁止混风格包；类型切换（如喜剧切悬疑）直接换包，
   视听突变即类型转换的标点，转场即换包（风格也是节奏标点）。
2. **参数覆盖顺序**：`风格参数` > 场景锚点 > 全局默认（三层，逐层覆盖）。
3. **类型即节奏**：喜剧 2s 均长、悬疑 5s、古装 4.5s——均长本身就是类型信号（单镜上限 5s）。
4. **出口双门不放宽**：风格包只覆盖默认值，不豁免 `references/dramaturgy-gate.md` 的六点检查
   （与出口双门配合时，风格参数放宽的不门禁不放宽）。
5. **覆盖面**：基础 4 包（01–04）+ 类型 8 包（05–12）合计 **12 包**，覆盖主流类型与题材。

## 与本项目集成

- 风格包 YAML 直接写入创作循环 `options.style_pack`；`_build_directing` 将
  `style/tone/pacing` 落入 `DirectingPlan`。
- `gate_directing`（D001–D004）校验风格/基调/节奏/阐述完整性。
