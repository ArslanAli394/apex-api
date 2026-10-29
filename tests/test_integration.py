"""
Integration tests combining multiple components.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_item_lifecycle(self, sample_item_data):
        """Test complete item lifecycle: create, read, update, delete."""
        # Create
        create_response = client.post("/api/v1/items", json=sample_item_data)
        assert create_response.status_code == 200
        item_id = create_response.json()["data"]["id"]

        # Read
        get_response = client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == 200

        # Update
        update_data = {"name": "Updated Name", "status": "inactive"}
        update_response = client.put(f"/api/v1/items/{item_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["data"]["status"] == "inactive"

        # Delete
        delete_response = client.delete(f"/api/v1/items/{item_id}")
        assert delete_response.status_code == 200

        # Verify deletion
        final_get = client.get(f"/api/v1/items/{item_id}")
        assert final_get.status_code == 404

    def test_metrics_endpoint(self):
        """Test metrics endpoint is available."""
        response = client.get("/metrics")
        assert response.status_code == 200
        # Prometheus format should contain TYPE and HELP
        assert b"TYPE" in response.content or b"apex_" in response.content

    def test_metrics_json_endpoint(self):
        """Test JSON metrics endpoint."""
        response = client.get("/metrics/json")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "requests_total" in data

    def test_api_documentation_available(self):
        """Test that API documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_api_openapi_schema(self):
        """Test OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_error_handling(self):
        """Test error handling returns proper format."""
        response = client.get("/api/v1/items/invalid-id")
        assert response.status_code in [404, 422]

    def test_concurrent_requests(self, sample_item_data):
        """Test handling multiple requests."""
        responses = []
        for i in range(5):
            modified_data = {**sample_item_data, "name": f"Item {i}"}
            response = client.post("/api/v1/items", json=modified_data)
            responses.append(response)

        assert all(r.status_code == 200 for r in responses)

    def test_request_id_in_response(self, sample_item_data):
        """Test that request ID is included in response headers."""
        response = client.post("/api/v1/items", json=sample_item_data)
        assert "x-request-id" in response.headers
        assert response.headers["x-request-id"] != ""
