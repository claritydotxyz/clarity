import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from clarity.schemas.collector import FileEvent, ProcessEvent
import structlog

logger = structlog.get_logger()

class SystemWatcher:
    """Watches system events and processes."""
    
    def __init__(self, callback):
        self.callback = callback
        self.process_cache = {}
        self.running = False

    async def start(self):
        """Start watching system events."""
        self.running = True
        while self.running:
            try:
                processes = await self._get_processes()
                events = self._detect_changes(processes)
                
                if events:
                    await self.callback(events)
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.error("system_watcher.error", error=str(e))

    async def stop(self):
        """Stop watching system events."""
        self.running = False

    async def _get_processes(self) -> Dict:
        """Get current process information."""
        processes = {}
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent']):
            try:
                processes[proc.info['pid']] = {
                    'name': proc.info['name'],
                    'status': proc.info['status'],
                    'cpu_percent': proc.info['cpu_percent']
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    def _detect_changes(self, current_processes: Dict) -> List[ProcessEvent]:
        """Detect process changes."""
        events = []
        
        # Check for new processes
        for pid, info in current_processes.items():
            if pid not in self.process_cache:
                events.append(ProcessEvent(
                    timestamp=datetime.utcnow(),
                    event_type='started',
                    pid=pid,
                    process_name=info['name']
                ))
        
        # Check for ended processes
        for pid in self.process_cache:
            if pid not in current_processes:
                events.append(ProcessEvent(
                    timestamp=datetime.utcnow(),
                    event_type='ended',
                    pid=pid,
                    process_name=self.process_cache[pid]['name']
                ))
        
        self.process_cache = current_processes
        return events

class FileWatcher(FileSystemEventHandler):
    """Watches file system events."""
    
    def __init__(self, callback, patterns: Optional[List[str]] = None):
        super().__init__()
        self.callback = callback
        self.patterns = patterns or ['*']
        self.observer = Observer()

    def start(self, path: str):
        """Start watching file system events."""
        self.observer.schedule(self, path, recursive=True)
        self.observer.start()
        logger.info("file_watcher.started", path=path)

    def stop(self):
        """Stop watching file system events."""
        self.observer.stop()
        self.observer.join()
        logger.info("file_watcher.stopped")

    def on_created(self, event):
        if not event.is_directory and self._match_pattern(event.src_path):
            self._handle_event('created', event.src_path)

    def on_modified(self, event):
        if not event.is_directory and self._match_pattern(event.src_path):
            self._handle_event('modified', event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and self._match_pattern(event.src_path):
            self._handle_event('deleted', event.src_path)

    def _match_pattern(self, path: str) -> bool:
        """Check if path matches any pattern."""
        from fnmatch import fnmatch
        return any(fnmatch(path, pattern) for pattern in self.patterns)

    def _handle_event(self, event_type: str, path: str):
        """Handle file system event."""
        event = FileEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            path=path,
            filename=path.split('/')[-1]
        )
        asyncio.create_task(self.callback(event))
