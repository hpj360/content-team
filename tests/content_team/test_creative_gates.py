"""质量门断言库单元测试（gates.py）。"""
from __future__ import annotations

from types import SimpleNamespace

from hermes.content_team.creative.gates import (
    ERROR_PENALTY,
    MAX_LOGLINE_CHARS,
    REVIEW_PASS_SCORE,
    WARN_PENALTY,
    GateIssue,
    GateReport,
    count_scenes,
    find_tokens,
    gate_directing,
    gate_novel,
    gate_script,
    gate_storyboard,
    score_reports,
    validate_shot_durations,
)

OK_SCRIPT_BODY = (
    "第一场 内景/日\n动作。\n第二场 外景/夜\n动作。\n第三场 内景/日\n动作。"
)


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def test_count_scenes_chinese_and_english():
    assert count_scenes("第一场 内景/日\n内容") == 1
    assert count_scenes("INT. ROOM - DAY\n内容\nEXT. STREET - NIGHT\n内容") == 2
    assert count_scenes("") == 0


def test_find_tokens():
    assert find_tokens("他不由得停下", ("不由得", "顿时")) == ["不由得"]
    assert find_tokens("平静", ("不由得",)) == []


def test_validate_shot_durations():
    assert validate_shot_durations([SimpleNamespace(shot_number=1, duration_seconds=3.0)]) == []
    errors = validate_shot_durations(
        [SimpleNamespace(shot_number=1, duration_seconds=0.5)]
    )
    assert errors and "镜头 1" in errors[0]


# ---------------------------------------------------------------------------
# NOVEL
# ---------------------------------------------------------------------------


def test_gate_novel_long_logline_is_error():
    report = gate_novel(
        {
            "title": "书名",
            "logline": "字" * (MAX_LOGLINE_CHARS + 1),
            "chapters": [{"body": "正文", "word_count": 2000}],
        }
    )
    assert not report.passed
    assert [i.code for i in report.errors] == ["N002"]


def test_gate_novel_warns_on_short_chapter():
    report = gate_novel(
        {"title": "书名", "logline": "核心", "chapters": [{"body": "短", "word_count": 10}]}
    )
    assert report.passed
    assert [i.code for i in report.warnings] == ["N006"]


# ---------------------------------------------------------------------------
# SCRIPT
# ---------------------------------------------------------------------------


def test_gate_script_ok():
    report = gate_script({"logline": "核心", "body": OK_SCRIPT_BODY})
    assert report.passed
    assert report.issues == []


def test_gate_script_empty_body():
    report = gate_script({"logline": "核心", "body": ""})
    assert not report.passed
    assert "S003" in [i.code for i in report.errors]


def test_gate_script_ai_cliche_and_psych_are_warnings():
    report = gate_script(
        {"logline": "核心", "body": OK_SCRIPT_BODY.replace("动作。", "他心里不由得一动。")}
    )
    codes = {i.code for i in report.warnings}
    assert {"S005", "S006"} <= codes
    assert report.passed  # 警告不阻断


def test_gate_script_compliance_blocks():
    report = gate_script(
        {"logline": "核心", "body": OK_SCRIPT_BODY + "\n枪支买卖"}
    )
    assert not report.passed
    assert "S007" in [i.code for i in report.errors]


# ---------------------------------------------------------------------------
# STORYBOARD
# ---------------------------------------------------------------------------


def _shots(*durations, sizes=None):
    sizes = sizes or ["WIDE", "MEDIUM", "CLOSE"]
    return [
        {
            "shot_number": i + 1,
            "description": f"镜{i + 1}",
            "shot_size": sizes[i % len(sizes)],
            "duration_seconds": d,
        }
        for i, d in enumerate(durations)
    ]


def test_gate_storyboard_ok():
    report = gate_storyboard({"shots": _shots(3.0, 3.0, 3.0)})
    assert report.passed


def test_gate_storyboard_segment_too_long():
    report = gate_storyboard({"shots": _shots(5.0, 5.0, 5.0, 5.0)})
    assert not report.passed
    assert "B004" in [i.code for i in report.errors]


def test_gate_storyboard_nonconsecutive():
    shots = _shots(3.0, 3.0)
    shots[1]["shot_number"] = 5
    report = gate_storyboard({"shots": shots})
    assert "B003" in [i.code for i in report.errors]


# ---------------------------------------------------------------------------
# DIRECTING
# ---------------------------------------------------------------------------


def test_gate_directing_requires_all_fields():
    report = gate_directing({"style": "写实", "tone": "", "pacing": "", "director_notes": ""})
    assert not report.passed
    assert {i.code for i in report.errors} == {"D002", "D003", "D004"}


# ---------------------------------------------------------------------------
# 评分
# ---------------------------------------------------------------------------


def test_score_reports_penalties():
    clean = [GateReport(stage="NOVEL")]
    assert score_reports(clean)[0] == 100.0

    with_error = [
        GateReport(stage="NOVEL", issues=[GateIssue("X", "err", "error", "structure")])
    ]
    assert score_reports(with_error)[0] == 100.0 - ERROR_PENALTY

    with_warn = [
        GateReport(stage="NOVEL", issues=[GateIssue("Y", "warn", "warn", "craft")])
    ]
    assert score_reports(with_warn)[0] == 100.0 - WARN_PENALTY

    # 分数不为负
    many = [GateReport(stage="X", issues=[GateIssue(f"E{i}", "e", "error") for i in range(20)])]
    assert score_reports(many)[0] == 0.0


def test_review_pass_score_is_reasonable():
    assert 0 < REVIEW_PASS_SCORE <= 100
