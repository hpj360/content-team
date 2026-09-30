# 提示词调优报告（R15 pass）

> 数据来源：`tests/content_team/test_creative_live_tuning.py`（实网，智谱 GLM-4-Flash）。
> 命令：`CONTENT_TEAM_LIVE_LLM=1 HERMES_LLM_PROVIDER=zai HERMES_LLM_MODEL=glm-4-flash pytest tests/content_team/test_creative_live_tuning.py -q -s`

## 一、变体定义

| 变体 | 契约要点 |
|---|---|
| v1 | 极简契约（只约定 JSON 形状），模型自由度高 |
| v2 | **硬性配额**：≥3 场次、每场动作+台词、300–900 字、结尾钩子 |
| v3 | v2 + **风格锚定强约束**（有指纹时贴合句长/段落节奏）+ 禁 AI 腔 |

## 二、实测结果

### 2.1 扩大样本（5 选题 × 3 变体，n=5，含 judge 语义分）

| 变体 | 平均字数 | 平均场景数 | 门禁通过率 | **judge 语义分** |
|---|---|---|---|---|
| v1 | 529.6 | 3–8 | 100% | 77.0 |
| **v2（选定）** | 505.2 | 3–5 | 100% | **89.0** |
| v3 | 258.8 | 3–4 | 100% | 57.0 |

明细（15 次生成 + 15 次 judge）：
```
waimai-counterattack  v1=630字/4场/90分   v2=348字/4场/90分   v3=203字/3场/85分
deepsea-mystery       v1=739字/8场/95分   v2=827字/5场/85分   v3=376字/4场/60分
craft-beer-heiress    v1=443字/3场/75分   v2=429字/3场/95分   v3=289字/3场/60分
mecha-trial           v1=473字/3场/75分   v2=443字/3场/85分   v3=214字/3场/40分
divorce-lawyer        v1=363字/3场/50分   v2=479字/3场/90分   v3=212字/3场/40分
```

### 2.2 首轮小样本（2 选题 × 3 变体，n=2，仅结构指标）

| 变体 | 平均字数 | 场景数 | 门禁通过率 |
|---|---|---|---|
| v1 | 573.5 | 3 / 6 | 100% |
| **v2** | 625.0 | 3 / 4 | 100% |
| v3 | 294.0 | 3 / 4 | 100% |

## 三、结论与决策

- **选定默认 v2**：扩大样本后，v2 在**语义评分（89.0）**上显著领先 v1（77.0）与 v3（57.0），
  且结构达标率 100%、字数落在合理区间；配额约束（场次/动作/台词/钩子）在提示层显式化，
  降低对模型发挥的依赖。`prompts.DEFAULT_VARIANT = "v2"` 与数据一致。
- **v3 明显偏弱**：字数偏短（258.8）且 judge 分最低（57.0）——风格锚定约束让模型"惜字"，
  在**未提供指纹时**反而劣化。保留 v3 仅供已设定指纹的高级用户手动选用。
- **v1 可用但方差大**（场景数 3–8、语义分波动 50–95），作为兜底变体保留。

## 四、局限（诚实声明）

- 样本量 5 选题 × 1 次/变体；结论方向性明确（v2 领先幅度大），但未做重复采样估计方差。
- judge 为 LLM 评议（GLM-4-Flash 同族），存在**同源偏好**；最终质量仍需人工抽检。
- 调优只看剧本阶段；小说/分镜/导演阶段的提示词变体尚未做同类对比。

## 五、复现步骤

```powershell
$env:PYTHONPATH="src"
$env:HERMES_LLM_PROVIDER="zai"
$env:HERMES_LLM_MODEL="glm-4-flash"
$env:CONTENT_TEAM_LIVE_LLM="1"
$env:CONTENT_TEAM_TUNING_TOPICS="2"   # 可选：放大选题数
py -3.12 -m pytest tests/content_team/test_creative_live_tuning.py -q -s
```
