import logging
import sys
from typing import Optional
import structlog
from clarity.config.settings import settings

def setup_logging(log_level: Optional[str] = None):
    """Configure structured logging."""
    level = log_level or settings.LOG_LEVEL

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure root logger
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

def get_logger(name: str = __name__):
    """Get structured logger instance."""
    return structlog.get_logger(name)

# File: utils/monitoring/metrics.py
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    CollectorRegistry,
    multiprocess
)

# Registry setup
registry = CollectorRegistry()
if settings.PROMETHEUS_MULTIPROC_DIR:
    registry = multiprocess.MultiProcessCollector(registry)

# API metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total count of HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry
)

request_duration_seconds = Histogram(
    "request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=registry
)

active_users_gauge = Gauge(
    "active_users",
    "Number of currently active users",
    registry=registry
)

# Data processing metrics
data_processing_duration = Histogram(
    "data_processing_duration_seconds",
    "Duration of data processing operations",
    ["operation"],
    registry=registry
)

processed_items_total = Counter(
    "processed_items_total",
    "Total number of processed items",
    ["type"],
    registry=registry
)

processing_errors_total = Counter(
    "processing_errors_total",
    "Total number of processing errors",
    ["type", "error"],
    registry=registry
)

# ML metrics
model_prediction_duration = Histogram(
    "model_prediction_duration_seconds",
    "Duration of model predictions",
    ["model"],
    registry=registry
)

prediction_accuracy = Gauge(
    "prediction_accuracy",
    "Model prediction accuracy",
    ["model"],
    registry=registry
)

feature_importance = Gauge(
    "feature_importance",
    "Feature importance scores",
    ["feature", "model"],
    registry=registry
)

# System metrics
system_memory_usage = Gauge(
    "system_memory_usage_bytes",
    "System memory usage in bytes",
    registry=registry
)

system_cpu_usage = Gauge(
    "system_cpu_usage_percent",
    "System CPU usage percentage",
    registry=registry
)

# Cache metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache"],
    registry=registry
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache"],
    registry=registry
)

def record_request_metric(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics."""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

def record_processing_metric(operation: str, duration: float, item_type: str):
    """Record data processing metrics."""
    data_processing_duration.labels(operation=operation).observe(duration)
    processed_items_total.labels(type=item_type).inc()

def record_model_metric(model: str, duration: float, accuracy: float):
    """Record ML model metrics."""
    model_prediction_duration.labels(model=model).observe(duration)
    prediction_accuracy.labels(model=model).set(accuracy)
