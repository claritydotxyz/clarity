from prometheus_client import Counter, Gauge, Histogram, Summary

# API Metrics
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

active_users = Gauge(
    'active_users',
    'Number of currently active users'
)

# Data Processing Metrics
data_processing_duration_seconds = Histogram(
    'data_processing_duration_seconds',
    'Duration of data processing tasks',
    ['type']
)

data_points_processed_total = Counter(
    'data_points_processed_total',
    'Total number of data points processed',
    ['source']
)

processing_errors_total = Counter(
    'processing_errors_total',
    'Total number of processing errors',
    ['type']
)

# ML Model Metrics
model_prediction_duration_seconds = Histogram(
    'model_prediction_duration_seconds',
    'Duration of model predictions',
    ['model_type']
)

model_accuracy = Gauge(
    'model_accuracy',
    'Model prediction accuracy',
    ['model_type']
)

training_duration_seconds = Histogram(
    'training_duration_seconds',
    'Duration of model training',
    ['model_type']
)

# Resource Metrics
memory_usage_bytes = Gauge(
    'memory_usage_bytes',
    'Current memory usage in bytes',
    ['type']
)

cpu_usage_percent = Gauge(
    'cpu_usage_percent',
    'Current CPU usage percentage'
)

database_connections = Gauge(
    'database_connections',
    'Number of active database connections'
)

# Cache Metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

# Business Metrics
insights_generated_total = Counter(
    'insights_generated_total',
    'Total number of insights generated',
    ['type']
)

user_productivity_score = Gauge(
    'user_productivity_score',
    'User productivity score',
    ['user_id']
)
