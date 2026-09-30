"""多平台导出（创作者视角 Round 9 · B3）。

回应创作者日常动作「贴稿」：把创作产物导出为目标平台的格式，免去手改排版。

- **分章 TXT**：番茄小说 / 起点中文网等通用的「第N章 标题 + 正文」结构。
- **EPUB3**：stdlib ``zipfile`` 生成，可分发/手机与 Kindle 阅读。
- **短剧剧本**：红果式「【集】/场次/运镜占位」结构，直接可贴。

纯函数、无第三方依赖；API 层负责 Content-Disposition 与 MIME。
"""
from __future__ import annotations

import io
import zipfile
from html import escape
from typing import Any, Iterable

_EPUB_MIMETYPE = "application/epub+zip"


def export_novel_txt(
    title: str, chapters: Iterable[dict[str, Any]]
) -> str:
    """导出番茄/起点式分章 TXT。``chapters`` 项含 ``number/title/body``。"""
    lines = [title.strip(), ""]
    for chapter in chapters:
        number = chapter.get("number")
        chapter_title = str(chapter.get("title") or "").strip()
        heading = f"第{number}章 {chapter_title}".strip()
        lines.append(heading)
        lines.append("")
        lines.append(str(chapter.get("body") or "").strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def export_novel_epub(
    title: str,
    chapters: Iterable[dict[str, Any]],
    *,
    author: str = "content-team",
    language: str = "zh-CN",
) -> bytes:
    """生成最小可用的 EPUB3（mimetype 必须为首个且 STORED 条目）。"""
    chapter_list = list(chapters)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1) mimetype 必须第一个且不压缩
        zf.writestr(
            zipfile.ZipInfo("mimetype"), _EPUB_MIMETYPE,
            compress_type=zipfile.ZIP_STORED,
        )
        # 2) container
        zf.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<container version="1.0" '
            'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
            '<rootfiles><rootfile full-path="OEBPS/content.opf" '
            'media-type="application/oebps-package+xml"/></rootfiles>'
            "</container>",
        )
        # 3) css
        zf.writestr(
            "OEBPS/style.css",
            "body{font-family:serif;line-height:1.8;margin:1em;}"
            "h1{font-size:1.3em;}p{text-indent:2em;margin:0.5em 0;}",
        )
        # 4) 章节
        manifest_items: list[str] = []
        spine_items: list[str] = []
        nav_items: list[str] = []
        for idx, chapter in enumerate(chapter_list, start=1):
            number = chapter.get("number")
            chapter_title = escape(str(chapter.get("title") or "").strip())
            body = str(chapter.get("body") or "").strip()
            paragraphs = "".join(
                f"<p>{escape(p)}</p>" for p in body.splitlines() if p.strip()
            )
            file_name = f"chapter{idx}.xhtml"
            heading = f"第{number}章 {chapter_title}".strip()
            zf.writestr(
                f"OEBPS/{file_name}",
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<html xmlns="http://www.w3.org/1999/xhtml" '
                'xml:lang="zh-CN"><head>'
                f"<title>{heading}</title>"
                '<link rel="stylesheet" type="text/css" href="style.css"/>'
                f"</head><body><h1>{heading}</h1>{paragraphs}</body></html>",
            )
            manifest_items.append(
                f'<item id="c{idx}" href="{file_name}" '
                'media-type="application/xhtml+xml"/>'
            )
            spine_items.append(f'<itemref idref="c{idx}"/>')
            nav_items.append(
                f'<li><a href="{file_name}">{heading}</a></li>'
            )
        # 5) nav
        zf.writestr(
            "OEBPS/nav.xhtml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" '
            'xmlns:epub="http://www.idpf.org/2007/ops"><head>'
            f"<title>{escape(title)}</title></head><body>"
            '<nav epub:type="toc"><ol>'
            + "".join(nav_items)
            + "</ol></nav></body></html>",
        )
        # 6) opf
        zf.writestr(
            "OEBPS/content.opf",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
            'unique-identifier="bookid"><metadata '
            'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            f"<dc:title>{escape(title)}</dc:title>"
            f"<dc:creator>{escape(author)}</dc:creator>"
            f"<dc:language>{language}</dc:language>"
            '<dc:identifier id="bookid">urn:uuid:content-team</dc:identifier>'
            "</metadata><manifest>"
            '<item id="nav" href="nav.xhtml" '
            'media-type="application/xhtml+xml" properties="nav"/>'
            '<item id="css" href="style.css" media-type="text/css"/>'
            + "".join(manifest_items)
            + "</manifest><spine>"
            + "".join(spine_items)
            + "</spine></package>",
        )
    return buffer.getvalue()


_STAGE_RENDER_RULE = "【运镜】待导演/分镜补齐"


def export_short_drama_script(
    title: str,
    body: str,
    *,
    logline: str = "",
    shots: Iterable[dict[str, Any]] | None = None,
) -> str:
    """导出红果式短剧剧本（集/场次/人物/台词/运镜标注）。"""
    lines = ["【短剧剧本】", f"剧名：{title.strip()}"]
    if logline:
        lines.append(f"一句话：{logline.strip()}")
    lines.append("")
    if shots:
        lines.append("【分镜摘要】")
        for shot in shots:
            lines.append(
                f"镜{shot.get('shot_number')}｜{shot.get('shot_size')}｜"
                f"{shot.get('camera_movement')}｜"
                f"{str(shot.get('description') or '').strip()}"
            )
        lines.append("")
    lines.append(_STAGE_RENDER_RULE)
    lines.append("")
    lines.append(body.strip())
    return "\n".join(lines).rstrip() + "\n"


def export_wechat_article(title: str, body: str) -> str:
    """导出公众号友好的 Markdown（标题 + 正文，空行分段）。"""
    paragraphs = "\n\n".join(
        p.strip() for p in str(body or "").splitlines() if p.strip()
    )
    return f"# {title.strip()}\n\n{paragraphs}\n"
