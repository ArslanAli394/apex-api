"""
Middleware for request/response logging and metrics collection.
"""

import time
import uuid
from typing import Callable, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Log request and response details."""
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Record request start time
        start_time = time.time()

        # Log request
        logger.info(
            f"Request received",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
                "client": request.client.host if request.client else "unknown",
            },
        )

        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"Request error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration,
                    "error": str(e),
                },
            )
            raise

        # Calculate request duration
        duration = (time.time() - start_time) * 1000

        # Log response
        logger.info(
            f"Response sent",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration,
            },
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting metrics."""

    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.error_count = 0
        self.total_duration = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Collect metrics for request/response."""
        start_time = time.time()
        self.request_count += 1

        try:
            response = await call_next(request)
            if response.status_code >= 400:
                self.error_count += 1
        except Exception:
            self.error_count += 1
            raise
        finally:
            duration = (time.time() - start_time) * 1000
            self.total_duration += duration

        return response

    def get_metrics(self) -> dict:
        """Get current metrics."""
        avg_duration = (
            self.total_duration / self.request_count if self.request_count > 0 else 0
        )
        return {
            "requests_total": self.request_count,
            "requests_error": self.error_count,
            "requests_success": self.request_count - self.error_count,
            "request_duration_avg": avg_duration,
        }
