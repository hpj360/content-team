"""LLM 成本治理（Round 16）。

- ``UsageTracker``：累计每次调用的 token 用量，支持预算上限；
- 通过 ``contextvars`` 与调用栈解耦：``llm_io`` 自动向当前 tracker 记账，
  无需把 tracker 层层透传；测试可显式设置。
- 超预算时抛 ``BudgetExceeded``，由调用方（drafter/judge/reviser）的异常兜底
  降级为模板/空结果——即"预算耗尽自动降级"，不会拖垮整条管线。
"""
from __future__ import annotations

import contextvars
from dataclasses import dataclass, field
from typing import Any

_current_tracker: contextvars.ContextVar["UsageTracker | None"] = (
    contextvars.ContextVar("content_team_usage_tracker", default=None)
)


class BudgetExceeded(RuntimeError):
    """LLM 预算耗尽。"""


@dataclass
class UsageTracker:
    """累计 token 用量与调用次数（线程内；跨 asyncio.to_thread 通过 contextvar 副本传递）。"""

    budget_tokens: int | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    calls: int = 0
    by_role: dict[str, int] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def over_budget(self) -> bool:
        return self.budget_tokens is not None and self.total_tokens >= self.budget_tokens

    def check(self, *, role: str = "") -> None:
        """预算守卫：调用前检查，超限直接抛 ``BudgetExceeded``。"""
        if self.over_budget:
            raise BudgetExceeded(
                f"LLM budget exceeded: {self.total_tokens}/{self.budget_tokens} "
                f"tokens (role={role or 'unknown'})"
            )

    def record(
        self, *, prompt_tokens: int = 0, completion_tokens: int = 0, role: str = ""
    ) -> None:
        self.calls += 1
        self.prompt_tokens += max(0, int(prompt_tokens))
        self.completion_tokens += max(0, int(completion_tokens))
        if role:
            self.by_role[role] = self.by_role.get(role, 0) + int(
                prompt_tokens
            ) + int(completion_tokens)

    def to_dict(self) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "budget_tokens": self.budget_tokens,
            "over_budget": self.over_budget,
            "by_role": dict(self.by_role),
        }


def current_tracker() -> UsageTracker | None:
    """当前上下文中的 tracker（未设置返回 None）。"""
    return _current_tracker.get()


def set_tracker(tracker: UsageTracker | None) -> contextvars.Token:
    """设置当前 tracker，返回可用于恢复的 token。"""
    return _current_tracker.set(tracker)


def reset_tracker(token: contextvars.Token) -> None:
    _current_tracker.reset(token)


def extract_usage(response: Any) -> tuple[int, int]:
    """从 LlmResponse.raw 提取 (prompt_tokens, completion_tokens)。

    兼容 OpenAI 风格 ``usage`` 字段；缺失时返回 (0, 0)（不阻断）。
    """
    raw = getattr(response, "raw", None)
    if not isinstance(raw, dict):
        return 0, 0
    usage = raw.get("usage")
    if not isinstance(usage, dict):
        return 0, 0
    prompt = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
    completion = usage.get("completion_tokens") or usage.get("output_tokens") or 0
    try:
        return int(prompt), int(completion)
    except (TypeError, ValueError):
        return 0, 0
