from datetime import datetime
from zoneinfo import ZoneInfo

def make_timezone_aware(datetime_str: str, gmt_offset: int) -> datetime:

    if not datetime_str: # for last_login for example
        datetime_str = "2000-01-01T12:00:00"

    naive_dt = datetime.fromisoformat(datetime_str)

    if naive_dt.year <= 500:
        naive_dt = naive_dt.replace(year=1001)
        
    tz_name = f"Etc/GMT{(-gmt_offset):+d}"
    return naive_dt.replace(tzinfo=ZoneInfo(tz_name))