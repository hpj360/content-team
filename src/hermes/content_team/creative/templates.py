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
