import psutil
from typing import Dict, List
from datetime import datetime
from clarity.schemas.system import NetworkMetrics, NetworkInterface
import structlog

logger = structlog.get_logger()

class NetworkMonitor:
    def __init__(self):
        self.history_size = 60

    async def collect_metrics(self) -> NetworkMetrics:
        try:
            net_io = psutil.net_io_counters()
            interfaces = self._get_interfaces()
            
            return NetworkMetrics(
                timestamp=datetime.utcnow(),
                bytes_sent=net_io.bytes_sent,
                bytes_recv=net_io.bytes_recv,
                packets_sent=net_io.packets_sent,
                packets_recv=net_io.packets_recv,
                interfaces=interfaces
            )
        except Exception as e:
            logger.error("network.metrics_collection_failed", error=str(e))
            raise

    def _get_interfaces(self) -> List[NetworkInterface]:
        interfaces = []
        for name, stats in psutil.net_if_stats().items():
            if stats.isup:
                interfaces.append(NetworkInterface(
                    name=name,
                    speed_mb=stats.speed,
                    is_up=stats.isup,
                    mtu=stats.mtu
                ))
        return interfaces
