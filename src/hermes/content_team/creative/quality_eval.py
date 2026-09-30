"""创意质量评测（Round 14）。

回答"生成的内容到底好不好"，而不是只问"结构是否合法"。以**固定选题 × 变体**
衡量生成稿，产出可比较的指标，作为后续提示词调优的客观标尺（防自评 Goodhart）。

指标：
- ``draft_chars`` / ``chars_ok``：正文长度是否落在预期区间
- ``scene_count`` / ``scenes_ok``：场景数是否达标（短剧/剧本）
- ``gate_passed`` / ``error_codes``：结构质量门是否一次通过
- ``deai_hits_before``：过出口门之前命中的 AI 腔数量（衡量"生成是否自带 AI 味"）
- ``retrieval_used``：是否消费了检索命中（A1 不是摆设）

纯函数、可离线测试；实网运行由 live 套件驱动。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from hermes.content_team.creative.deai import apply_de_ai_pass
from hermes.content_team.creative.gates import count_scenes, gate_script

EVALS_PATH = Path(__file__).resolve().parent / "evals" / "creative_quality.json"


def load_quality_evals(path: Path | None = None) -> dict[str, Any]:
    """载入创意质量评测集。"""
    return json.loads((path or EVALS_PATH).read_text(encoding="utf-8"))


@dataclass
class DraftMetrics:
    """单次生成的指标。"""

    topic_id: str
    variant_id: str
    draft_chars: int = 0
    chars_ok: bool = False
    scene_count: int = 0
    scenes_ok: bool = False
    gate_passed: bool = False
    error_codes: list[str] = field(default_factory=list)
    warning_codes: list[str] = field(default_factory=list)
    deai_hits_before: int = 0
    retrieval_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def measure_draft(
    draft: dict[str, Any],
    *,
    topic: dict[str, Any],
    variant_id: str,
    logline: str | None = None,
    retrieval: list[dict[str, Any]] | None = None,
) -> DraftMetrics:
    """对一个草稿计算指标（剧本口径）。"""
    body = str((draft or {}).get("body") or "")
    chars = len(body)
    low, high = (topic.get("chars_range") or [0, 10**9])[:2]

    # 结构质量门（用 logline + body；logline 缺省取选题标题）
    report = gate_script({"logline": logline or topic.get("title") or "", "body": body})
    error_codes = [i.code for i in report.errors]
    warning_codes = [i.code for i in report.warnings]

    # AI 腔命中（过出口门之前）
    _, applied = apply_de_ai_pass(body)

    scene_count = count_scenes(body)

    return DraftMetrics(
        topic_id=str(topic.get("id") or ""),
        variant_id=variant_id,
        draft_chars=chars,
        chars_ok=bool(body) and low <= chars <= high,
        scene_count=scene_count,
        scenes_ok=scene_count >= int(topic.get("min_scenes") or 1),
        gate_passed=report.passed,
        error_codes=error_codes,
        warning_codes=warning_codes,
        deai_hits_before=len(applied),
        retrieval_used=bool(retrieval),
    )


def summarize(rows: list[DraftMetrics]) -> dict[str, Any]:
    """聚合指标（用于变体对比与阈值判断）。"""
    if not rows:
        return {"n": 0}
    n = len(rows)
    return {
        "n": n,
        "chars_ok_rate": round(sum(r.chars_ok for r in rows) / n, 3),
        "scenes_ok_rate": round(sum(r.scenes_ok for r in rows) / n, 3),
        "gate_pass_rate": round(sum(r.gate_passed for r in rows) / n, 3),
        "avg_chars": round(sum(r.draft_chars for r in rows) / n, 1),
        "avg_deai_hits": round(sum(r.deai_hits_before for r in rows) / n, 2),
        "retrieval_used_rate": round(sum(r.retrieval_used for r in rows) / n, 3),
    }


def compare_variants(
    rows: list[DraftMetrics],
) -> dict[str, dict[str, Any]]:
    """按变体分组聚合，用于"风格锚定是否更好"的对比。"""
    grouped: dict[str, list[DraftMetrics]] = {}
    for row in rows:
        grouped.setdefault(row.variant_id, []).append(row)
    return {variant: summarize(items) for variant, items in grouped.items()}
