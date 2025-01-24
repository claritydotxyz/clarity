import psutil
from typing import Dict
from datetime import datetime
from clarity.schemas.system import MemoryMetrics
import structlog

logger = structlog.get_logger()

class MemoryMonitor:
    def __init__(self):
        self.threshold_percent = 90

    async def collect_metrics(self) -> MemoryMetrics:
        try:
            virtual_memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return MemoryMetrics(
                timestamp=datetime.utcnow(),
                total_gb=virtual_memory.total / (1024**3),
                available_gb=virtual_memory.available / (1024**3),
                used_gb=virtual_memory.used / (1024**3),
                usage_percent=virtual_memory.percent,
                swap_used_gb=swap.used / (1024**3),
                swap_percent=swap.percent
            )
        except Exception as e:
            logger.error("memory.metrics_collection_failed", error=str(e))
            raise

