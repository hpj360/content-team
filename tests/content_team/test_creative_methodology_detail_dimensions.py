"""细节维度方法论契约测试（场景细节工程 + 情感冲突外化）。"""
from __future__ import annotations

from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SCENE_DETAIL = _REPO / "skills/novel-writing/references/scene-detail-engineering.md"
_EMOTION_CONFLICT = _REPO / "skills/novel-writing/references/emotion-conflict-externalization.md"


def test_scene_detail_engineering_exists():
    """场景细节工程文件存在且非空。"""
    assert _SCENE_DETAIL.is_file(), "场景细节工程文件不存在"
    text = _SCENE_DETAIL.read_text(encoding="utf-8")
    assert len(text) > 3500, "内容偏薄"
    assert text.count("##") >= 8, "应有九节结构（含标题）"


def test_emotion_conflict_externalization_exists():
    """情感冲突外化文件存在且非空。"""
    assert _EMOTION_CONFLICT.is_file(), "情感冲突外化文件不存在"
    text = _EMOTION_CONFLICT.read_text(encoding="utf-8")
    assert len(text) > 4200, "内容偏薄"
    assert text.count("##") >= 8, "应有九节结构（含标题）"


def test_scene_detail_five_dimensions():
    """场景细节工程包含五维矩阵（环境/动作/物件/感官/影响）。"""
    text = _SCENE_DETAIL.read_text(encoding="utf-8")
    assert "环境" in text and "动作" in text and "物件" in text
    assert "感官" in text and "影响" in text
    assert "密度纪律" in text or "密度" in text
    assert "视角过滤" in text


def test_emotion_conflict_four_channels():
    """情感冲突外化包含四通道（生理/动作/环境/心理）与五维外化。"""
    text = _EMOTION_CONFLICT.read_text(encoding="utf-8")
    assert "生理反应" in text or "生理" in text
    assert "动作释放" in text or "动作" in text
    assert "环境投射" in text or "环境" in text
    assert "心理" in text
    assert "冲突" in text and ("五维" in text or "外化" in text)


def test_before_after_examples_present():
    """两篇均包含前后对照演示。"""
    scene_text = _SCENE_DETAIL.read_text(encoding="utf-8")
    emotion_text = _EMOTION_CONFLICT.read_text(encoding="utf-8")
    assert "示例" in scene_text and ("原版" in scene_text or "对照" in scene_text)
    assert "示例" in emotion_text and ("原版" in emotion_text or "对照" in emotion_text)


def test_cross_references_deduplication():
    """去重：两篇文件交叉引用既有资产，不重复展开理论。"""
    scene_text = _SCENE_DETAIL.read_text(encoding="utf-8")
    emotion_text = _EMOTION_CONFLICT.read_text(encoding="utf-8")
    
    # scene-detail 应引用 scene-engineering / narratology-toolbox
    assert "scene-engineering" in scene_text or "场景工程" in scene_text
    assert "narratology-toolbox" in scene_text or "叙述学" in scene_text
    
    # emotion-conflict 应引用 narratology-toolbox / character-bible
    assert "narratology-toolbox" in emotion_text or "自由间接引语" in emotion_text
    assert "character-bible" in emotion_text or "角色" in emotion_text


def test_templates_parseable():
    """新增模板（scene-detail-expansion / emotion-curve-card）可解析。"""
    from hermes.content_team.creative.templates import get_template
    
    t1 = get_template("scene-detail-expansion")
    assert t1 is not None, "场景扩写模板不存在"
    assert "五维细节" in t1.body
    assert len(t1.variables) >= 2
    
    t2 = get_template("emotion-curve-card")
    assert t2 is not None, "情感曲线卡模板不存在"
    assert "四通道" in t2.body
    assert len(t2.variables) >= 2


def test_skill_registration():
    """两篇已登记进 novel-writing/SKILL.md。"""
    skill_md = _REPO / "skills/novel-writing/SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    assert "scene-detail-engineering" in text, "场景细节工程未登记"
    assert "emotion-conflict-externalization" in text, "情感冲突外化未登记"


def test_usage_guide_updated():
    """使用手册提及细节维度门或五维细节。"""
    usage = _REPO / "knowledge/usage-writing-with-content-team.md"
    if not usage.is_file():
        pytest.skip("使用手册不存在")
    text = usage.read_text(encoding="utf-8")
    assert "细节" in text or "五维" in text or "scene-detail" in text


def test_no_wholesale_copying():
    """无整段引用痕迹（检查两篇文件不含受版权保护的台词/剧本）。"""
    scene_text = _SCENE_DETAIL.read_text(encoding="utf-8")
    emotion_text = _EMOTION_CONFLICT.read_text(encoding="utf-8")
    
    # 示例演示应是原创虚构，不应包含真实作品台词
    forbidden = ["影神图", "黑神话", "反相之地", "勘察组", "罗生门"]
    for term in forbidden:
        assert term not in scene_text, f"不应复制 {term} 原文"
        assert term not in emotion_text, f"不应复制 {term} 原文"
