import pytest
from clarity.core.processors.apps.browser import BrowserProcessor
from clarity.core.processors.apps.ide import IDEProcessor
from clarity.core.processors.system.cpu import CPUMonitor
from clarity.core.processors.system.memory import MemoryMonitor

async def test_browser_processor():
    processor = BrowserProcessor()
    result = await processor.collect_activity()
    
    assert result.timestamp is not None
    assert isinstance(result.active_browsers, list)
    assert isinstance(result.productivity_score, float)

async def test_ide_processor():
    processor = IDEProcessor()
    result = await processor.collect_activity()
    
    assert result.timestamp is not None
    assert isinstance(result.active_files, list)
