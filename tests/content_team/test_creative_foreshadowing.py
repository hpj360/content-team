"""Round 4：伏笔生命周期一致性门测试。"""
from __future__ import annotations

from hermes.content_team.creative.gates import gate_foreshadowing_lifecycle


def _fs(**overrides):
    item = {
        "id": "F1",
        "content": "神秘信件来了",
        "planted_at": "第1章",
        "planned_resolution": "第3章回收",
        "status": "planted",
        "keyword": "信件",
    }
    item.update(overrides)
    return item


def _data(fs, bodies: dict[int, str]) -> dict:
    return {
        "foreshadowing": [fs],
        "chapter_bodies": [
            {"chapter_number": n, "body": b} for n, b in sorted(bodies.items())
        ],
    }


def test_lifecycle_ok_when_keyword_found():
    report = gate_foreshadowing_lifecycle(_data(_fs(), {1: "桌上有一封信件，字迹模糊。"}))
    assert report.passed, report.error_messages()


def test_lifecycle_missing_plant_is_error():
    # Round 5 起埋设章已写但未命中 → 区间错误 L004（替代全局 L001）
    report = gate_foreshadowing_lifecycle(_data(_fs(), {1: "与研究无关的章节。"}))
    assert "L004" in [i.code for i in report.errors]
    assert "L001" not in [i.code for i in report.errors]


def test_lifecycle_missing_keyword_falls_back_to_content_prefix():
    item = _fs()
    del item["keyword"]
    data = {
        "foreshadowing": [item],
        "chapter_bodies": [{"chapter_number": 2, "body": "……神秘信件……"}],
    }
    report = gate_foreshadowing_lifecycle(data)
    assert report.passed


def test_lifecycle_invalid_status_is_error():
    data = _data(_fs(status="odd"), {1: "信件出现。"})
    report = gate_foreshadowing_lifecycle(data)
    assert "L002" in [i.code for i in report.errors]


def test_lifecycle_no_foreshadowing_passes():
    data = {"foreshadowing": [], "chapter_bodies": [{"chapter_number": 1, "body": "..."}]}
    assert gate_foreshadowing_lifecycle(data).passed


def test_lifecycle_missing_planned_resolution_is_error():
    item = _fs(planned_resolution="")
    data = {
        "foreshadowing": [item],
        "chapter_bodies": [{"chapter_number": 1, "body": "信件出现。"}],
    }
    report = gate_foreshadowing_lifecycle(data)
    assert "L003" in [i.code for i in report.errors]


def test_lifecycle_planted_without_planned_resolution_is_error():
    item = _fs(planned_resolution="")
    body = "第一段：他收到来信件，却未明说寄信人。"
    data = {"foreshadowing": [item], "chapter_bodies": [{"chapter_number": 1, "body": body}]}
    report = gate_foreshadowing_lifecycle(data)
    # 埋设在正文可见（keyword 命中），仅回收位置缺失为 error
    assert "L003" in [i.code for i in report.errors]
    assert "L001" not in [i.code for i in report.errors]
