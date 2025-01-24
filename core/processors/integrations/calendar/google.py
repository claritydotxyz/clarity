from typing import List, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from clarity.schemas.calendar import CalendarEvent, EventType
import structlog

logger = structlog.get_logger()

class GoogleCalendarProcessor:
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    def __init__(self, credentials_path: str):
        self.credentials_path = credentials_path
        self.service = None

    async def authenticate(self):
        try:
            creds = None
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('calendar', 'v3', credentials=creds)
        except Exception as e:
            logger.error("google_calendar.auth_failed", error=str(e))
            raise

    async def get_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        if not self.service:
            await self.authenticate()
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return [
                CalendarEvent(
                    id=event['id'],
                    title=event['summary'],
                    start_time=datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date'))),
                    end_time=datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date'))),
                    type=EventType.MEETING if 'meet.google.com' in event.get('location', '') else EventType.GENERAL,
                    platform="google"
                )
                for event in events_result.get('items', [])
            ]
        except Exception as e:
            logger.error("google_calendar.event_fetch_failed", error=str(e))
            return []
