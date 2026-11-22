from datetime import date, datetime
from zoneinfo import ZoneInfo

from settings import TIMEZONE


def now() -> datetime:
    """Return the current datetime in the configured timezone."""
    return datetime.now(ZoneInfo(TIMEZONE))


def today() -> date:
    """Return today's date in the configured timezone."""
    return now().date()