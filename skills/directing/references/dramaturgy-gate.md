# 戏剧硬门与模型语法适配（蒸馏）

> 面向 `directing` 的按需加载参考。蒸馏自公开"视觉导演 skill"的 dramaturgy 门禁与模型语法适配方法，重构为可执行清单，非逐字引用。

## 一、出口双门：不合格不出稿

每个镜头提示词在离开 skill 前必须通过两道门，任一不过则**不返回**：

1. **六点戏剧检查**（scene formula / three details / three jobs / motivated camera / readable geometry / five anchors）
2. **三细节审计**（每镜必须有三个具体可视细节）

禁止用"cinematic / dramatic / masterpiece / 8K"这类形容词堆砌替代导演推理。

## 二、六点戏剧检查（逐镜）

1. **scene formula**：这一镜在"建置/推进/强调"里承担哪个功能？
2. **three details**：至少三个具体可视细节（不是形容词）。
3. **three jobs**：镜头必须至少做三件事之一——改变情绪 / 推进动作 / 增加压力；三件都不做就删。
4. **motivated camera**：镜头运动必须有动机（跟随动作/揭示信息），不能为动而动。
5. **readable geometry**：空间关系可读（谁在前、谁在后、朝哪）。
6. **five anchors**：五个连续性锚点（角色身份/服装/道具/光位/画面方向）逐字固定。

## 三、三细节审计

- 每个镜头列三个可观测细节：如"左手撑桌沿 / 灯泡闪烁 / 门缝透光"。
- 细节必须可被画面验证；写不出三个 = 该镜未想清楚。

## 四、模型语法适配（能力优先路由）

不绑定具体厂商版本，按**控制面能力**选择提示词形态：

| 形态 | 适用 | 要点 |
|---|---|---|
| S1 motion-only | 已有静帧，只驱动动作 | 只写运动，不重复描述画面 |
| S2 full-description | 无参考图，纯文生视频 | 完整视觉+运动 |
| S3 keyframe-pair | 首尾帧工具 | 描述首帧→末帧变化 |
| S4 multi-shot timestamped | 多镜一次生成 | 每镜带时间戳与切点 |

适配层覆盖的能力族（示例，需以厂商最新文档为准）：Runway / Veo / Kling / Luma / Sora 类 / Hailuo / Pika / Vidu / Midjourney Video / 即梦·Seedance / 万相 / 开源(ComfyUI)。

图像侧同样按能力族适配（Midjourney / Flux / Nano Banana 类 / Seedream / Qwen-Image / SDXL+ControlNet / Ideogram / Recraft），并配套**角色与场景一致性**方法（canonical description + 参考图 + 逐字锚点）。

## 五、质量门（机器可验证）

- [ ] 每镜通过六点戏剧检查（留痕）
- [ ] 每镜有三个可观测细节
- [ ] 运镜有动机说明
- [ ] 五个连续性锚点逐字固定
- [ ] 提示词形态标注为 S1–S4 之一
- [ ] 能力族适配已声明，且不硬编码单一厂商行为
- [ ] 出口：失败任一门的提示词不进入交付
