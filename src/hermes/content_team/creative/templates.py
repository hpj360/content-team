"""内容模板系统（Round 18）。

把可复用的写作框架沉淀为**模板**，供创作者在开书/开集/开场时预填：
- 内置模板：网文黄金三章、短剧单集 8 拍、分镜对话戏序列、导演风格包起点；
- 可扩展：``content-creation/`` 下的 Markdown 计划文件自动索引为"文档模板"。

纯数据 + 纯函数；`GET /api/creative/templates` 暴露。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_CONTENT_CREATION_DIR = _PROJECT_ROOT / "content-creation"


@dataclass
class Template:
    """写作模板。"""

    id: str
    name: str
    category: str          # novel / script / storyboard / directing
    description: str
    body: str              # 含 {占位符} 的模板正文
    variables: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "body": self.body,
            "variables": list(self.variables),
        }


BUILTIN_TEMPLATES: tuple[Template, ...] = (
    Template(
        id="novel-golden-three",
        name="网文黄金三章",
        category="novel",
        description="前三章结构模板：处境→金手指→第一次小爽点+悬念。",
        variables=["书名", "主角", "核心卖点", "金手指", "初始冲突"],
        body=(
            "《{书名}》黄金三章\n\n"
            "主角：{主角}　核心卖点：{核心卖点}\n\n"
            "第1章　处境\n"
            "- 前 500 字：主角 + 处境 + 抛出一个钩子\n"
            "- 金手指/核心设定亮相：{金手指}\n"
            "- 章尾钩子：\n\n"
            "第2章　冲突\n"
            "- 第一个明确冲突：{初始冲突}\n"
            "- 展示主角的选择\n"
            "- 章尾钩子：\n\n"
            "第3章　小爽点\n"
            "- 第一次小兑现（读者情绪回报）\n"
            "- 抛出更大的悬念\n"
        ),
    ),
    Template(
        id="short-drama-episode-8beat",
        name="短剧单集 8 拍",
        category="script",
        description="90 秒竖屏短剧单集节拍模板（含时长分配与卡点）。",
        variables=["集数", "集名", "本集冲突", "反转", "结尾钩子"],
        body=(
            "【第{集数}集】{集名}\n\n"
            "P1 冷开场(0-3s)　抓眼：\n"
            "P2 兑现(3-15s)　上集钩子落地：\n"
            "P3 施压(15-35s)　{本集冲突}：\n"
            "P4 回击(35-55s)　部分成功：\n"
            "P5 反转(55-70s)　{反转}：\n"
            "P6 代价(70-78s)　副作用：\n"
            "P7 悬置(78-85s)　强钩子：{结尾钩子}\n"
            "P8 出口(85-90s)　卡点：\n"
        ),
    ),
    Template(
        id="storyboard-dialogue-scene",
        name="对话戏分镜序列",
        category="storyboard",
        description="对峙/谈判场景的标准 7 镜序列（满足 2–5s 硬门）。",
        variables=["场次", "地点", "人物A", "人物B"],
        body=(
            "场次：{场次}　地点：{地点}\n\n"
            "镜1 WIDE STATIC 4.0s 建置：{人物A} 与 {人物B} 的空间关系\n"
            "镜2 MEDIUM STATIC 3.5s {人物A} 开口\n"
            "镜3 MEDIUM_CLOSE DOLLY 4.5s {人物B} 情绪上脸\n"
            "镜4 CLOSE STATIC 3.0s 关键道具入画\n"
            "镜5 MEDIUM PAN 3.5s 视线交接（轴线内回打）\n"
            "镜6 EXTREME_CLOSE ZOOM 2.5s 情绪峰值\n"
            "镜7 FULL TRACKING 4.0s 一方离场，关系落定\n"
        ),
    ),
    Template(
        id="directing-style-pack-starter",
        name="导演风格包起点",
        category="directing",
        description="填写风格参数 YAML 的脚手架（覆盖默认值）。",
        variables=["作品名", "风格定位", "参考片"],
        body=(
            "《{作品名}》导演风格包\n"
            "风格定位：{风格定位}　参考片：{参考片}\n\n"
            "风格参数:\n"
            "  lens_kit_mm: []\n"
            "  allowed_moves: []\n"
            "  forbidden_moves: []\n"
            "  motion_budget: low\n"
            "  key_light_ratio: \"\"\n"
            "  palette: []\n"
            "  avg_shot_length_s: 0\n"
            "  sound_policy: \"\"\n"
            "  negative_prompt_additions: []\n"
        ),
    ),
    Template(
        id="comedy-sketch-structure",
        name="素描喜剧结构",
        category="script",
        description="商业素描（Sketch）6 拍模板：高概念前提 + 三次升级 + 回调 + 情绪收尾。",
        variables=["前提", "怪人", "直人", "回调细节", "收尾情绪"],
        body=(
            "前提（一句话高概念）：{前提}\n"
            "怪人（恪守荒诞规则）：{怪人}\n"
            "直人（正常反应）：{直人}\n\n"
            "拍1 建立规则(15s)：\n"
            "拍2 升级一（小荒谬）：\n"
            "拍3 升级二（加码受压）：\n"
            "拍4 升级三（顶点临崩）：\n"
            "拍5 反转/摊牌：\n"
            "拍6 情绪收尾（回调「{回调细节}」→ {收尾情绪}）：\n"
        ),
    ),
    Template(
        id="mystery-game-outline",
        name="剧本杀/悬疑大纲",
        category="script",
        description="多视角悬疑大纲模板：角色私线 + 线索链 + 双反转 + 信息公平自检。",
        variables=["故事名", "主反转", "二次反转", "情感落点"],
        body=(
            "《{故事名}》悬疑结构\n\n"
            "角色（3–6，各持唯一信息）：\n"
            "- 角色A：公开身份 / 私线信息：\n"
            "- 角色B：公开身份 / 私线信息：\n"
            "- 角色C：公开身份 / 私线信息：\n\n"
            "线索链（公开 60% / 私线 40%）：\n"
            "- 线索1 → 指向 → 线索2 → 解锁 → 线索3\n\n"
            "时间线碰撞（同一时段的不同版本）：\n"
            "主反转：{主反转}（前置伏笔 ≥2）\n"
            "二次反转：{二次反转}（可选）\n"
            "情感落点：{情感落点}\n\n"
            "信息公平自检：所有结论所需线索是否都在公开信息中？\n"
        ),
    ),
    Template(
        id="worldbuilding-sheet",
        name="世界观设定表",
        category="novel",
        description="五层世界观（规则/势力/地理/经济/历史）填写模板，规则须含代价与限制。",
        variables=["世界名", "核心规则", "规则代价", "主要势力", "舞台"],
        body=(
            "《{世界名}》世界观设定\n\n"
            "规则层（含代价与限制）：\n"
            "- 核心规则：{核心规则}\n"
            "- 代价/限制：{规则代价}\n"
            "- 层级表：L1（前置/代价/失效）→ L2 → L3\n\n"
            "势力层（≥3，目标互相冲突）：\n"
            "- 势力A：目标 / 手段 / 底线 / 与主角关系\n"
            "- 势力B：\n"
            "- 势力C：\n\n"
            "地理层（每地图一条独有规则）：\n"
            "- {舞台}：独有规则 → 产生的新冲突\n\n"
            "经济层：资源从哪来 / 卡住谁\n"
            "历史层（伏笔来源，逐条登记 planned_resolution）：\n"
            "- 前史事件 → 伏笔：\n"
        ),
    ),
    Template(
        id="character-profile",
        name="人物档案",
        category="novel",
        description="人物档案模板：目标/弱点/缺陷根源/成长弧/四维状态/识别符。",
        variables=["姓名", "定位", "目标", "弱点", "识别符"],
        body=(
            "【{姓名}】定位：{定位}\n"
            "外在（含可画识别符）：{识别符}\n"
            "目标：{目标}\n"
            "弱点：{弱点}\n"
            "缺陷根源：\n"
            "成长弧（三阶段）：\n"
            "能力：初期 / 中期 / 后期\n"
            "关系：\n"
            "红线（不可违背）：\n\n"
            "四维状态（逐卷更新）：\n"
            "- 能力：进入 → 离开\n- 心理：进入 → 离开\n"
            "- 关系：进入 → 离开\n- 目标：进入 → 离开\n"
        ),
    ),
    Template(
        id="series-episode-outline",
        name="分集大纲",
        category="showrunning",
        description="多集/多卷大纲模板：每集钩子/冲突/高潮/悬念 + 跨集一致性红线。",
        variables=["系列名", "总集数", "核心记忆点"],
        body=(
            "《{系列名}》分集大纲（共 {总集数} 集）\n"
            "核心记忆点：{核心记忆点}\n\n"
            "| 集 | 钩子 | 冲突 | 高潮 | 结尾悬念 | 情绪配比 |\n"
            "|---|---|---|---|---|---|\n"
            "| 1 | | | | | 压 |\n| 2 | | | | | 小爽 |\n"
            "| 3 | | | | | 压 |\n| 4 | | | | | 爽 |\n\n"
            "跨集一致性红线：\n"
            "- 人物：\n- 世界观：\n- 视觉基调：\n"
        ),
    ),
    Template(
        id="stage-play-script",
        name="舞台剧剧本",
        category="script",
        description="舞台剧场次模板：舞台说明 + 角色调度 + 台词（无剪辑，靠台词与调度）。",
        variables=["剧名", "幕次", "地点", "角色A", "角色B"],
        body=(
            "《{剧名}》第{幕次}幕\n"
            "【场】{地点}·时间\n"
            "（舞台说明：布景/灯光/走位）\n\n"
            "{角色A}：（动作提示）台词。\n"
            "{角色B}：台词。\n\n"
            "【调度标注】走位 / 群戏位置 / 关键动作\n"
            "【幕末】转折或悬念\n"
        ),
    ),
    Template(
        id="variety-script",
        name="综艺台本",
        category="script",
        description="综艺/栏目台本：环节表 + 规则 + 预设冲突 + 突发兜底 + 剪辑点。",
        variables=["节目名", "期数", "本期主题", "时长"],
        body=(
            "【节目】{节目名}　【期数】{期数}　【时长】{时长}\n"
            "【本期主题】{本期主题}\n\n"
            "【环节一】开场（5 min）\n"
            "  主持人开场口播（钩子/看点/悬念）：\n"
            "  嘉宾介绍（每人 1 句记忆点）：\n"
            "【环节二】核心游戏（20 min）\n"
            "  规则（目标/步骤/胜负判定）：\n"
            "  预设冲突点 ×2：\n"
            "  突发应对 ×3（冷场/失控/超时）：\n"
            "【环节三】收尾（5 min）\n"
            "  金句提炼 / 下期预告：\n\n"
            "【剪辑点提示】笑点 / 反应 / 字幕点：\n"
        ),
    ),
    Template(
        id="oral-broadcast-script",
        name="口播脚本",
        category="script",
        description="口播/知识脚本：钩子→承诺→三点（结论+例子）→行动号召。",
        variables=["主题", "钩子", "承诺", "要点1", "要点2", "要点3"],
        body=(
            "主题：{主题}\n\n"
            "钩子(0-3s)：{钩子}\n"
            "承诺(3-8s)：{承诺}\n\n"
            "Point1：{要点1}（结论 + 一个例子）\n"
            "Point2：{要点2}（结论 + 一个例子）\n"
            "Point3：{要点3}（结论 + 一个例子）\n\n"
            "收尾(末5s)：行动号召 / 关注引导\n"
        ),
    ),
    Template(
        id="audio-drama-script",
        name="广播剧脚本",
        category="script",
        description="广播剧/有声剧脚本：音效与留白替代画面，声音即画面。",
        variables=["剧名", "场景", "角色A", "角色B"],
        body=(
            "《{剧名}》\n【场景】{场景}\n\n"
            "【音效】环境声（雨/脚步/门响）：\n"
            "{角色A}（情绪）：台词。\n"
            "{角色B}（情绪）：台词。\n"
            "【音乐】情绪提示（进入/骤停）：\n"
            "【留白】2 秒\n\n"
            "（听觉锚点：角色标志性声音/口癖）\n"
        ),
    ),
    Template(
        id="interactive-node-script",
        name="互动剧节点脚本",
        category="script",
        description="互动/分支叙事节点模板：节点+选项+变量+跳转+结局判定。",
        variables=["剧名", "节点号", "地点", "变量"],
        body=(
            "《{剧名}》节点 {节点号}　{地点}·时间\n"
            "（场景描述 / 画面）\n"
            "角色A：台词。\n\n"
            "—— 选项 ——\n"
            "  [A] 追问真相   → 变量: {变量}+1  → 跳转 N__\n"
            "  [B] 保持沉默   → 变量: {变量}-1  → 跳转 N__\n"
            "  [C] 出示证据   （需 item=证据）  → 跳转 N__\n\n"
            "【结局判定】条件 → 结局名：\n"
        ),
    ),
    Template(
        id="documentary-script",
        name="纪录片三栏脚本",
        category="script",
        description="纪录片脚本：画面 / 同期声 / 解说词 三栏对齐，解说词不抢同期声。",
        variables=["片名", "主题"],
        body=(
            "《{片名}》　主题：{主题}\n\n"
            "| 画面（Visual） | 同期声/访谈（Sync） | 解说词（VO） |\n"
            "|---|---|---|\n"
            "| | | |\n"
            "| | | |\n\n"
            "结构：钩子（异常/悬念）→ 展开（人物/事件）→ 升华（留画面，不点破）\n"
        ),
    ),
    Template(
        id="romance-misunderstanding-engine",
        name="言情误会引擎大纲",
        category="novel",
        description="现代言情误会引擎三层误会模板：信息差→身份差→立场差 + 体面化解与代价。",
        variables=["书名", "主角A", "主角B", "核心误解", "戳破时机"],
        body=(
            "《{书名}》误会引擎大纲\n\n"
            "主角A：{主角A}（心动证据，仅观众可见）\n"
            "主角B：{主角B}（心动证据，仅观众可见）\n\n"
            "第一层误会（信息差）：{核心误解}\n"
            "- 促成场景：\n- 误解强化场景（主角B 用行动'证实'误解）：\n"
            "第二层误会（身份差）：\n"
            "- 第三方破坏：\n- 双向独自误会（各自以为对方变心）：\n"
            "第三层误会（立场差）：\n"
            "- 价值观冲突：\n- 不可退让的红线（各自视角都成立）：\n\n"
            "戳破时机：{戳破时机}（尽量安排在主角付出不可逆代价之后）\n"
            "体面化解：误会成因必须可理解、可原谅（红线清单自检）\n"
            "结尾钩子：\n"
        ),
    ),
    Template(
        id="vertical-two-minute-episode",
        name="竖屏两分钟单集",
        category="script",
        description="120 秒竖屏短剧单集模板：三段四钩，钩子间隔 ≤35s，适配竖屏卡点节奏。",
        variables=["集数", "本集危机", "反转点", "结尾钩子"],
        body=(
            "【第{集数}集】竖屏 120s 单集\n\n"
            "【段一 起 (0-30s)】\n"
            "  冷开场钩子(0-5s)：\n"
            "  危机呈现：{本集危机}\n"
            "  钩点1(约28s) 小兑现或小升级：\n"
            "【段二 抗 (30-80s)】\n"
            "  施压升级（分镜建议：近景密度↑）：\n"
            "  钩点2(约55s) 认知反转：{反转点}\n"
            "  钩点3(约78s) 新增悬念：\n"
            "【段三 收 (80-120s)】\n"
            "  代价落地：\n"
            "  结尾钩子(108-116s)：{结尾钩子}\n"
            "  卡点(最后 4s)：\n\n"
            "【竖屏纪律】主体居中偏上；关键信息不入字幕安全区外；每镜 2–4s。\n"
        ),
    ),
    Template(
        id="animation-unit-episode",
        name="动画番剧单元集",
        category="script",
        description="动画单元+主线双引擎模板：单元承载新观众，主线承载老观众，含辨识度资产自检。",
        variables=["集数", "单元任务", "主线递进", "记忆点", "留主线钩"],
        body=(
            "【第{集数}集】单元+主线双引擎\n\n"
            "单元外壳（本集独立）\n"
            "  任务钩子：{单元任务}\n"
            "  单元三拍：遇事 → 受挫 → 破局（每拍有新信息）\n"
            "  单元收获：新盟友/新道具/新副本规则\n\n"
            "主线铅笔（本集一点，不喧宾夺主）\n"
            "  主线递进：{主线递进}（每集只推一格）\n"
            "  留主线钩（结尾 10s）：{留主线钩}\n\n"
            "辨识度资产自检（每集至少用一次）\n"
            "  角色识别符/口头禅：{记忆点}\n"
            "  标志性机位/转场：\n"
            "  声音签名（BGM 短乐句/音效）：\n\n"
            "【单元弧线离开主线】本集结束时观众'没看过前集也能懂，看了前集赚一笔'。\n"
        ),
    ),
    Template(
        id="storyboard-vertical-scene",
        name="竖屏竖构图镜头序列",
        category="storyboard",
        description="竖屏对峙场景 7 镜模板：竖构图景别映射 + 卡点切点 + 满足 2–5s 硬门。",
        variables=["场次", "地点", "人物A", "人物B"],
        body=(
            "场次：{场次}　地点：{地点}（竖屏 9:16）\n\n"
            "镜1 MEDIUM STATIC 3.5s 上下压缩景别：双人对峙半身连线\n"
            "镜2 CLOSE STATIC 3.0s {人物A} 情绪上脸（主体偏上，字幕下移）\n"
            "镜3 EXTREME_CLOSE DOLLY 4.0s {人物B} 瞳孔与手部小动作\n"
            "镜4 MEDIUM HANDHELD 4.5s 冲突肢体接触（match action 切）\n"
            "镜5 CLOSE TILT 2.5s 前景遮挡转视点（卡点：音效先入）\n"
            "镜6 EXTREME_CLOSE STATIC 2.0s 静帧强停（卡点镜）\n"
            "镜7 MEDIUM PAN 4.5s 一方孤立离框，关系落定\n\n"
            "【竖屏纪律】每镜景别与机位变化 ≥30°；字幕不入主体面部区。\n"
        ),
    ),
    Template(
        id="jubensha-character-book",
        name="剧本杀角色本/线索卡",
        category="script",
        description="沉浸式/剧本杀：角色本（私视角）+ 公共线索卡 + DM 手册要点。",
        variables=["剧本名", "角色名", "身份", "目标", "秘密"],
        body=(
            "《{剧本名}》角色本：{角色名}\n"
            "身份：{身份}　目标：{目标}　秘密：{秘密}\n"
            "已知线索：\n行动任务：\n\n"
            "【公共线索卡】（按轮次发放，公开:私线 ≈ 6:4）\n"
            "- 线索ID / 内容 / 指向 / 解锁条件\n\n"
            "【DM 手册要点】\n"
            "- 真实时间线：\n- 触发条件：\n- 控场与救场：\n- 结局判定：\n"
        ),
    ),
)


def list_document_templates() -> list[Template]:
    """把 ``content-creation/`` 下的 Markdown 索引为文档模板（若存在）。"""
    if not _CONTENT_CREATION_DIR.is_dir():
        return []
    templates: list[Template] = []
    for path in sorted(_CONTENT_CREATION_DIR.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        templates.append(
            Template(
                id=f"doc-{path.stem}",
                name=path.stem,
                category="document",
                description="来自 content-creation/ 的计划文档",
                body=text[:2000],
                variables=[],
            )
        )
    return templates


def list_templates() -> list[Template]:
    """全部模板（内置 + 文档）。"""
    return [*BUILTIN_TEMPLATES, *list_document_templates()]


def get_template(template_id: str) -> Template | None:
    for template in list_templates():
        if template.id == template_id:
            return template
    return None


def render_template(template_id: str, variables: dict[str, Any]) -> str | None:
    """渲染模板：替换 ``{占位符}``；缺省变量保留占位符（便于人工补全）。"""
    template = get_template(template_id)
    if template is None:
        return None
    rendered = template.body
    for key, value in (variables or {}).items():
        rendered = rendered.replace("{" + str(key) + "}", str(value))
    return rendered
