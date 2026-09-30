"""Round 12（实网联调产出）：稳健 LLM JSON IO + 草稿归一化 离线测试。

实网联调发现并修复三类真实缺陷：
1. 响应被 max_tokens 截断 → 非法 JSON；
2. 静默吞异常 → "成功但空"；
3. 模型照搬 SKILL.md 的 scenes schema，违反 harness 契约。
"""
from __future__ import annotations

from hermes.content_team.creative.builders_llm import normalize_draft
from hermes.content_team.creative.llm_io import (
    chat_json_safe,
    extract_json_lenient,
)


# ---------------------------------------------------------------------------
# 宽松 JSON 提取 / 截断修复
# ---------------------------------------------------------------------------


def test_extract_direct_and_fenced():
    assert extract_json_lenient('{"a": 1}') == {"a": 1}
    assert extract_json_lenient('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json_lenient('前言 {"a": 1} 后记') == {"a": 1}


def test_extract_repairs_truncated_json():
    # 被截断在字符串中途
    truncated = '{"title": "外卖员逆袭", "body": "第一场 内景/日\\n李默推门'
    data = extract_json_lenient(truncated)
    assert data is not None
    assert data.get("title") == "外卖员逆袭" or "body" in (data or {})
    # 被截断在数组/对象中途
    truncated2 = '{"scenes": [{"action": "x"}, {"action": "y"'
    data2 = extract_json_lenient(truncated2)
    assert isinstance(data2, dict)


def test_extract_returns_none_on_garbage():
    assert extract_json_lenient("完全不是 JSON") is None
    assert extract_json_lenient("") is None


# ---------------------------------------------------------------------------
# 截断扩容重试
# ---------------------------------------------------------------------------


class _FakeResp:
    def __init__(self, content, finish="stop"):
        self.content = content
        self.finish_reason = finish


class _TruncatingClient:
    """首次返回被截断 JSON（finish=length），扩容后返回完整 JSON。"""

    def __init__(self):
        self.calls: list[int] = []

    def chat(self, messages, max_tokens=None):
        self.calls.append(max_tokens or 0)
        if len(self.calls) == 1:
            return _FakeResp('{"title": "t", "body": "第一场 截断在', finish="length")
        return _FakeResp('{"title": "t", "body": "完整正文"}', finish="stop")


def test_chat_json_safe_expands_tokens_on_truncation():
    client = _TruncatingClient()
    data = chat_json_safe(client, [], max_tokens=256, retries=3)
    assert data["body"] == "完整正文"
    assert client.calls[0] == 256 and client.calls[1] == 512  # 扩容重试


class _AlwaysBadClient:
    def chat(self, messages, max_tokens=None):
        return _FakeResp("no json here", finish="stop")


def test_chat_json_safe_returns_empty_after_retries():
    assert chat_json_safe(_AlwaysBadClient(), [], max_tokens=128, retries=2) == {}


class _RaisingClient:
    def chat(self, messages, max_tokens=None):
        raise RuntimeError("boom")


def test_chat_json_safe_handles_exception():
    assert chat_json_safe(_RaisingClient(), [], retries=2) == {}


# ---------------------------------------------------------------------------
# 草稿归一化（兼容 SKILL.md 文档式 schema）
# ---------------------------------------------------------------------------


def test_normalize_contract_shape():
    out = normalize_draft({"title": "t", "body": "正文"})
    assert out["body"] == "正文" and out["drafter"] == "llm"


def test_normalize_scenes_shape_renders_body():
    """模型照搬 SKILL.md 的 scenes 结构 → 渲染为场次正文。"""
    data = {
        "success": True,
        "logline": "外卖员逆袭",
        "scenes": [
            {
                "scene_number": 1,
                "slugline": "内景·餐厅·夜",
                "purpose": "建置",
                "action": "李默被当众羞辱。",
                "dialogues": [{"character": "李默", "line": "我不干了。"}],
            },
            {
                "scene_number": 2,
                "slugline": "外景·街头·夜",
                "purpose": "转折",
                "action": "他亮出身份。",
                "dialogues": [],
            },
        ],
    }
    out = normalize_draft(data)
    assert out["adapted"] == "scenes"
    assert "第1场" in out["body"] and "第2场" in out["body"]
    assert "李默" in out["body"] and "我不干了。" in out["body"]
    assert out["title"] == "外卖员逆袭"


def test_normalize_text_shape():
    assert normalize_draft({"text": "纯文本正文"})["body"] == "纯文本正文"


def test_normalize_empty_returns_empty():
    assert normalize_draft({}) == {}
    assert normalize_draft({"scenes": []}) == {}
    assert normalize_draft("not a dict") == {}
