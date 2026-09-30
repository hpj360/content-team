"""提示词变体注册表（R15 调优 pass 的基础设施）。

把 drafter 的"输出契约"版本化，使 A/B 调优可复现：
- ``v1``：极简契约（兼容优先，模型自由度高）；
- ``v2``：**硬性配额**（场景数/每场动作+台词/字数区间/结尾钩子），提高结构达标率；
- ``v3``：v2 + 风格锚定强约束（有指纹时要求句子节奏贴合）。

默认版本由 ``DEFAULT_VARIANT`` 决定，取值以实网评测（见 ``test_creative_live_tuning``
与 ``knowledge/creative-tuning-report.md``）为准。
"""
from __future__ import annotations

DRAFTER_CONTRACTS: dict[str, str] = {
    "v1": (
        "\n\n---\n\n"
        "## 输出契约（最高优先级，覆盖上文示例）\n"
        "你只输出一个 JSON 对象，且只含两个字段：\n"
        '{"title": "本段标题", "body": "完整正文纯文本"}\n'
        "- body 必须是可直接使用的正文纯文本；\n"
        "- 不要输出 scenes/characters/logline 等其它结构；不要输出解释或 markdown 围栏。"
    ),
    "v2": (
        "\n\n---\n\n"
        "## 输出契约（最高优先级，覆盖上文示例）\n"
        "你只输出一个 JSON 对象，且只含两个字段：\n"
        '{"title": "本段标题", "body": "完整正文纯文本"}\n'
        "硬性要求（必须全部满足）：\n"
        "1. 正文至少包含 3 个场次，每场以「第N场　内/外景·地点·时间」起头；\n"
        "2. 每场必须同时有可拍摄的动作描述与至少一句台词；\n"
        "3. 正文总字数控制在 300–900 字；\n"
        "4. 最后一场结尾必须留一个钩子（悬念/反转/宣战）；\n"
        "5. 不要输出 scenes/characters 等结构，不要 markdown 围栏。"
    ),
    "v3": (
        "\n\n---\n\n"
        "## 输出契约（最高优先级，覆盖上文示例）\n"
        "你只输出一个 JSON 对象："
        '{"title": "本段标题", "body": "完整正文纯文本"}\n'
        "硬性要求：\n"
        "1. 正文至少 3 个场次，格式「第N场　内/外景·地点·时间」；\n"
        "2. 每场含动作描述 + 至少一句台词；正文 300–900 字；结尾留钩子；\n"
        "3. **若提供了作者文风指纹，正文的句长节奏、段落长度与常用词必须贴合该指纹**；\n"
        "4. 禁止 AI 腔（不由得/顿时/心中暗道/值得一提的是）；\n"
        "5. 只输出 JSON，无围栏、无解释。"
    ),
}

DEFAULT_VARIANT = "v2"


def available_variants() -> tuple[str, ...]:
    return tuple(DRAFTER_CONTRACTS)


def drafter_contract(variant: str | None = None) -> str:
    """返回指定（或默认）版本的输出契约文本；未知版本回退默认。"""
    key = variant or DEFAULT_VARIANT
    return DRAFTER_CONTRACTS.get(key, DRAFTER_CONTRACTS[DEFAULT_VARIANT])
