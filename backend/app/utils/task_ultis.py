"""Shared task helpers."""
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings


def infer_priority(base_weight: int) -> str:
    if base_weight >= 4:
        return "High"
    if base_weight >= 2:
        return "Medium"
    return "Low"


def business_today() -> date:
    return business_now().date()


def business_now() -> datetime:
    return datetime.now(ZoneInfo(settings.business_timezone))


def business_period_key(reference: datetime | None = None) -> str:
    current = _as_business_time(reference)
    return f"{current.year}-{current.month:02d}"


def business_month_utc_range(reference: datetime | None = None) -> tuple[datetime, datetime]:
    current = _as_business_time(reference)
    start = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return (
        start.astimezone(UTC).replace(tzinfo=None),
        end.astimezone(UTC).replace(tzinfo=None),
    )


def business_day_utc_range(day: date | None = None) -> tuple[datetime, datetime]:
    timezone = ZoneInfo(settings.business_timezone)
    start = datetime.combine(day or business_today(), datetime.min.time(), tzinfo=timezone)
    return start.astimezone(UTC), (start + timedelta(days=1)).astimezone(UTC)


def completion_business_date(completed_at: datetime) -> date:
    if completed_at.tzinfo is None:
        completed_at = completed_at.replace(tzinfo=UTC)
    return completed_at.astimezone(ZoneInfo(settings.business_timezone)).date()


def _as_business_time(reference: datetime | None) -> datetime:
    timezone = ZoneInfo(settings.business_timezone)
    if reference is None:
        return datetime.now(timezone)
    if reference.tzinfo is None:
        return reference.replace(tzinfo=timezone)
    return reference.astimezone(timezone)
