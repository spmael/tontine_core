"""Shared validation for public datetime inputs."""

from datetime import datetime


def require_aware_datetime(value: datetime, field_name: str) -> None:
    """Reject a naive datetime with guidance for constructing an aware value."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{field_name} must be timezone-aware; use datetime.timezone.utc "
            "or zoneinfo.ZoneInfo when constructing it."
        )
