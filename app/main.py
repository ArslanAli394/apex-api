"""
FastAPI main application.
Entry point for the Apex Operations API.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import init_db
from app.utils.logger import setup_logging, get_logger
from app.middleware.logging import RequestLoggingMiddleware, MetricsMiddleware
from app.routes import health, metrics, items

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    init_db()
    logger.info("Application startup complete")
    yield
    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Generic Apex Operations API for DevOps Assessment",
    version=settings.app_version,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MetricsMiddleware)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred",
        },
    )


# Root endpoint
@app.get("/", tags=["Info"])
async def root():
    """Service information endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "operational",
        "docs": "/docs",
        "health": "/health/live",
        "ready": "/health/ready",
    }


# Include routers
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(items.router, prefix=settings.api_prefix)


# Health check on root
@app.get("/ping", tags=["Health Checks"])
async def ping():
    """Simple ping endpoint for liveness."""
    return {"status": "pong"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers if settings.is_production else 1,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
