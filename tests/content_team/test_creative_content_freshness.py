"""R19：语料库/失败手册/平台规则时效性 测试。"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from hermes.content_team.creative.content_freshness import (
    RULES_PATH,
    check_freshness,
    load_platform_rules,
    update_rules,
)

_CORPUS = Path(__file__).resolve().parents[2] / "knowledge" / "corpus"
_FAILURE_CASEBOOK = (
    Path(__file__).resolve().parents[2]
    / "skills" / "directing" / "references" / "failure-casebook.md"
)


# ---------------------------------------------------------------------------
# 语料库
# ---------------------------------------------------------------------------


def test_corpus_files_exist_and_wellformed():
    assert (_CORPUS / "README.md").is_file()
    for name in ("deconstruction-chekhov-chameleon.md", "deconstruction-luxun-kongyiji.md",
                 "failure-corpus.md"):
        path = _CORPUS / name
        assert path.is_file(), f"缺少 {name}"
        text = path.read_text(encoding="utf-8")
        assert text.lstrip().startswith("#")
        assert len(text) > 500
        # 拆解报告须含可迁移结论
        if name.startswith("deconstruction"):
            assert "可迁移" in text


def test_failure_casebook_expanded_to_f10():
    text = _FAILURE_CASEBOOK.read_text(encoding="utf-8")
    for code in ("F1", "F5", "F6", "F7", "F8", "F9", "F10"):
        assert code in text, f"failure casebook 缺少 {code}"


# ---------------------------------------------------------------------------
# 平台规则与时效性
# ---------------------------------------------------------------------------


def test_platform_rules_snapshot_shape():
    data = load_platform_rules()
    assert data["version"] >= 1
    assert data["updated_at"]
    assert data["review_cadence_days"] >= 1
    platforms = data["platforms"]
    assert {"番茄小说", "起点中文网", "红果短剧", "抖音", "小红书",
            "微信公众号", "微信视频号"} <= set(platforms)
    for spec in platforms.values():
        assert spec["form"] and spec["cadence"]


def test_check_freshness_not_stale_for_recent():
    report = check_freshness(today=date(2026, 10, 1))  # 快照 updated_at=2026-09-30
    assert report.age_days == 1
    assert report.stale is False
    assert report.next_review > report.updated_at


def test_check_freshness_stale_when_old():
    report = check_freshness(today=date(2028, 1, 1))
    assert report.stale is True
    assert report.age_days > report.review_cadence_days


def test_check_freshness_max_age_override():
    report = check_freshness(today=date(2026, 10, 20), max_age_days=10)
    assert report.stale is True


def test_check_freshness_invalid_date_treated_stale(tmp_path):
    path = tmp_path / "rules.json"
    path.write_text(json.dumps({"version": 1, "updated_at": "not-a-date",
                                "review_cadence_days": 30, "platforms": {}}),
                    encoding="utf-8")
    assert check_freshness(path, today=date(2026, 10, 1)).stale is True


def test_update_rules_bumps_version_and_adds_platform(tmp_path):
    path = tmp_path / "rules.json"
    path.write_text(RULES_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    before = load_platform_rules(path)

    updated = update_rules(
        path=path,
        updates={"platforms": {"B站": {"form": "short-video", "cadence": "中视频，三连"}}},
        today=date(2026, 12, 31),
    )
    assert updated["version"] == before["version"] + 1
    assert updated["updated_at"] == "2026-12-31"
    assert "B站" in updated["platforms"]
    # 原平台不受影响
    assert updated["platforms"]["番茄小说"]["chapter_words"] == [2000, 3000]


async def test_platform_rules_api(client):
    resp = await client.get("/api/platform-rules")
    assert resp.status_code == 200
    data = resp.json()
    assert "rules" in data and "freshness" in data
    assert data["freshness"]["platforms"]
    assert isinstance(data["freshness"]["stale"], bool)
