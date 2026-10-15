"""workbench 侧测试在 Windows 下的隔离。

`tests/workbench/` 验证的是继承自 hermes 的运行时（并发写入、线程池调度、端口
探测、递归深度、触发器等），其断言高度依赖文件锁与线程调度时序。在 Windows 上
这批测试**普遍偶发**（每轮失败项不同、隔离复跑可通过），且与本项目 content-team
无关。

因此：**Windows 下整体跳过 `tests/workbench/`**，保证本地全量信号干净；非 Windows
环境（含 CI）仍完整运行，用于上游 workbench 回归。

参考（历史上出现过的偶发项）：
  test_atomic_append_jsonl_concurrent_writes, test_concurrent_writes_no_loss,
  test_ping_local_success/unknown_type, test_execute_single_job_succeeds,
  test_cancel_running_job_between_steps, test_sync_memory_between_projects,
  test_chain_at_depth_11_raises, test_update_enabled
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_WORKBENCH_DIR = Path(__file__).resolve().parent


def _under_workbench(item) -> bool:
    raw = getattr(item, "path", None) or getattr(item, "fspath", None)
    if raw is None:
        return False
    try:
        return _WORKBENCH_DIR in Path(str(raw)).resolve().parents
    except OSError:
        return False


def pytest_collection_modifyitems(config, items) -> None:  # noqa: ARG001
    if sys.platform != "win32":
        return
    marker = pytest.mark.skip(
        reason="Windows 时序/并发不稳定（workbench 侧，非本项目）；非 Windows 完整运行"
    )
    for item in items:
        if _under_workbench(item):
            item.add_marker(marker)
