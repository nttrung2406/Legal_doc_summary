from prometheus_client import Counter, Histogram, Gauge
import psutil
import time
from typing import Callable
from fastapi import Request, Response
import logging

logger = logging.getLogger(__name__)

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# System metrics
CPU_USAGE = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

MEMORY_USAGE = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes'
)

DISK_USAGE = Gauge(
    'system_disk_usage_bytes',
    'System disk usage in bytes'
)

# API specific metrics
UPLOAD_COUNT = Counter(
    'document_uploads_total',
    'Total document uploads',
    ['status']
)

CHAT_REQUESTS = Counter(
    'chat_requests_total',
    'Total chat requests',
    ['status']
)

SUMMARY_REQUESTS = Counter(
    'summary_requests_total',
    'Total summary generation requests',
    ['status']
)

def update_system_metrics():
    """Update system metrics periodically"""
    while True:
        try:
            # CPU usage
            CPU_USAGE.set(psutil.cpu_percent())
            
            # Memory usage
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.used)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            DISK_USAGE.set(disk.used)
            
            time.sleep(5)  # Update every 5 seconds
        except Exception as e:
            logger.error(f"Error updating system metrics: {str(e)}")
            time.sleep(5)

async def monitor_request(request: Request, call_next: Callable) -> Response:
    """Middleware to monitor requests"""
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    
    try:
        response = await call_next(request)
        status = response.status_code
        
        # Record request metrics
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        
        return response
    except Exception as e:
        logger.error(f"Error in request monitoring: {str(e)}")
        raise 