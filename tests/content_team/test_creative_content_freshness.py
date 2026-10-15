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


# ---------------------------------------------------------------------------
# R19 续：语料库索引与引用
# ---------------------------------------------------------------------------


def test_corpus_index_shape_and_files():
    from hermes.content_team.creative.corpus import CORPUS_DIR, load_corpus_index

    cases = load_corpus_index()
    assert len(cases) >= 17
    ids = {c.id for c in cases}
    assert {"chekhov-chameleon", "luxun-kongyiji", "ohenry-gift",
            "ibsen-dollhouse", "shortdrama-waimai-example",
            "chapter-form-wukong", "comedy-sketch", "mystery-game",
            "maupassant-necklace", "sophocles-oedipus",
            "poe-telltale-heart", "shakespeare-hamlet",
            "akutagawa-rashomon", "chekhov-cherry-orchard",
            "wilde-earnest", "maupassant-uncle-jules",
            "luxun-medicine"} <= ids
    for case in cases:
        assert case.file and (CORPUS_DIR / case.file).is_file(), f"缺文件 {case.file}"
        assert case.genres and case.tags and case.summary


def test_find_cases_filters():
    from hermes.content_team.creative.corpus import find_cases

    genting = find_cases(genre="言情")
    assert any(c.id == "ohenry-gift" for c in genting)

    drama = find_cases(form="short-drama")
    assert {c.id for c in drama} == {"shortdrama-waimai-example"}

    tagged = find_cases(tag="结尾反转")
    assert any(c.id == "ohenry-gift" for c in tagged)
    assert find_cases(genre="不存在") == []


def test_corpus_refs_for_text():
    from hermes.content_team.creative.corpus import corpus_refs_for, get_case

    refs = corpus_refs_for("复仇打脸 都市 短剧 外卖员")
    assert "shortdrama-waimai-example" in refs
    assert corpus_refs_for("") == []
    assert get_case("ohenry-gift") is not None
    assert get_case("nope") is None


async def test_corpus_api(client):
    resp = await client.get("/api/corpus")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 5 and data["matched"] >= 5

    filtered = await client.get("/api/corpus", params={"genre": "言情"})
    assert filtered.json()["matched"] >= 1

    one = await client.get("/api/corpus/ibsen-dollhouse")
    assert one.status_code == 200 and one.json()["form"] == "stage-play"
    assert (await client.get("/api/corpus/nope")).status_code == 404


async def test_beat_planner_includes_corpus_refs():
    from hermes.content_team.creative.planners import make_beat_sheet_planner
    from hermes.content_team.models.creative import CreationStage

    class T:
        title = "外卖员逆袭"
        description = "复仇打脸，都市短剧"

    plan = await make_beat_sheet_planner()(CreationStage.SCRIPT, {"topic": T()})
    assert "corpus_refs" in plan
    assert "shortdrama-waimai-example" in plan["corpus_refs"]


def test_corpus_new_paradigm_cases_indexed():
    """范式分析类案例（章回体/素描/剧本杀）已入库并可被题材引用。"""
    from hermes.content_team.creative.corpus import corpus_refs_for, find_cases, get_case

    for case_id in ("chapter-form-wukong", "comedy-sketch", "mystery-game"):
        case = get_case(case_id)
        assert case is not None and case.summary and case.tags

    # 题材/标签可命中
    assert find_cases(tag="章回体")
    assert find_cases(tag="视角分割")
    assert "mystery-game" in corpus_refs_for("悬疑 推理 剧本杀")


def test_corpus_paradigm_files_have_copyleft_notice():
    """范式分析文件须含版权声明（只做方法论迁移）。"""
    from hermes.content_team.creative.corpus import CORPUS_DIR

    for name in ("deconstruction-chapter-form-wukong.md",
                 "deconstruction-comedy-sketch.md",
                 "deconstruction-mystery-game.md"):
        text = (CORPUS_DIR / name).read_text(encoding="utf-8")
        assert "版权声明" in text
        assert "不复制" in text
