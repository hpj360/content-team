"""去 AI 味出口门（创作者视角 Round 8 · A2'）。

平台 AI 检测与读者敏感是账号权重风险，因此去 AI 味是**出口门**：任何
LLM/草稿文本在落库前必须经过本 pass。规则保守、可解释、可留痕。

与 `gates.py` 的 S005/S006 检查互补：门禁只「检出并扣分」，本模块「顺手修」。
"""
from __future__ import annotations

import re

from hermes.content_team.creative.gates import (
    AI_CLICHE_TOKENS,
    PSYCH_NARRATION_RE,
)

# 高频 AI 腔句式（保守替换，避免误伤正常表达）
# 「不仅…更是/而且…」两段式与三段式均覆盖
_PARALLEL_TRIPLE_RE = re.compile(
    r"不仅[^，。！？]{0,20}，(?:而且|更是|还)[^，。！？]{0,20}[，。]"
)
_NOT_BUT_RE = re.compile(r"不是[^，。！？]{0,20}，?而是[^，。！？]{0,20}[，。]")
_COPULA_EMPHASIS_RE = re.compile(r"无疑是[^，。！？]{0,20}[，。]")

_PSYCH_REPLACEMENT = "（动作描写）"


def apply_de_ai_pass(text: str) -> tuple[str, list[str]]:
    """对文本执行去 AI 味 pass。

    返回 ``(清洗后文本, 触发的规则名列表)``；未修改时规则列表为空。
    """
    if not text:
        return text, []

    applied: list[str] = []
    out = text

    for token in AI_CLICHE_TOKENS:
        if token in out:
            out = out.replace(token, "")
            applied.append(f"cliche:{token}")

    if PSYCH_NARRATION_RE.search(out):
        out = PSYCH_NARRATION_RE.sub(_PSYCH_REPLACEMENT, out)
        applied.append("psych-narration")

    for name, pattern in (
        ("parallel-triple", _PARALLEL_TRIPLE_RE),
        ("not-but", _NOT_BUT_RE),
        ("copula-emphasis", _COPULA_EMPHASIS_RE),
    ):
        new_out = pattern.sub("", out)
        if new_out != out:
            out = new_out
            applied.append(name)

    # 清理替换后的多余空格/标点堆叠（**保留换行**，否则会破坏场景/段落结构）
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    out = re.sub(r"([，。！？])\1+", r"\1", out)
    return out, applied


def de_ai_report(applied: list[str]) -> dict[str, object]:
    """把 pass 结果转为可留痕的报告片段。"""
    return {"de_ai_pass": True, "rules_applied": applied, "count": len(applied)}
