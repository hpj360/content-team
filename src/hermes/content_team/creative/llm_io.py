"""健壮 LLM JSON IO（实网联调 Round 12 的产出）。

实网联调暴露的三个真实问题，在此统一解决：

1. **响应截断**：``chat_json`` 不接受 ``max_tokens``，provider 默认上限易把长正文
   截断成非法 JSON。→ 直接用 ``chat(max_tokens=...)`` 并显式扩容重试。
2. **静默失败**：异常被吞导致"调用成功但空结果"。→ 统一记录 warning 日志。
3. **JSON 包裹**：markdown 围栏 / 前后有散文 / 尾部截断。→ 宽松提取 + 括号配平修复。

不改动 hermes core（不修改 ``workbench/llm.py``）。
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger("hermes.content_team")

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)

DEFAULT_MAX_TOKENS = 2048
DEFAULT_RETRIES = 3


def extract_json_lenient(text: str) -> dict[str, Any] | None:
    """从可能被包裹/截断的文本中宽松提取 JSON 对象。

    顺序：整体解析 → 围栏内 → 首个 ``{`` 起的**括号配平子串** →
    截断修复（回溯到最近的完整元素边界再补括号）。
    """
    if not text:
        return None
    text = text.strip()

    direct = _try_parse(text)
    if direct is not None:
        return direct

    for match in _FENCE_RE.findall(text):
        parsed = _try_parse(match.strip())
        if parsed is not None:
            return parsed
        start = match.find("{")
        if start >= 0:
            sub = _extract_first_balanced(match[start:])
            if sub is not None:
                return _try_parse(sub)

    start = text.find("{")
    if start < 0:
        return None
    fragment = text[start:]

    balanced = _extract_first_balanced(fragment)
    if balanced is not None:
        return _try_parse(balanced)

    # 截断修复：从尾部回溯到最近的逗号边界，逐个尝试补括号
    for candidate in _truncation_candidates(fragment):
        repaired = candidate + _closers(candidate)
        parsed = _try_parse(repaired)
        if parsed is not None:
            return parsed
    return None


def _try_parse(candidate: str) -> dict[str, Any] | None:
    # strict=False：允许字符串内出现字面换行等控制字符（实网联调发现
    # 模型常在 JSON 字符串里直接换行，严格模式会误判为非法）。
    try:
        value = json.loads(candidate, strict=False)
    except (json.JSONDecodeError, ValueError):
        return None
    if isinstance(value, dict):
        return value
    return {"value": value}


def _scan(text: str):
    """生成 (index, char, depth, in_string) 序列，供配平与截断分析。"""
    depth = 0
    in_str = False
    escape = False
    for idx, ch in enumerate(text):
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            yield idx, ch, depth, in_str
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        yield idx, ch, depth, in_str


def _extract_first_balanced(fragment: str) -> str | None:
    """截取从首个 ``{`` 起、depth 归零的完整子串（忽略其后散文）。"""
    saw_open = False
    for idx, ch, depth, in_str in _scan(fragment):
        if in_str:
            continue
        if ch == "{":
            saw_open = True
        if saw_open and ch == "}" and depth == 0:
            return fragment[: idx + 1]
    return None


def _truncation_candidates(fragment: str, *, limit: int = 6) -> list[str]:
    """截断修复候选：从尾部最近的逗号边界逐级回退（不含该逗号）。"""
    comma_positions: list[int] = []
    for idx, ch, depth, in_str in _scan(fragment):
        if not in_str and ch == "," and depth >= 1:
            comma_positions.append(idx)
    candidates: list[str] = []
    for pos in reversed(comma_positions[-limit:]):
        candidates.append(fragment[:pos])
    # 兜底：去掉尾部未闭合字符串后直接补括号
    head = fragment
    if head.count('"') % 2 == 1:
        head = head[: head.rfind('"')]
    candidates.append(re.sub(r"[,:]\s*$", "", head))
    return candidates


def _closers(fragment: str) -> str:
    """按栈补全未闭合的 ``}`` / ``]``（字符串内不计）。"""
    stack: list[str] = []
    for _idx, ch, _depth, in_str in _scan(fragment):
        if in_str:
            continue
        if ch in "{[":
            stack.append(ch)
        elif ch in "}]" and stack:
            stack.pop()
    return "".join("}" if c == "{" else "]" for c in reversed(stack))


def chat_json_safe(
    client: Any,
    messages: list[Any],
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    retries: int = DEFAULT_RETRIES,
    role: str = "",
) -> dict[str, Any]:
    """调用 LLM 并稳健解析 JSON。

    策略（避免"部分修复"覆盖"完整重试"）：
      1. **严格解析**成功 → 直接返回；
      2. 因 token 截断（``finish_reason == "length"``）且仍有重试 → **扩容重试**；
      3. 最后才用宽松修复兜底；仍失败返回 {}（并记 warning）。

    成本治理：调用前后经 ``cost.current_tracker()`` 记账与预算守卫（超限抛
    ``BudgetExceeded``，由调用方降级）。
    """
    from hermes.content_team.creative.cost import current_tracker, extract_usage

    tracker = current_tracker()
    attempt_tokens = max_tokens
    fallback: dict[str, Any] | None = None
    for attempt in range(1, retries + 1):
        if tracker is not None:
            tracker.check(role=role)
        try:
            response = client.chat(messages, max_tokens=attempt_tokens)
        except Exception as exc:  # noqa: BLE001
            logger.warning("llm chat failed (attempt %s): %s", attempt, exc)
            continue
        if tracker is not None:
            prompt_tokens, completion_tokens = extract_usage(response)
            tracker.record(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                role=role,
            )
        content = getattr(response, "content", "") or ""
        finish = getattr(response, "finish_reason", "")

        strict = _strict_parse(content)
        if strict is not None:
            return strict

        if fallback is None:
            fallback = extract_json_lenient(content)

        if finish == "length" and attempt < retries:
            attempt_tokens = min(attempt_tokens * 2, 8192)
            logger.warning(
                "llm response truncated (attempt %s, tokens=%s); retrying larger",
                attempt, attempt_tokens,
            )
            continue
        if fallback is not None:
            logger.warning("llm json repaired leniently (attempt %s)", attempt)
            return fallback

        logger.warning(
            "llm json parse failed (attempt %s, finish=%s, chars=%s): %r",
            attempt, finish, len(content), content[:180],
        )
        attempt_tokens = min(attempt_tokens * 2, 8192)
    return fallback or {}


def _strict_parse(text: str) -> dict[str, Any] | None:
    """只接受严格 JSON（整体 / 围栏内），不做截断修复。"""
    if not text:
        return None
    stripped = text.strip()
    parsed = _try_parse(stripped)
    if parsed is not None:
        return parsed
    for match in _FENCE_RE.findall(stripped):
        parsed = _try_parse(match.strip())
        if parsed is not None:
            return parsed
    return None
