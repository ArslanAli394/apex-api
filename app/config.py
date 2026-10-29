"""
Configuration management for the Apex API application.
Handles environment-based configuration with validation.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Apex Operations API"
    app_version: str = "1.0.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    workers: int = int(os.getenv("WORKERS", "4"))

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://apex_user:apex_password@localhost:5432/apex_db"
    )
    db_echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    db_pool_pre_ping: bool = True

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "json"  # json or standard

    # Monitoring
    metrics_enabled: bool = True
    health_check_timeout: int = 5

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # API
    api_prefix: str = "/api/v1"
    enable_docs: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing."""
        return self.environment.lower() == "testing"


# Singleton instance
settings = Settings()
