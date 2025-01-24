from typing import Dict, List, Optional
from datetime import datetime
import psutil
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from clarity.schemas.apps import MessageActivity, MessageType, Channel
from clarity.utils.monitoring.metrics import message_activity_counter
import structlog

logger = structlog.get_logger()

class MessagingProcessor:
    def __init__(self, slack_token: Optional[str] = None):
        self.slack_client = WebClient(token=slack_token) if slack_token else None
        
        self.messaging_apps = {
            "slack": MessageType.SLACK,
            "teams": MessageType.TEAMS,
            "discord": MessageType.DISCORD,
            "telegram": MessageType.TELEGRAM
        }

    async def collect_activity(self) -> MessageActivity:
        try:
            active_apps = self._get_active_apps()
            channels = await self._get_active_channels()
            metrics = self._calculate_metrics(channels)
            
            message_activity_counter.inc(metrics["total_messages"])
            
            return MessageActivity(
                timestamp=datetime.utcnow(),
                active_apps=active_apps,
                channels=channels,
                metrics=metrics
            )
        except Exception as e:
            logger.error("messaging.collection_failed", error=str(e))
            raise

    def _get_active_apps(self) -> List[Dict]:
        active_apps = []
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                proc_name = proc.info['name'].lower()
                for app_name, msg_type in self.messaging_apps.items():
                    if app_name in proc_name:
                        active_apps.append({
                            'type': msg_type,
                            'pid': proc.info['pid']
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return active_apps

    async def _get_active_channels(self) -> List[Channel]:
        channels = []
        if self.slack_client:
            try:
                response = await self.slack_client.conversations_list()
                for channel in response["channels"]:
                    if channel["is_member"]:
                        channels.append(Channel(
                            name=channel["name"],
                            type=MessageType.SLACK,
                            message_count=channel["num_members"]
                        ))
            except SlackApiError as e:
                logger.error("slack.channel_fetch_failed", error=str(e))
        return channels

    def _calculate_metrics(self, channels: List[Channel]) -> Dict:
        return {
            "total_channels": len(channels),
            "total_messages": sum(c.message_count for c in channels),
            "active_platforms": len(set(c.type for c in channels))
        }
