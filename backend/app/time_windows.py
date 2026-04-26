from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass
class TimeWindows:
    timezone: str
    now_utc: str
    last_7_days_start_utc: str
    month_start_utc: str


def _resolve_zone(timezone_name: str) -> tuple[tzinfo, str]:
    try:
        zone = ZoneInfo(timezone_name)
        return zone, zone.key
    except ZoneInfoNotFoundError:
        return timezone.utc, "UTC"


def compute_time_windows(timezone_name: str) -> TimeWindows:
    zone, resolved_name = _resolve_zone(timezone_name)
    now_local = datetime.now(zone)
    now_utc = now_local.astimezone(timezone.utc)
    last_7_days_start_local = now_local - timedelta(days=7)
    month_start_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return TimeWindows(
        timezone=resolved_name,
        now_utc=now_utc.isoformat(),
        last_7_days_start_utc=last_7_days_start_local.astimezone(timezone.utc).isoformat(),
        month_start_utc=month_start_local.astimezone(timezone.utc).isoformat(),
    )
