"""R52：事件/影响方法论补全 + 细节体检单模板 + 实稿诊断报告 契约测试。"""
from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_DETAIL = _REPO / "skills" / "novel-writing" / "references" / "scene-detail-engineering.md"
_REPORT = _REPO / "content-creation" / "novel" / "45-吞兽维修师-细节维度执行报告.md"


def test_detail_doc_has_event_and_impact_sections():
    text = _DETAIL.read_text(encoding="utf-8")
    for concept in ("事件的可写化", "事件三要素", "因果链", "时间颗粒度", "事件类型矩阵"):
        assert concept in text, f"缺事件维度概念 {concept}"
    for concept in ("影响的外显四通道", "人的反应", "物的状态", "空间的变化", "后续选项"):
        assert concept in text, f"缺影响通道 {concept}"
    assert "事件—影响对账" in text or "事件-影响对账" in text, "缺事件-影响对账表"
    assert "三账=记账口径" in text or "记账口径" in text, "缺三账与四通道的口径关系说明"


def test_detail_doc_structure_intact():
    text = _DETAIL.read_text(encoding="utf-8")
    assert "## 十二、局限" in text, "局限节号应顺延为十二"
    assert text.count("## ") >= 12, "章节数异常"


def test_audit_template_registered():
    from hermes.content_team.creative.templates import get_template

    t = get_template("detail-audit-sheet")
    assert t is not None, "细节体检单模板未注册"
    for concept in ("五维体检", "影响四通道", "档位评级", "补写清单"):
        assert concept in t.body, f"模板缺 {concept}"


def test_execution_report_exists_and_complete():
    assert _REPORT.is_file(), "实稿诊断报告缺失"
    text = _REPORT.read_text(encoding="utf-8")
    assert text.lstrip().startswith("# ")
    for section in ("诊断口径", "总览表", "逐段诊断", "改写示范", "批量执行", "局限"):
        assert section in text, f"报告缺章节 {section}"
    # 6 段抽样：逐段小节数
    cases = re.findall(r"^###\s", text, flags=re.MULTILINE)
    assert len(cases) >= 6, f"抽样段不足 6（实际 {len(cases)}）"
    # 改写示范应使用档位标注
    assert "档3" in text or "档4" in text, "改写示范未标注具体化档位"


def test_execution_report_no_forbidden_words():
    text = _REPORT.read_text(encoding="utf-8")
    for word in ("打脸", "外卖员"):
        assert word not in text, f"报告出现禁词 {word}"
