# 平台规则维护机制（R19）

> 配套机器可读快照：`src/hermes/content_team/creative/data/platform_rules.json`
> 检查工具：`creative/content_freshness.py`（`GET /api/platform-rules`）

## 一、为什么需要机制

平台规则（字数/时长/审核红线/变现）随政策与算法频繁变动。**过期规则 = 系统性误导**——
团队按旧规格生产，成片可能被限流或下架。因此规则必须**版本化、可检查、有复核节拍**。

## 二、版本化快照

```json
{
  "version": 3,
  "updated_at": "2026-09-30",
  "review_cadence_days": 180,
  "platforms": { "番茄小说": { "chapter_words": [2000, 3000], ... } }
}
```

- `version` 每次更新 +1；`updated_at` 盖章当日；`review_cadence_days` 为复核节拍。
- 规则以**结构化字段**表达（区间、红线列表、变现方式），便于机器校验与提示词注入。

## 三、新鲜度检查（自动）

```python
from hermes.content_team.creative.content_freshness import check_freshness
report = check_freshness()          # 可注入 today 便于测试
report.stale                        # True 表示已过期，需复核
report.next_review                  # 下次复核日期
```

- `stale=True` 时，编导方案与工作台应提示"平台规则待复核"。
- 建议接入定时任务：每 `review_cadence_days/2` 提醒一次（可由 content_team scheduler 触发）。

## 四、更新流程

1. **来源复核**：平台官方文档/创作者中心/公告（记录来源与日期）。
2. **字段更新**：只改受影响的字段，不重写整表。
3. **调用更新**：

```python
from hermes.content_team.creative.content_freshness import update_rules
update_rules(updates={"platforms": {"抖音": {"duration_seconds": [15, 90]}}})
# version+1，updated_at 盖今日
```

4. **同步文档**：`showrunning/references/platform-playbooks.md` 的人工说明同步更新。
5. **回归**：`pytest tests/content_team/test_creative_content_freshness.py`。

## 五、变更日志模板

| 日期 | 版本 | 平台 | 字段 | 旧值 → 新值 | 来源 |
|---|---|---|---|---|---|
| 2026-09-30 | 2 | 抖音 | duration_seconds | [15,60] → [15,90] | 官方公告 |

## 六、红线

- 规则快照**不得写入平台账号/密钥**等敏感信息；
- 数据只做**公开规则的结构化摘要**，不复制平台文档原文；
- `stale` 未复核前，不要把该平台规格当作承诺对外交付。
