from datetime import datetime, timedelta
from typing import Optional, Tuple
import pytz
from clarity.schemas.temporal import DaySegment, WeekSegment

def get_day_segment(hour: int) -> DaySegment:
    """Get day segment for given hour."""
    if 5 <= hour < 8:
        return DaySegment.EARLY_MORNING
    elif 8 <= hour < 12:
        return DaySegment.MORNING
    elif 12 <= hour < 17:
        return DaySegment.AFTERNOON
    elif 17 <= hour < 21:
        return DaySegment.EVENING
    else:
        return DaySegment.NIGHT

def get_week_segment(date: datetime) -> WeekSegment:
    """Get week segment for given date."""
    weekday = date.weekday()
    if weekday < 5:
        return WeekSegment.WEEKDAY
    return WeekSegment.WEEKEND

def parse_date_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    timezone: str = "UTC"
) -> Tuple[datetime, datetime]:
    """Parse and validate date range."""
    tz = pytz.timezone(timezone)
    end = datetime.now(tz) if not end_date else datetime.fromisoformat(end_date)
    start = (end - timedelta(days=30)) if not start_date else datetime.fromisoformat(start_date)
    
    if start > end:
        raise ValueError("Start date must be before end date")
    
    return start, end

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"
