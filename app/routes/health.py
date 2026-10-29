"""
Health check endpoints for liveness and readiness probes.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
import logging

from app.config import settings
from app.database import check_db_connection
from app.schemas import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health Checks"])


@router.get("/live", response_model=HealthResponse)
async def liveness_probe() -> HealthResponse:
    """
    Liveness probe - indicates if service is running.
    Used by orchestrators to restart dead services.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        checks={"service": "running"},
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_probe() -> HealthResponse:
    """
    Readiness probe - indicates if service is ready to handle traffic.
    Includes database connectivity check.
    """
    checks = {}
    status = "healthy"

    # Check database connectivity
    db_ready = await check_db_connection()
    checks["database"] = "connected" if db_ready else "disconnected"

    if not db_ready:
        status = "degraded"
        logger.warning("Database not ready")

    if status == "degraded":
        raise HTTPException(
            status_code=503,
            detail=HealthResponse(
                status=status,
                timestamp=datetime.utcnow(),
                version=settings.app_version,
                checks=checks,
            ).model_dump(),
        )

    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        checks={**checks, "service": "ready"},
    )
