# content-team

自媒体综合运营平台，服务于 1–5 人小型自媒体团队：**选题 → 创作 → 审查 → 修订 → 发布 → 数据** 全链同库。

基于 [hermes](https://github.com/hpj360/hermes) v0.6.0 框架 fork（保持包名 `hermes`，业务落在 `content_team` 子包）。

## 能力概览

| 层 | 内容 |
|---|---|
| 创作技能 | `skills/`：小说/剧本/分镜/导演/编导 5 技能 + 50 份方法论与实例库 references |
| 质量审查 | `creative/gates.py`（34 断言）· 独立审查器 · 硬门 · 自动修订闭环 · 行为契约 evals |
| 创作编排 | 4 阶段管线 + planner/drafter/critic/checker 四角色 + 一致性检索 + 记忆记账 |
| 风控 | 文风指纹（越用越像你）· 去 AI 味出口门 · token 成本护栏 |
| 交付 | 写作台 · 审查统计/报告 · 多平台导出（TXT/EPUB/红果/公众号）· 创作→发布桥 · 零构建工作台 |
| 语料/模板 | `knowledge/corpus/`（公版拆解 + 范式分析）· 模板系统（`GET /api/templates`） |

## 快速开始

```powershell
pip install fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" aiosqlite pydantic pydantic-settings python-dotenv
$env:PYTHONPATH="src"
uvicorn hermes.content_team.app:app --reload
```

- 工作台：`http://127.0.0.1:8000/dashboard`
- 接口文档：`http://127.0.0.1:8000/docs`

## 测试

```powershell
$env:PYTHONPATH="src"
py -3.12 -m pytest tests/content_team tests/test_creative_skills.py -q   # 本项目套件
py -3.12 -m pytest -q                                                    # 全量
```

实网联调（可选，默认跳过）：

```powershell
$env:CONTENT_TEAM_LIVE_LLM="1"
$env:HERMES_LLM_PROVIDER="zai"; $env:HERMES_LLM_MODEL="glm-4-flash"; $env:ZAI_API_KEY="..."
py -3.12 -m pytest tests/content_team/test_creative_llm_live.py tests/content_team/test_creative_live_pipeline.py -q -s
```

## 文档

- `CONTEXT.md` — 项目定位与术语表
- `knowledge/creative-methodology-overview.md` — 总纲：体系骨架（叙事有哪些零件）
- `knowledge/usage-writing-with-content-team.md` — 操作手册：写小说时的流程与命令
- `knowledge/asset-map.md` — 资产总图：任务路由的唯一入口
- `knowledge/INDEX.md` — 全量资产目录（生成式索引）
- `knowledge/corpus/README.md` — 语料库分族目录与同 IP 分工
- `knowledge/creative-quality-model.md` — 审查质量模型与迭代评分
- `knowledge/creative-tuning-report.md` — 提示词调优报告（实网）
- `docs/adr/` — 架构决策记录

## 许可

见仓库内各来源声明；技能文档为原创蒸馏，未复制第三方受版权内容。
