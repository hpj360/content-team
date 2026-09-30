"""创作能力（小说/剧本/分镜/导演/编导）与创作循环集成测试。

覆盖：
- 小说 CRUD 与章节管理（章节号自增、字数统计）
- 剧本 CRUD 与过滤
- 分镜 CRUD 与镜头管理
- 导演/编导方案 CRUD
- 创作循环：小说 → 剧本 → 分镜 → 导演 端到端
- CreativePipeline 的 builder/checker 分离与停止规则（单元）
"""
from __future__ import annotations

import pytest

from hermes.content_team.creative.pipeline import (
    SEGMENT_MAX_SECONDS,
    SHOT_MAX_SECONDS,
    SHOT_MIN_SECONDS,
    CreativePipeline,
    StageRound,
    validate_shot_durations,
)
from hermes.content_team.models.creative import (
    CameraMovement,
    CreationStage,
    ShotSize,
)


async def _create_topic(client, title="测试选题", description="选题描述") -> str:
    """通过 API 创建选题并返回其 ID。"""
    resp = await client.post(
        "/api/topics", json={"title": title, "description": description}
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# 小说与章节
# ---------------------------------------------------------------------------


async def test_create_novel(client):
    """POST /api/novels 创建小说。"""
    resp = await client.post(
        "/api/novels",
        json={
            "title": "山海纪",
            "genre": "东方奇幻",
            "logline": "少年寻父",
            "target_word_count": 200000,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "山海纪"
    assert data["genre"] == "东方奇幻"
    assert data["status"] == "PLANNING"
    assert data["word_count"] == 0
    assert data["target_word_count"] == 200000
    assert data["topic_id"] is None


async def test_list_novels_with_status_filter(client):
    """GET /api/novels?status=DRAFTING 按状态过滤。"""
    await client.post("/api/novels", json={"title": "甲"})
    novel_id = (await client.post("/api/novels", json={"title": "乙"})).json()["id"]
    await client.put(f"/api/novels/{novel_id}", json={"status": "DRAFTING"})

    resp = await client.get("/api/novels?status=DRAFTING")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "乙"


async def test_update_and_delete_novel(client):
    """PUT / DELETE /api/novels/{id}。"""
    novel_id = (
        await client.post("/api/novels", json={"title": "旧名"})
    ).json()["id"]

    resp = await client.put(
        f"/api/novels/{novel_id}",
        json={"title": "新名", "word_count": 1200},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "新名"
    assert resp.json()["word_count"] == 1200

    resp = await client.delete(f"/api/novels/{novel_id}")
    assert resp.status_code == 204
    assert (await client.get(f"/api/novels/{novel_id}")).status_code == 404


async def test_novel_not_found(client):
    """获取不存在的小说返回 404。"""
    resp = await client.get(
        "/api/novels/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404


async def test_create_and_list_chapters(client):
    """POST/GET /api/novels/{id}/chapters，章节号自增且字数自动统计。"""
    novel_id = (await client.post("/api/novels", json={"title": "长篇"})).json()["id"]

    r1 = await client.post(
        f"/api/novels/{novel_id}/chapters",
        json={"title": "第一章", "body": "你好 世界"},
    )
    assert r1.status_code == 201
    assert r1.json()["chapter_number"] == 1
    assert r1.json()["word_count"] == 4  # 去除空白后的字符数

    r2 = await client.post(
        f"/api/novels/{novel_id}/chapters", json={"title": "第二章"}
    )
    assert r2.json()["chapter_number"] == 2

    resp = await client.get(f"/api/novels/{novel_id}/chapters")
    assert resp.status_code == 200
    chapters = resp.json()
    assert [c["chapter_number"] for c in chapters] == [1, 2]


async def test_update_chapter_recomputes_word_count(client):
    """更新章节正文时自动重算字数。"""
    novel_id = (await client.post("/api/novels", json={"title": "书"})).json()["id"]
    chapter_id = (
        await client.post(
            f"/api/novels/{novel_id}/chapters",
            json={"title": "章", "body": "abc"},
        )
    ).json()["id"]

    resp = await client.put(
        f"/api/novels/{novel_id}/chapters/{chapter_id}",
        json={"body": "a b c d e"},
    )
    assert resp.status_code == 200
    assert resp.json()["word_count"] == 5


async def test_chapter_wrong_novel_returns_404(client):
    """章节不属于该小说时返回 404。"""
    novel_a = (await client.post("/api/novels", json={"title": "A"})).json()["id"]
    novel_b = (await client.post("/api/novels", json={"title": "B"})).json()["id"]
    chapter_id = (
        await client.post(
            f"/api/novels/{novel_a}/chapters", json={"title": "章"}
        )
    ).json()["id"]

    resp = await client.put(
        f"/api/novels/{novel_b}/chapters/{chapter_id}", json={"title": "X"}
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 剧本
# ---------------------------------------------------------------------------


async def test_create_and_filter_scripts(client):
    """POST /api/scripts 创建剧本，GET 支持类型过滤。"""
    resp = await client.post(
        "/api/scripts",
        json={
            "title": "都市微短剧",
            "script_type": "MICRO",
            "logline": "外卖员逆袭",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["script_type"] == "MICRO"
    assert data["status"] == "DRAFT"
    assert data["logline"] == "外卖员逆袭"

    await client.post(
        "/api/scripts", json={"title": "舞台剧", "script_type": "STAGE"}
    )

    resp = await client.get("/api/scripts?script_type=MICRO")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["script_type"] == "MICRO"


async def test_update_and_delete_script(client):
    """PUT / DELETE /api/scripts/{id}。"""
    script_id = (
        await client.post("/api/scripts", json={"title": "草稿"})
    ).json()["id"]

    resp = await client.put(
        f"/api/scripts/{script_id}", json={"status": "FINAL", "body": "正文"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "FINAL"
    assert resp.json()["body"] == "正文"

    assert (await client.delete(f"/api/scripts/{script_id}")).status_code == 204
    assert (await client.get(f"/api/scripts/{script_id}")).status_code == 404


# ---------------------------------------------------------------------------
# 分镜与镜头
# ---------------------------------------------------------------------------


async def test_create_storyboard_and_shots(client):
    """POST /api/storyboards 与 /shots，镜头号升序返回。"""
    script_id = (
        await client.post("/api/scripts", json={"title": "剧本"})
    ).json()["id"]

    sb_resp = await client.post(
        "/api/storyboards", json={"title": "分镜一", "script_id": script_id}
    )
    assert sb_resp.status_code == 201
    storyboard_id = sb_resp.json()["id"]
    assert sb_resp.json()["script_id"] == script_id

    shot_resp = await client.post(
        f"/api/storyboards/{storyboard_id}/shots",
        json={
            "shot_number": 2,
            "shot_size": "CLOSE",
            "camera_movement": "ZOOM",
            "description": "特写眼睛",
            "duration_seconds": 1.5,
        },
    )
    assert shot_resp.status_code == 201
    await client.post(
        f"/api/storyboards/{storyboard_id}/shots",
        json={"shot_number": 1, "description": "远景"},
    )

    resp = await client.get(f"/api/storyboards/{storyboard_id}/shots")
    assert resp.status_code == 200
    shots = resp.json()
    assert [s["shot_number"] for s in shots] == [1, 2]
    assert shots[1]["shot_size"] == "CLOSE"
    assert shots[1]["camera_movement"] == "ZOOM"
    assert shots[1]["duration_seconds"] == 1.5


async def test_create_storyboard_without_script(client):
    """分镜可独立于剧本创建（script_id 可空）。"""
    resp = await client.post("/api/storyboards", json={"title": "独立分镜"})
    assert resp.status_code == 201
    assert resp.json()["script_id"] is None


async def test_shot_wrong_storyboard_returns_404(client):
    """镜头不属于该分镜时返回 404。"""
    sb_a = (await client.post("/api/storyboards", json={"title": "A"})).json()["id"]
    sb_b = (await client.post("/api/storyboards", json={"title": "B"})).json()["id"]
    shot_id = (
        await client.post(
            f"/api/storyboards/{sb_a}/shots", json={"shot_number": 1}
        )
    ).json()["id"]

    resp = await client.put(
        f"/api/storyboards/{sb_b}/shots/{shot_id}", json={"description": "x"}
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 导演 / 编导方案
# ---------------------------------------------------------------------------


async def test_create_and_filter_directing_plans(client):
    """POST /api/directing-plans 创建方案，支持 role 过滤。"""
    script_id = (
        await client.post("/api/scripts", json={"title": "剧本"})
    ).json()["id"]

    resp = await client.post(
        "/api/directing-plans",
        json={
            "title": "导演阐述",
            "script_id": script_id,
            "role": "DIRECTOR",
            "style": "写实",
            "director_notes": "克制表演",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "DIRECTOR"

    await client.post(
        "/api/directing-plans",
        json={"title": "编导方案", "role": "SHOWRUNNER"},
    )

    resp = await client.get("/api/directing-plans?role=SHOWRUNNER")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["role"] == "SHOWRUNNER"


# ---------------------------------------------------------------------------
# 创作循环端到端
# ---------------------------------------------------------------------------


async def test_creation_run_end_to_end(client):
    """POST /api/creation/runs 跑通小说→剧本→分镜→导演。"""
    topic_id = await _create_topic(client, "深海迷航", "深海科考队失踪事件")

    resp = await client.post(
        "/api/creation/runs",
        json={"topic_id": topic_id, "max_rounds": 3},
    )
    assert resp.status_code == 201
    run = resp.json()
    assert run["status"] == "SUCCEEDED"
    assert run["current_stage"] is None
    assert run["rounds"] == 4  # 4 个阶段各 1 轮
    assert run["topic_id"] == topic_id
    assert run["artifacts"]["novel_id"]
    assert run["artifacts"]["script_id"]
    assert run["artifacts"]["storyboard_id"]
    assert run["artifacts"]["directing_plan_id"]
    assert len(run["stage_results"]) == 4

    # 验证产出实体可查
    novel = await client.get(f"/api/novels/{run['artifacts']['novel_id']}")
    assert novel.status_code == 200
    assert novel.json()["topic_id"] == topic_id

    chapters = await client.get(
        f"/api/novels/{run['artifacts']['novel_id']}/chapters"
    )
    assert len(chapters.json()) == 1

    shots = await client.get(
        f"/api/storyboards/{run['artifacts']['storyboard_id']}/shots"
    )
    assert len(shots.json()) == 3

    plan = await client.get(
        f"/api/directing-plans/{run['artifacts']['directing_plan_id']}"
    )
    assert plan.status_code == 200
    assert plan.json()["director_notes"]


async def test_creation_run_topic_not_found(client):
    """选题不存在时返回 404。"""
    resp = await client.post(
        "/api/creation/runs",
        json={
            "topic_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert resp.status_code == 404


async def test_creation_run_partial_stages(client):
    """只跑前两个阶段时止于剧本。"""
    topic_id = await _create_topic(client, "局部管线")
    resp = await client.post(
        "/api/creation/runs",
        json={"topic_id": topic_id, "stages": ["NOVEL", "SCRIPT"]},
    )
    assert resp.status_code == 201
    run = resp.json()
    assert run["status"] == "SUCCEEDED"
    assert "novel_id" in run["artifacts"]
    assert "script_id" in run["artifacts"]
    assert "storyboard_id" not in run["artifacts"]


async def test_list_and_get_creation_runs(client):
    """GET /api/creation/runs 与 /runs/{id}。"""
    topic_id = await _create_topic(client, "列表测试")
    run_id = (
        await client.post("/api/creation/runs", json={"topic_id": topic_id})
    ).json()["id"]

    resp = await client.get(f"/api/creation/runs?topic_id={topic_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.get(f"/api/creation/runs/{run_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == run_id

    resp = await client.get(
        "/api/creation/runs/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# CreativePipeline 单元测试（不依赖数据库）
# ---------------------------------------------------------------------------


async def test_pipeline_passes_all_stages():
    """builder/checker 全通过时依次完成所有阶段。"""
    calls: list[CreationStage] = []

    async def builder(stage, ctx):
        calls.append(stage)
        return {"stage": stage.value}

    async def checker(stage, output, ctx):
        return True, ""

    pipeline = CreativePipeline(
        builder, checker, stages=(CreationStage.NOVEL, CreationStage.SCRIPT)
    )
    result = await pipeline.run()
    assert result.success is True
    assert result.rounds == 2
    assert calls == [CreationStage.NOVEL, CreationStage.SCRIPT]
    assert all(isinstance(r, StageRound) for r in result.stage_results)


async def test_pipeline_retries_then_passes():
    """checker 前一轮失败、后一轮通过时，重试后继续。"""
    attempts = {"n": 0}

    async def builder(stage, ctx):
        return {}

    async def checker(stage, output, ctx):
        attempts["n"] += 1
        return (attempts["n"] >= 2), "尚未达标"

    pipeline = CreativePipeline(
        builder, checker, stages=(CreationStage.NOVEL,), max_rounds=3
    )
    result = await pipeline.run()
    assert result.success is True
    assert result.rounds == 2


async def test_pipeline_stops_after_max_rounds():
    """阶段持续失败时，达到 max_rounds 后停止并回报阻塞阶段。"""
    async def builder(stage, ctx):
        return {}

    async def checker(stage, output, ctx):
        return False, "始终不达标"

    pipeline = CreativePipeline(
        builder,
        checker,
        stages=(CreationStage.NOVEL, CreationStage.SCRIPT),
        max_rounds=2,
    )
    result = await pipeline.run()
    assert result.success is False
    assert result.rounds == 2
    assert result.current_stage == CreationStage.NOVEL
    assert "NOVEL" in result.stopped_reason


async def test_pipeline_artifacts_flow_to_next_stage():
    """上游阶段的 output 会合并进下游 builder 的上下文。"""
    seen: dict = {}

    async def builder(stage, ctx):
        if stage == CreationStage.NOVEL:
            return {"novel_id": "n-1"}
        seen.update(ctx)
        return {}

    async def checker(stage, output, ctx):
        return True, ""

    pipeline = CreativePipeline(
        builder, checker, stages=(CreationStage.NOVEL, CreationStage.SCRIPT)
    )
    await pipeline.run({"topic": "t"})
    assert seen["novel_id"] == "n-1"
    assert seen["topic"] == "t"


@pytest.mark.parametrize(
    "size,movement",
    [(ShotSize.WIDE, CameraMovement.DOLLY), (ShotSize.CLOSE, CameraMovement.ZOOM)],
)
def test_shot_enums_available(size, movement):
    """镜头枚举可用（景别/运镜）。"""
    assert size.value
    assert movement.value


# ---------------------------------------------------------------------------
# 分镜质量门（蒸馏自公开分镜方法：段 ≤15s、镜 2–5s）
# ---------------------------------------------------------------------------


def _shot(number: int, duration: float):
    """构造仅含时长/镜号的轻量镜头对象，用于校验纯函数。"""
    from types import SimpleNamespace

    return SimpleNamespace(shot_number=number, duration_seconds=duration)


def test_shot_duration_gate_passes_within_range():
    """镜 2–5s 且段 ≤15s 时无错误。"""
    shots = [_shot(1, 2.0), _shot(2, 3.0), _shot(3, 5.0)]
    assert validate_shot_durations(shots) == []
    assert sum(s.duration_seconds for s in shots) <= SEGMENT_MAX_SECONDS


def test_shot_duration_gate_rejects_too_short():
    """镜时长低于 2s 报错。"""
    errors = validate_shot_durations([_shot(1, SHOT_MIN_SECONDS - 0.1)])
    assert len(errors) == 1
    assert "镜头 1" in errors[0]


def test_shot_duration_gate_rejects_too_long():
    """镜时长高于 5s 报错。"""
    errors = validate_shot_durations([_shot(1, SHOT_MAX_SECONDS + 3.0)])
    assert len(errors) == 1
    assert "超出" in errors[0]


def test_shot_duration_gate_rejects_overlong_segment():
    """各镜合规但段总时长超过 15s 时报错。"""
    shots = [_shot(1, 5.0), _shot(2, 5.0), _shot(3, 5.0), _shot(4, 5.0)]
    errors = validate_shot_durations(shots)
    assert any("段时长" in e for e in errors)


async def test_creation_run_storyboard_respects_duration_gate(client):
    """默认管线产出的镜头满足时长硬门（端到端）。"""
    topic_id = (
        await client.post(
            "/api/topics", json={"title": "质量门选题", "description": "验证分镜时长门"}
        )
    ).json()["id"]

    run = (
        await client.post("/api/creation/runs", json={"topic_id": topic_id})
    ).json()
    assert run["status"] == "SUCCEEDED"

    shots = (
        await client.get(f"/api/storyboards/{run['artifacts']['storyboard_id']}/shots")
    ).json()
    assert shots
    for shot in shots:
        assert SHOT_MIN_SECONDS <= shot["duration_seconds"] <= SHOT_MAX_SECONDS
    assert sum(s["duration_seconds"] for s in shots) <= SEGMENT_MAX_SECONDS
