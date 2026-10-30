"""
Prometheus metrics endpoint and metrics collection.
"""

from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry
import logging

from app.config import settings
from app.schemas import MetricsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["Metrics"])

# Create custom registry
REGISTRY = CollectorRegistry()

# Define Prometheus metrics
request_count = Counter(
    "apex_requests_total",
    "Total number of requests",
    registry=REGISTRY,
)

request_errors = Counter(
    "apex_requests_errors_total",
    "Total number of failed requests",
    registry=REGISTRY,
)

request_duration = Histogram(
    "apex_request_duration_seconds",
    "Request duration in seconds",
    registry=REGISTRY,
)

db_connections_active = Gauge(
    "apex_db_connections_active",
    "Number of active database connections",
    registry=REGISTRY,
)

db_queries_total = Counter(
    "apex_db_queries_total",
    "Total number of database queries",
    registry=REGISTRY,
)


@router.get("/", response_class=PlainTextResponse)
async def prometheus_metrics() -> str:
    """
    Return Prometheus metrics in text format.
    Compatible with Prometheus scraping.
    """
    return generate_latest(REGISTRY).decode("utf-8")


@router.get("/json", response_model=MetricsResponse)
async def metrics_json() -> MetricsResponse:
    """
    Return metrics in JSON format.
    Easier for client-side parsing.
    """
    return MetricsResponse(
        timestamp=datetime.utcnow(),
        requests_total=int(request_count._value.get()),
        requests_success=int(request_count._value.get()) - int(request_errors._value.get()),
        requests_error=int(request_errors._value.get()),
        request_duration_avg=0.0,
        database_queries=int(db_queries_total._value.get()),
        db_connection_active=int(db_connections_active._value.get()),
    )


def increment_request_count():
    """Increment request counter."""
    request_count.inc()


def increment_error_count():
    """Increment error counter."""
    request_errors.inc()


def record_request_duration(duration: float):
    """Record request duration."""
    request_duration.observe(duration)


def set_active_connections(count: int):
    """Set number of active connections."""
    db_connections_active.set(count)


def increment_query_count():
    """Increment database query counter."""
    db_queries_total.inc()
