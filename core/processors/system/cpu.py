import psutil
from typing import Dict, List
from datetime import datetime
from clarity.schemas.system import CPUMetrics
import structlog

logger = structlog.get_logger()

class CPUMonitor:
    def __init__(self):
        self.interval = 1.0  # seconds
        self.history_size = 60  # Keep last 60 samples

    async def collect_metrics(self) -> CPUMetrics:
        try:
            cpu_percent = psutil.cpu_percent(interval=self.interval)
            per_cpu = psutil.cpu_percent(interval=self.interval, percpu=True)
            freq = psutil.cpu_freq()
            
            return CPUMetrics(
                timestamp=datetime.utcnow(),
                usage_percent=cpu_percent,
                per_cpu_percent=per_cpu,
                frequency_mhz=freq.current if freq else None,
                core_count=psutil.cpu_count(),
                load_average=psutil.getloadavg()
            )
        except Exception as e:
            logger.error("cpu.metrics_collection_failed", error=str(e))
            raise
