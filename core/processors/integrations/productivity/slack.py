from typing import Dict, List, Optional
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from clarity.schemas.productivity import (
    SlackMessage,
    SlackChannel,
    SlackStats
)
import structlog

logger = structlog.get_logger()

class SlackProcessor:
    def __init__(self, token: str):
        self.client = WebClient(token=token)

    async def get_user_messages(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[SlackMessage]:
        try:
            messages = []
            channels = await self._get_user_channels(user_id)
            
            for channel in channels:
                response = self.client.conversations_history(
                    channel=channel.id,
                    oldest=start_date.timestamp(),
                    latest=end_date.timestamp()
                )
                
                messages.extend([
                    SlackMessage(
                        text=msg["text"],
                        user=msg["user"],
                        channel=channel.name,
                        timestamp=float(msg["ts"]),
                        thread_ts=msg.get("thread_ts"),
                        reactions=len(msg.get("reactions", []))
                    )
                    for msg in response["messages"]
                    if msg["user"] == user_id
                ])
                
            return messages
        except SlackApiError as e:
            logger.error("slack.message_fetch_failed", error=str(e))
            return []

    async def _get_user_channels(self, user_id: str) -> List[SlackChannel]:
        try:
            response = self.client.users_conversations(user=user_id)
            
            return [
                SlackChannel(
                    id=channel["id"],
                    name=channel["name"],
                    is_private=channel["is_private"],
                    member_count=channel["num_members"]
                )
                for channel in response["channels"]
            ]
        except SlackApiError as e:
            logger.error("slack.channel_fetch_failed", error=str(e))
            return []

    async def get_user_stats(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> SlackStats:
        try:
            messages = await self.get_user_messages(user_id, start_date, end_date)
            channels = await self._get_user_channels(user_id)
            
            return SlackStats(
                total_messages=len(messages),
                channel_count=len(channels),
                threads_participated=len(set(m.thread_ts for m in messages if m.thread_ts)),
                total_reactions=sum(m.reactions for m in messages),
                active_channels=len(set(m.channel for m in messages))
            )
        except Exception as e:
            logger.error("slack.stats_calculation_failed", error=str(e))
            return SlackStats()
