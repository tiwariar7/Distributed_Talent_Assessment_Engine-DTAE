"""
Prometheus metrics collection and monitoring middleware.
"""

import time
from django.http import HttpResponse
from django.urls import resolve
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

# 1. HTTP Metrics
HTTP_REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP Request Latency in seconds",
    ["method", "endpoint"],
)
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP Requests",
    ["method", "endpoint", "status"],
)

# 2. Celery queue depth
CELERY_QUEUE_DEPTH = Gauge(
    "celery_queue_depth",
    "Celery task queue depths",
    ["queue"],
)

# 3. Sandbox Metrics
SANDBOX_EXECUTION_DURATION = Histogram(
    "sandbox_execution_duration_seconds",
    "Sandbox execution duration",
    ["language"],
)
SANDBOX_STARTUP_TIME = Histogram(
    "sandbox_startup_seconds",
    "Sandbox docker startup time",
    ["language"],
)
CONTAINER_FAILURES = Counter(
    "sandbox_container_failures_total",
    "Total sandbox container execution failures",
    ["language", "reason"],
)
EXECUTION_STATUS_TOTAL = Counter(
    "execution_status_total",
    "Total sandbox executions by language and exit status",
    ["language", "status"],
)

# 4. WebSocket Metrics
WEBSOCKET_CONNECTIONS = Gauge(
    "websocket_connections_active",
    "Active WebSocket connections",
)

# 5. CouchDB MVCC metrics
COUCHDB_CONFLICT_RETRIES = Counter(
    "couchdb_conflict_retries_total",
    "Total CouchDB MVCC conflict retries",
)

# 6. Leaderboard Metrics
LEADERBOARD_UPDATE_LATENCY = Histogram(
    "leaderboard_update_latency_seconds",
    "Leaderboard update latency in seconds",
)
LEADERBOARD_FAILED_EVENTS = Counter(
    "leaderboard_failed_events_total",
    "Total failed leaderboard update events",
)
LEADERBOARD_CACHE_HITS = Counter(
    "leaderboard_cache_hits_total",
    "Total leaderboard cache hits",
)
LEADERBOARD_CACHE_MISSES = Counter(
    "leaderboard_cache_misses_total",
    "Total leaderboard cache misses",
)


class PrometheusMiddleware:
    """Middleware for tracking HTTP request telemetry and exposing metrics."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/metrics" or request.path == "/metrics/":
            return self.metrics_view(request)

        start_time = time.perf_counter()
        response = self.get_response(request)
        duration = time.perf_counter() - start_time

        try:
            match = resolve(request.path)
            endpoint = match.url_name or request.path
        except Exception:
            endpoint = request.path

        method = request.method
        status = str(response.status_code)

        HTTP_REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
        HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status).inc()

        return response

    def metrics_view(self, request) -> HttpResponse:
        """Endpoint view serving standard prometheus text metrics."""
        self._update_queue_depths()
        data = generate_latest()
        return HttpResponse(data, content_type=CONTENT_TYPE_LATEST)

    def _update_queue_depths(self) -> None:
        """Poll the Celery/RabbitMQ broker to dynamically gauge current queue depths."""
        try:
            from config.celery import app
            with app.connection_or_acquire() as conn:
                for queue in ["high_priority", "medium_priority", "low_priority", "maintenance"]:
                    try:
                        _, message_count, _ = conn.default_channel.queue_declare(
                            queue=queue, passive=True
                        )
                        CELERY_QUEUE_DEPTH.labels(queue=queue).set(message_count)
                    except Exception:
                        pass
        except Exception:
            pass

# Refactor: Enhance component rendering performance.

# Refactor: Refactor variable names for better readability.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Enhance component rendering performance.
