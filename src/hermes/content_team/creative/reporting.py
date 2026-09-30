"""审查报告渲染：把 CreationRun 渲染为可读 Markdown 报告。

用途：创作复盘、人工复核（NEEDS_REVISION 的处置依据）与归档。
纯函数、无 IO；导出入口见 API ``GET /api/creation/runs/{id}/report``。
"""
from __future__ import annotations

from typing import Any

from hermes.content_team.models.creative import CreationRun

_STAGE_ORDER = ("NOVEL", "SCRIPT", "STORYBOARD", "DIRECTING", "STORY_STATE",
                "STORY_FORESHADOWING")

_STAGE_LABELS = {
    "NOVEL": "小说",
    "SCRIPT": "剧本",
    "STORYBOARD": "分镜",
    "DIRECTING": "导演方案",
    "STORY_STATE": "故事状态",
    "STORY_FORESHADOWING": "伏笔生命周期",
    "UNKNOWN": "未知阶段",
}


def render_run_report(run: CreationRun) -> str:
    """渲染运行报告（Markdown）。"""
    lines: list[str] = []
    title = f"创作审查报告 · {run.id}"
    lines.append(f"# {title}")
    lines.append("")

    review = run.review or {}
    score = run.review_score
    verdict = _verdict_label(run.status.value if run.status else None)
    lines.append("## 总览")
    lines.append("")
    lines.append(f"- 运行 ID：`{run.id}`")
    lines.append(f"- 选题：`{run.topic_id}`")
    lines.append(f"- 阶段：{' → '.join(run.stages or []) or '（无）'}")
    lines.append(f"- 结果：**{verdict}**")
    lines.append(
        f"- 审查：总分 **{_fmt(score)}**"
        f"（通过线 {review.get('passed')}），"
        f"error {review.get('error_count', 0)} / warn {review.get('warning_count', 0)}"
    )
    lines.append(
        f"- 修订：{run.revise_rounds} 轮"
        f"（outcome={run.revision_outcome.value if run.revision_outcome else 'NONE'}）"
    )
    if run.error_message:
        lines.append(f"- 说明：{run.error_message}")
    lines.append("")

    dims = review.get("dimensions") or {}
    if dims:
        lines.append("## 维度得分")
        lines.append("")
        lines.append("| 维度 | 得分 |")
        lines.append("|---|---|")
        for name in ("structure", "compliance", "consistency", "pacing", "craft"):
            if name in dims:
                lines.append(f"| {name} | {_fmt(dims.get(name))} |")
        lines.append("")

    stage_issues = review.get("stage_issues") or {}
    if stage_issues:
        lines.append("## 问题清单")
        lines.append("")
        for stage in sorted(stage_issues, key=_stage_sort_key):
            label = _STAGE_LABELS.get(stage, stage)
            lines.append(f"### {label}（{stage}）")
            lines.append("")
            lines.append("| 编码 | 级别 | 说明 |")
            lines.append("|---|---|---|")
            for issue in stage_issues[stage]:
                lines.append(
                    f"| {issue.get('code')} | {issue.get('severity')} "
                    f"| {issue.get('message')} |"
                )
            lines.append("")

    if run.revise_log:
        lines.append("## 修订日志")
        lines.append("")
        lines.append("| # | 编码 | 是否修复 | 动作 |")
        lines.append("|---|---|---|---|")
        for idx, entry in enumerate(run.revise_log, start=1):
            lines.append(
                f"| {idx} | {entry.get('code')} | {entry.get('fixed')} "
                f"| {entry.get('action')} |"
            )
        lines.append("")

    artifacts = run.artifacts or {}
    if artifacts:
        lines.append("## 产物")
        lines.append("")
        for key in sorted(artifacts):
            lines.append(f"- `{key}` = `{artifacts[key]}`")
        lines.append("")

    lines.append("---")
    lines.append(
        "*由 content_team 独立审查器生成；error 级问题不因总分达标而豁免。*"
    )
    return "\n".join(lines)


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def _verdict_label(status: str | None) -> str:
    return {
        "SUCCEEDED": "通过",
        "NEEDS_REVISION": "需修订",
        "STOPPED": "已停止",
        "FAILED": "失败",
        "RUNNING": "进行中",
    }.get(status or "", status or "-")


def _stage_sort_key(stage: str) -> int:
    try:
        return _STAGE_ORDER.index(stage)
    except ValueError:
        return len(_STAGE_ORDER)
