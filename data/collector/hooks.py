from typing import Callable, Dict, List
from datetime import datetime
import asyncio
import structlog

logger = structlog.get_logger()

class DataCollectionHook:
    """Hook system for data collection events."""
    
    def __init__(self):
        self.pre_collect_hooks: List[Callable] = []
        self.post_collect_hooks: List[Callable] = []
        self.error_hooks: List[Callable] = []

    def register_pre_collect(self, hook: Callable):
        """Register hook to run before data collection."""
        self.pre_collect_hooks.append(hook)

    def register_post_collect(self, hook: Callable):
        """Register hook to run after data collection."""
        self.post_collect_hooks.append(hook)

    def register_error_handler(self, hook: Callable):
        """Register hook to handle errors."""
        self.error_hooks.append(hook)

    async def execute_pre_collect(self, context: Dict):
        """Execute all pre-collection hooks."""
        for hook in self.pre_collect_hooks:
            try:
                await hook(context)
            except Exception as e:
                logger.error("hook.pre_collect.failed", hook=hook.__name__, error=str(e))

    async def execute_post_collect(self, context: Dict, data: Dict):
        """Execute all post-collection hooks."""
        for hook in self.post_collect_hooks:
            try:
                await hook(context, data)
            except Exception as e:
                logger.error("hook.post_collect.failed", hook=hook.__name__, error=str(e))

    async def execute_error_handlers(self, context: Dict, error: Exception):
        """Execute all error handling hooks."""
        for hook in self.error_hooks:
            try:
                await hook(context, error)
            except Exception as e:
                logger.error("hook.error_handler.failed", hook=hook.__name__, error=str(e))
