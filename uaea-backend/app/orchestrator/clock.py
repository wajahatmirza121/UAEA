"""'Today' for the assistant — real date in Pakistan time, or TODAY_OVERRIDE for demos."""

from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

from app.config import settings


def today() -> datetime.date:
    if settings.today_override:
        try:
            return datetime.date.fromisoformat(settings.today_override)
        except ValueError:
            pass
    try:
        return datetime.datetime.now(ZoneInfo(settings.timezone)).date()
    except Exception:
        return datetime.date.today()


def days_until(d: datetime.date | str | None) -> int | None:
    if d is None:
        return None
    if isinstance(d, str):
        d = datetime.date.fromisoformat(d)
    return (d - today()).days
