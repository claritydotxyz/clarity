from typing import List, Optional
from datetime import datetime, timedelta
from O365 import Account
from clarity.schemas.calendar import CalendarEvent, EventType
import structlog

logger = structlog.get_logger()

class OutlookCalendarProcessor:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.account = None

    async def authenticate(self):
        try:
            self.account = Account((self.client_id, self.client_secret))
            if not self.account.is_authenticated:
                self.account.authenticate()
        except Exception as e:
            logger.error("outlook_calendar.auth_failed", error=str(e))
            raise

    async def get_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        if not self.account:
            await self.authenticate()
            
        try:
            schedule = self.account.schedule()
            calendar = schedule.get_default_calendar()
            q = calendar.new_query('start').greater_equal(start_date)
            q.chain('and').on_attribute('end').less_equal(end_date)
            
            events = calendar.get_events(query=q, include_recurring=True)
            
            return [
                CalendarEvent(
                    id=event.object_id,
                    title=event.subject,
                    start_time=event.start,
                    end_time=event.end,
                    type=EventType.MEETING if event.is_online_meeting else EventType.GENERAL,
                    platform="outlook"
                )
                for event in events
            ]
        except Exception as e:
            logger.error("outlook_calendar.event_fetch_failed", error=str(e))
            return []
