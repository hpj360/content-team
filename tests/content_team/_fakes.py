"""共享测试替身：LLM 客户端 fake（实现 chat/chat_json 两条路径）。"""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any


class FakeLlmClient:
    """最小 LLM 客户端替身。

    - ``data``：``chat``/``chat_json`` 返回的 JSON 对象（会被序列化为 content）；
    - ``error``：注入异常以验证降级；
    - ``raw``：直接指定 content 字符串（用于测试截断/换行等脏响应）；
    - 记录 ``calls``（每次 max_tokens）与 ``messages``（最后一次）。
    """

    def __init__(
        self,
        data: Any = None,
        error: Exception | None = None,
        *,
        raw: str | None = None,
        finish_reason: str = "stop",
    ) -> None:
        self._data = data
        self._error = error
        self._raw = raw
        self._finish = finish_reason
        self.calls: list[int] = []
        self.messages: list[Any] | None = None

    def _content(self) -> str:
        if self._raw is not None:
            return self._raw
        return json.dumps(self._data if self._data is not None else {}, ensure_ascii=False)

    def chat(self, messages, *, max_tokens=None, **_kw):
        self.messages = messages
        self.calls.append(max_tokens or 0)
        if self._error is not None:
            raise self._error
        return SimpleNamespace(content=self._content(), finish_reason=self._finish)

    def chat_json(self, messages, **_kw):
        self.messages = messages
        if self._error is not None:
            raise self._error
        if isinstance(self._data, dict):
            return dict(self._data)
        return {}
