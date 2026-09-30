"""质量门行为契约测试：加载 evals/evals.json 并逐条执行。

参照公开导演/分镜 skill 的 ``evals/evals.json`` 行为契约模式，把审查能力
固化为可回归的用例集。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from hermes.content_team.creative.gates import STAGE_GATES

EVALS_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "hermes"
    / "content_team"
    / "creative"
    / "evals"
    / "evals.json"
)


def _load_cases() -> list[dict]:
    data = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    return data["cases"]


CASES = _load_cases()


def test_evals_file_wellformed():
    data = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    assert data["version"] >= 1
    assert data["cases"]
    for case in data["cases"]:
        assert {"id", "stage", "input", "expect"} <= set(case)
        assert case["stage"] in STAGE_GATES


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_eval_case(case: dict):
    gate = STAGE_GATES[case["stage"]]
    report = gate(case["input"])
    expect = case["expect"]

    if "passed" in expect:
        assert report.passed is expect["passed"], (
            f"{case['id']}: passed={report.passed}, "
            f"errors={[i.code for i in report.errors]}"
        )
    if "error_codes" in expect:
        assert {i.code for i in report.errors} == set(expect["error_codes"])
    if "warn_codes" in expect:
        assert {i.code for i in report.warnings} == set(expect["warn_codes"])
