import pytest
from datetime import datetime, timedelta
from clarity.data.collector.watchers import SystemWatcher, FileWatcher
from clarity.core.processors.apps.browser import BrowserProcessor
from clarity.core.processors.apps.ide import IDEProcessor

async def test_system_watcher():
    events = []
    def callback(event):
        events.append(event)
    
    watcher = SystemWatcher(callback)
    await watcher.start()
    await asyncio.sleep(1)
    await watcher.stop()
    
    assert len(events) > 0
    assert all('pid' in event for event in events)

async def test_browser_collector():
    collector = BrowserProcessor()
    activity = await collector.collect_activity()
    
    assert activity.timestamp is not None
    assert isinstance(activity.active_browsers, list)
    assert isinstance(activity.productivity_score, float)
