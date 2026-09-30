"""内容时效性（R19）：平台规则的新鲜度检查与更新提醒。

平台规则随政策/算法变动，过期规则比没有规则更危险（创作者按旧规则生产）。
本模块把规则**版本化 + 新鲜度可检查**，并给出复核提醒。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

RULES_PATH = Path(__file__).resolve().parent / "data" / "platform_rules.json"


@dataclass
class FreshnessReport:
    """规则新鲜度报告。"""

    version: int
    updated_at: str
    age_days: int
    review_cadence_days: int
    stale: bool
    next_review: str
    platforms: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "updated_at": self.updated_at,
            "age_days": self.age_days,
            "review_cadence_days": self.review_cadence_days,
            "stale": self.stale,
            "next_review": self.next_review,
            "platforms": self.platforms,
        }


def load_platform_rules(path: Path | None = None) -> dict[str, Any]:
    """载入平台规则快照。"""
    import json

    return json.loads((path or RULES_PATH).read_text(encoding="utf-8"))


def check_freshness(
    path: Path | None = None,
    *,
    today: date | None = None,
    max_age_days: int | None = None,
) -> FreshnessReport:
    """检查平台规则是否过期。

    ``today`` 可注入以便测试；``max_age_days`` 缺省取文件里的 review_cadence_days。
    """
    data = load_platform_rules(path)
    updated_raw = str(data.get("updated_at") or "")
    try:
        updated = datetime.strptime(updated_raw, "%Y-%m-%d").date()
    except ValueError:
        updated = date(1970, 1, 1)
    reference = today or date.today()
    age_days = max(0, (reference - updated).days)
    cadence = int(max_age_days or data.get("review_cadence_days") or 180)
    next_review = updated + timedelta(days=cadence)
    return FreshnessReport(
        version=int(data.get("version") or 0),
        updated_at=updated_raw,
        age_days=age_days,
        review_cadence_days=cadence,
        stale=age_days > cadence,
        next_review=next_review.isoformat(),
        platforms=sorted((data.get("platforms") or {}).keys()),
    )


def update_rules(
    *,
    path: Path | None = None,
    updates: dict[str, Any],
    today: date | None = None,
) -> dict[str, Any]:
    """合并平台规则并盖章新版本（version+1、updated_at=今天）。"""
    import json

    target = path or RULES_PATH
    data = load_platform_rules(target)
    platforms = data.setdefault("platforms", {})
    for name, patch in (updates.get("platforms") or {}).items():
        platforms.setdefault(name, {}).update(patch)
    for key in ("review_cadence_days", "sources_note"):
        if key in updates:
            data[key] = updates[key]
    data["version"] = int(data.get("version") or 0) + 1
    data["updated_at"] = (today or date.today()).isoformat()
    target.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return data
