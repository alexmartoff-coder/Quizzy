from datetime import datetime, timezone, timedelta

def get_moscow_now():
    # Moscow is UTC+3
    return datetime.now(timezone(timedelta(hours=3)))

def to_moscow_time(dt):
    if dt.tzinfo is None:
        # Assume it's UTC if no tzinfo
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=3)))
