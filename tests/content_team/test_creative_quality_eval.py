"""Round 14：创意质量评测（离线）测试。"""
from __future__ import annotations

from hermes.content_team.creative.quality_eval import (
    DraftMetrics,
    compare_variants,
    load_quality_evals,
    measure_draft,
    summarize,
)

GOOD_SCRIPT = (
    "第一场　内景／日\n\n主角登场，交代处境与目标。\n\n"
    "第二场　内景／夜\n\n对手施压，冲突升级。\n\n"
    "第三场　外景／夜\n\n主角做出抉择，局势反转。"
)
CLICHE_SCRIPT = (
    "第一场　内景／日\n\n他不由得停下，心里想：不妙。\n\n"
    "第二场　内景／夜\n\n值得一提的是，对手施压。\n\n"
    "第三场　外景／夜\n\n主角做出抉择。"
)


def test_load_quality_evals_shape():
    data = load_quality_evals()
    assert data["topics"] and data["variants"]
    for topic in data["topics"]:
        assert {"id", "title", "description", "min_scenes", "chars_range"} <= set(topic)
    assert {v["id"] for v in data["variants"]} >= {"baseline", "style-anchored"}


def test_measure_good_draft_passes_metrics():
    topic = {"id": "t1", "title": "外卖员逆袭", "min_scenes": 3, "chars_range": [50, 4000]}
    m = measure_draft({"body": GOOD_SCRIPT}, topic=topic, variant_id="baseline")
    assert m.scene_count == 3 and m.scenes_ok
    assert m.chars_ok and m.gate_passed
    assert m.error_codes == []
    assert m.deai_hits_before == 0


def test_measure_bad_draft_flags_errors_and_cliche():
    topic = {"id": "t2", "title": "外卖员逆袭", "min_scenes": 3, "chars_range": [50, 4000]}
    m = measure_draft({"body": "第一场　内景／日\n\n只有一个场景。"}, topic=topic, variant_id="baseline")
    assert not m.scenes_ok
    assert "S004" in m.error_codes
    assert not m.gate_passed


def test_measure_counts_deai_hits_before_gate():
    topic = {"id": "t3", "title": "外卖员逆袭", "min_scenes": 3, "chars_range": [50, 4000]}
    m = measure_draft({"body": CLICHE_SCRIPT}, topic=topic, variant_id="baseline")
    assert m.deai_hits_before >= 2  # cliché + psych-narration


def test_measure_chars_range_enforced():
    topic = {"id": "t4", "title": "x", "min_scenes": 1, "chars_range": [10, 20]}
    m = measure_draft({"body": "第一场　内景／日\n" + "字" * 50}, topic=topic, variant_id="baseline")
    assert not m.chars_ok


def test_measure_retrieval_flag():
    topic = {"id": "t5", "title": "x", "min_scenes": 1, "chars_range": [1, 9999]}
    assert measure_draft(
        {"body": GOOD_SCRIPT}, topic=topic, variant_id="v", retrieval=[{"title": "第1章"}]
    ).retrieval_used


def test_summarize_and_compare_variants():
    topic = {"id": "t", "title": "题", "min_scenes": 3, "chars_range": [50, 4000]}
    rows = [
        measure_draft({"body": GOOD_SCRIPT}, topic=topic, variant_id="baseline"),
        measure_draft({"body": "第一场 x"}, topic=topic, variant_id="baseline"),
        measure_draft({"body": GOOD_SCRIPT}, topic=topic, variant_id="style-anchored"),
    ]
    summary = summarize(rows)
    assert summary["n"] == 3
    assert 0 <= summary["gate_pass_rate"] <= 1

    by_variant = compare_variants(rows)
    assert set(by_variant) == {"baseline", "style-anchored"}
    assert by_variant["style-anchored"]["gate_pass_rate"] == 1.0
    assert by_variant["baseline"]["gate_pass_rate"] == 0.5


def test_summarize_empty():
    assert summarize([]) == {"n": 0}


def test_draft_metrics_serializable():
    m = DraftMetrics(topic_id="t", variant_id="v")
    assert m.to_dict()["topic_id"] == "t"
