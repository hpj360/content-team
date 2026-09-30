# 提示词调优报告（R15 pass）

> 数据来源：`tests/content_team/test_creative_live_tuning.py`（实网，智谱 GLM-4-Flash）。
> 命令：`CONTENT_TEAM_LIVE_LLM=1 HERMES_LLM_PROVIDER=zai HERMES_LLM_MODEL=glm-4-flash pytest tests/content_team/test_creative_live_tuning.py -q -s`

## 一、变体定义

| 变体 | 契约要点 |
|---|---|
| v1 | 极简契约（只约定 JSON 形状），模型自由度高 |
| v2 | **硬性配额**：≥3 场次、每场动作+台词、300–900 字、结尾钩子 |
| v3 | v2 + **风格锚定强约束**（有指纹时贴合句长/段落节奏）+ 禁 AI 腔 |

## 二、实测结果（2 选题 × 3 变体，n=2）

| 变体 | 平均字数 | 平均场景数 | 门禁通过率 | 字数落区率 | AI 腔命中 |
|---|---|---|---|---|---|
| v1 | 573.5 | 3 / 6 | 100% | 100% | 0 |
| **v2** | **625.0** | 3 / 4 | 100% | 100% | 0 |
| v3 | 294.0 | 3 / 4 | 100% | 100% | 0 |

明细：
```
waimai-counterattack  v1=516字/3场  v2=759字/3场  v3=262字/3场
deepsea-mystery       v1=631字/6场  v2=491字/4场  v3=326字/4场
```

## 三、结论与决策

- **选定默认 v2**：平均字数最接近目标区间中枢（625 vs 目标 300–900），且配额约束（场次/动作/台词/钩子）在提示层显式化，降低对模型发挥的依赖。
- **v3 偏短（294 字）**：风格锚定约束让模型"惜字"，低于目标下限。保留 v3 供**已设定指纹的高级用户**手动选用（其价值在声线贴合，需人工评估，非结构指标能衡量）。
- **v1** 可用但方差更大（3–6 场），作为兜底变体保留。
- `prompts.DEFAULT_VARIANT = "v2"`（已与数据一致）。

## 四、局限（诚实声明）

- 样本量小（n=2 选题、每变体 2 次），结论为**方向性**；扩大样本请调
  `CONTENT_TEAM_TUNING_TOPICS` 并多次运行。
- 本次调优只看**结构指标**（字数/场景/门禁/AI 腔）；**语义质量**（钩子强度、
  台词个性）需结合 judge 评分与人工抽检，尚未纳入自动对比。
- 单次 GLM-4-Flash 调用成本低（实测 prompt+completion ≈ 25–800 tokens），
  6 次采样总成本可忽略。

## 五、复现步骤

```powershell
$env:PYTHONPATH="src"
$env:HERMES_LLM_PROVIDER="zai"
$env:HERMES_LLM_MODEL="glm-4-flash"
$env:CONTENT_TEAM_LIVE_LLM="1"
$env:CONTENT_TEAM_TUNING_TOPICS="2"   # 可选：放大选题数
py -3.12 -m pytest tests/content_team/test_creative_live_tuning.py -q -s
```
