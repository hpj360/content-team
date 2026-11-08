# 提示词调优报告（R15 pass）

> 数据来源：`tests/content_team/test_creative_live_tuning.py`（实网，智谱 GLM-4-Flash）。
> 命令：`CONTENT_TEAM_LIVE_LLM=1 HERMES_LLM_PROVIDER=zai HERMES_LLM_MODEL=glm-4-flash pytest tests/content_team/test_creative_live_tuning.py -q -s`

> **定位**：实网提示词调优数据报告（R15 pass + R23 语料注入对照）。
> **受众**：要查具体数值、变体对比与选定理由的人。
> **权威口径**：权威=实网调优数据；质量模型 R19/20/23 为其摘要，数值以本报告为准。
> **不做什么**：不承担逐轮台账（→ `creative-quality-model.md`）；不重复提示词正文。

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

## 三·补、语料注入效果（R23 实网对照）

命令：`pytest tests/content_team/test_creative_live_corpus.py -q -s`（同一选题、同一提示词变体 v2，
仅切换语料注入 on/off）：

| 变体 | 字数 | 场景数 | 门禁 | **judge 语义分** |
|---|---|---|---|---|
| corpus-off | 524 | 5 | 通过 | 60.0 |
| **corpus-on** | 417 | 3 | 通过 | **85.0** |

**结论**：语料注入带来 **+25 语义分**（60→85），且场景数收敛到目标 3 场——证明
R20/R22 的"语料进 prompt"不是摆设。（样本 n=1，方向性结论，扩大请调 `CONTENT_TEAM_TUNING_*`。）

## 三·补二、judge 去同源

`build_judge()` 支持跨 provider：配置 `CONTENT_TEAM_JUDGE_PROVIDER` / `CONTENT_TEAM_JUDGE_MODEL`
即用**不同厂商模型**评议（消除同源偏好）；未配置时回退同源 client。当前环境仅有 `zai` 凭据，
故实网仍为同源；接入第二个 provider 后自动生效。

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
