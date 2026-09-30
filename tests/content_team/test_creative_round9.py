"""Round 9（创作者视角 · B3）：多平台导出（TXT / EPUB / 红果剧本）。"""
from __future__ import annotations

import io
import zipfile

from hermes.content_team.creative.exporters import (
    export_novel_epub,
    export_novel_txt,
    export_short_drama_script,
    export_wechat_article,
)


async def _make_run(client):
    topic = (
        await client.post(
            "/api/topics", json={"title": "导出题", "description": "深海科考队失踪"}
        )
    ).json()["id"]
    return (
        await client.post("/api/creation/runs", json={"topic_id": topic})
    ).json()


# ---------------------------------------------------------------------------
# 纯函数
# ---------------------------------------------------------------------------


def test_export_txt_has_chapter_headings():
    text = export_novel_txt(
        "山海纪",
        [
            {"number": 1, "title": "开端", "body": "第一章正文。"},
            {"number": 2, "title": "转折", "body": "第二章正文。"},
        ],
    )
    assert text.startswith("山海纪")
    assert "第1章 开端" in text and "第2章 转折" in text
    assert "第一章正文。" in text


def test_export_epub_is_valid_zip_structure():
    payload = export_novel_epub(
        "山海纪",
        [{"number": 1, "title": "开端", "body": "正文第一段。\n第二段。"}],
    )
    assert payload[:2] == b"PK"
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        names = zf.namelist()
        assert names[0] == "mimetype"  # 必须首个
        info = zf.getinfo("mimetype")
        assert info.compress_type == zipfile.ZIP_STORED
        assert zf.read("mimetype") == b"application/epub+zip"
        assert "META-INF/container.xml" in names
        assert "OEBPS/content.opf" in names
        assert "OEBPS/nav.xhtml" in names
        assert "OEBPS/chapter1.xhtml" in names
        opf = zf.read("OEBPS/content.opf").decode("utf-8")
        assert "山海纪" in opf and "第1章 开端" in zf.read("OEBPS/chapter1.xhtml").decode("utf-8")


def test_export_redfruit_script_with_shots():
    text = export_short_drama_script(
        "外卖员逆袭",
        "第一场　内景／日\n\n他推门进来。",
        logline="外卖员被羞辱后逆袭",
        shots=[
            {
                "shot_number": 1,
                "shot_size": "WIDE",
                "camera_movement": "DOLLY",
                "description": "建置",
            }
        ],
    )
    assert "【短剧剧本】" in text
    assert "外卖员逆袭" in text
    assert "【分镜摘要】" in text
    assert "镜1｜WIDE｜DOLLY｜建置" in text
    assert "第一场" in text


def test_export_wechat_markdown():
    text = export_wechat_article("标题", "第一段\n第二段")
    assert text.startswith("# 标题")
    assert "第一段\n\n第二段" in text


# ---------------------------------------------------------------------------
# API 端到端
# ---------------------------------------------------------------------------


async def test_export_novel_txt_api(client):
    run = await _make_run(client)
    resp = await client.get(f"/api/novels/{run['artifacts']['novel_id']}/export")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    assert "attachment" in resp.headers.get("content-disposition", "")
    assert "第1章" in resp.text


async def test_export_novel_epub_api(client):
    run = await _make_run(client)
    resp = await client.get(
        f"/api/novels/{run['artifacts']['novel_id']}/export", params={"format": "epub"}
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/epub+zip")
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        assert zf.namelist()[0] == "mimetype"


async def test_export_script_redfruit_api(client):
    run = await _make_run(client)
    resp = await client.get(f"/api/scripts/{run['artifacts']['script_id']}/export")
    assert resp.status_code == 200
    assert "【短剧剧本】" in resp.text
    assert "镜1｜" in resp.text  # 含分镜摘要（管线已生成 3 镜）


async def test_export_404(client):
    resp = await client.get(
        "/api/novels/00000000-0000-0000-0000-000000000000/export"
    )
    assert resp.status_code == 404
