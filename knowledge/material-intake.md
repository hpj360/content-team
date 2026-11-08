# 素材入库受理规范（Material Intake SOP）

> 本规范定义"本地素材 → 结构化摘录 → 语料入库"的受理流程（AGENTS.md #3 的执行细则）。

## 一、投放目录

- 目录：`tmp/materials/`（仓库所有者拖入即可；该目录默认 .gitignore，不入库）。
- 命名建议：`作品名_类型_来源.txt/md/pdf/docx`（如 `剑来_网文选段_自购正版.docx`）。

## 二、支持的格式

| 格式 | 说明 |
|---|---|
| .txt / .md | 直接读取 |
| .docx / .epub | 内置 Python（python-docx / zipfile）解析 |
| .pdf | LibreOffice Kit 渲染解析 |
| 对话直接粘贴 | 也可，不落盘即可执行 |
| 公开网页 URL | 由 Agent 抓取（web_fetch），标 URL 出处 |

## 三、摘录产出物（每份素材）

1. `breakdown-<素材名>.md`（语料逐案拆解）或并入既有范式文件；
2. 结构骨架 / 亮点机制 / 金句档案（短引 ≤2 句/条，标页码/章节）/ 梗名 / 可复用落点（映射到
   `hook-library` `beat-sheets` `shot-patterns` 等仓库资产）；
3. 出处字段登记"由仓库所有者提供素材（<日期>）"；
4. 不逐字成段照录；不可升级到 L3。

## 四、登记流程

1. 摘录文件写入 `knowledge/corpus/`；
2. `knowledge/corpus/index.json` 增加条目（form 按素材类型选 `breakdown`/`novel-paradigm`）；
3. `knowledge/corpus/README.md` 目录表加行；
4. 重生成 `knowledge/INDEX.md`（零漂移测试）；
5. 对应 Round 记入 `knowledge/creative-quality-model.md`；
6. `tests/content_team/` 增加该批次的契约测试。

## 五、可以由 Agent 替你下载的范围

- **可以**：公开报道、影评、访谈、百科、官方试读章节（网页公开可见部分）——抓取后引用与摘要，
  出处标 URL。
- **不可以**：完整版权作品全文的下载与入库（付费订阅整本、盗版电子书、扫描件）。

## 六、当前素材槽位（待升级）

| 槽位 | 对应文件 | 状态 |
|---|---|---|
| 持械入宋 双载体量产 | `paradigm-webnovel-hit-masters.md` 案 5 | 机制已入库；成段素材待补 |
| 剑来 语录体 | `paradigm-webnovel-hit-masters.md` 案 4 | 已收 3 条金句；可按你提供的选段扩档案 |
| 十日终焉 轮回关卡设计 | `paradigm-webnovel-hit-masters.md` 案 1 | 报道口径 4 条关卡机制；逐关拆解待素材 |
| 悟空传 金句流 | `paradigm-webnovel-hit-masters.md` 案 6 | 已收 2 句；可扩 |
