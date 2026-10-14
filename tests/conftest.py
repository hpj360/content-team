"""Shared pytest fixtures for Hermes tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# 归档 skill 陈旧测试隔离（R24 技术债清理）
#
# 本项目自 hermes fork 后**有意归档**了设计/UI 类 skill（见 manifest.skills_archived），
# 其脚本已从磁盘移除，但仓库仍残留针对这些 skill 的测试（数量约占历史失败的全部）。
# 这些测试编码的是"归档前"的仓库快照，与本项目当前形态无关，故在收集阶段隔离；
# 文件保留在原处以备将来恢复归档 skill 时复用。
# ---------------------------------------------------------------------------

collect_ignore_glob = [
    "skills/*",  # 归档 skill 的脚本测试（figma_reader/ui_design_system/...）
    "test_mattpocock_skills.py",
    "test_grounded_citations_skill.py",
    "test_skill_consolidation.py",  # 断言归档/合并前的技能清单
]


@pytest.fixture
def reset_settings() -> Iterator[None]:
    """Clear the settings singleton before and after the test."""
    from hermes import config as _config
    _config._hermes_settings = None
    yield
    _config._hermes_settings = None


@pytest.fixture
def tmp_state_dir(
    tmp_path: Path, reset_settings: Iterator[None], monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Redirect HERMES_STATE_DIR/CACHE_DIR/PROFILE_PATH to tmp_path and reload settings."""
    state = tmp_path / "state"
    cache = tmp_path / "cache"
    profile = tmp_path / "profile.json"
    state.mkdir()
    cache.mkdir()
    monkeypatch.setenv("HERMES_STATE_DIR", str(state))
    monkeypatch.setenv("HERMES_CACHE_DIR", str(cache))
    monkeypatch.setenv("HERMES_PROFILE_PATH", str(profile))
    from hermes.config import get_settings
    get_settings(force_reload=True)
    yield tmp_path
