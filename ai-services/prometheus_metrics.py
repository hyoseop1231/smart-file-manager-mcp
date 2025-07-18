"""
Prometheus metrics for Smart File Manager
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
import psutil

# Request metrics
REQUEST_COUNT = Counter(
    'smart_file_manager_requests_total',
    'Total request count',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'smart_file_manager_request_duration_seconds',
    'Request latency',
    ['method', 'endpoint']
)

# File processing metrics
FILES_PROCESSED = Counter(
    'smart_file_manager_files_processed_total',
    'Total files processed',
    ['file_type', 'operation']
)

PROCESSING_ERRORS = Counter(
    'smart_file_manager_processing_errors_total',
    'Total processing errors',
    ['error_type']
)

# System metrics
INDEXED_FILES = Gauge(
    'smart_file_manager_indexed_files',
    'Number of indexed files',
    ['category']
)

QUEUE_SIZE = Gauge(
    'smart_file_manager_queue_size',
    'Processing queue size'
)

# Resource metrics
CPU_USAGE = Gauge('smart_file_manager_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('smart_file_manager_memory_usage_percent', 'Memory usage percentage')
DISK_USAGE = Gauge('smart_file_manager_disk_usage_percent', 'Disk usage percentage')

def update_system_metrics():
    """Update system resource metrics"""
    try:
        CPU_USAGE.set(psutil.cpu_percent(interval=0.1))
        MEMORY_USAGE.set(psutil.virtual_memory().percent)
        DISK_USAGE.set(psutil.disk_usage('/').percent)
    except Exception:
        pass

def track_request(method: str, endpoint: str, status: int, duration: float):
    """Track HTTP request metrics"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

def track_file_processing(file_type: str, operation: str):
    """Track file processing metrics"""
    FILES_PROCESSED.labels(file_type=file_type, operation=operation).inc()

def track_error(error_type: str):
    """Track processing errors"""
    PROCESSING_ERRORS.labels(error_type=error_type).inc()

def update_indexed_files(stats: dict):
    """Update indexed files gauge"""
    for category, count in stats.items():
        INDEXED_FILES.labels(category=category).set(count)

def get_metrics():
    """Generate Prometheus metrics"""
    update_system_metrics()
    return generate_latest()