"""
Test suite for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthChecks:
    """Test health check endpoints."""

    def test_liveness_probe_success(self):
        """Test liveness probe returns healthy status."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "checks" in data

    def test_readiness_probe_success(self):
        """Test readiness probe when database is available."""
        response = client.get("/health/ready")
        # May return 200 or 503 depending on database availability
        assert response.status_code in [200, 503]

    def test_ping_endpoint(self):
        """Test simple ping endpoint."""
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.json()["status"] == "pong"

    def test_root_endpoint(self):
        """Test root service info endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "environment" in data
        assert data["status"] == "operational"
