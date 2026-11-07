from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC timestamp (SQLite does not store tzinfo)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def normalize_branch(value: str) -> str:
    return value.strip().upper()
