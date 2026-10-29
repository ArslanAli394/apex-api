"""
Test suite for item API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestItemEndpoints:
    """Test CRUD endpoints for items."""

    def test_create_item(self, sample_item_data):
        """Test creating a new item."""
        response = client.post("/api/v1/items", json=sample_item_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["data"]["name"] == sample_item_data["name"]

    def test_create_item_missing_required_field(self):
        """Test creating item without required field fails."""
        invalid_data = {
            "description": "Missing name field",
            "category": "test",
        }
        response = client.post("/api/v1/items", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_list_items(self, sample_item_data):
        """Test listing items with pagination."""
        # Create an item first
        client.post("/api/v1/items", json=sample_item_data)

        # List items
        response = client.get("/api/v1/items")
        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        assert "page_size" in data
        assert "total_items" in data
        assert "items" in data

    def test_list_items_with_pagination(self, sample_item_data):
        """Test pagination parameters."""
        response = client.get("/api/v1/items?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_get_item(self, sample_item_data):
        """Test retrieving a specific item."""
        # Create item
        create_response = client.post("/api/v1/items", json=sample_item_data)
        item_id = create_response.json()["data"]["id"]

        # Get item
        response = client.get(f"/api/v1/items/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == item_id

    def test_get_nonexistent_item(self):
        """Test retrieving non-existent item returns 404."""
        response = client.get("/api/v1/items/99999")
        assert response.status_code == 404

    def test_update_item(self, sample_item_data):
        """Test updating an item."""
        # Create item
        create_response = client.post("/api/v1/items", json=sample_item_data)
        item_id = create_response.json()["data"]["id"]

        # Update item
        update_data = {"name": "Updated Name"}
        response = client.put(f"/api/v1/items/{item_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Updated Name"

    def test_delete_item(self, sample_item_data):
        """Test deleting an item."""
        # Create item
        create_response = client.post("/api/v1/items", json=sample_item_data)
        item_id = create_response.json()["data"]["id"]

        # Delete item
        response = client.delete(f"/api/v1/items/{item_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Verify deletion
        get_response = client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == 404

    def test_search_items(self, sample_item_data):
        """Test searching items."""
        # Create items with specific names
        client.post("/api/v1/items", json=sample_item_data)

        response = client.get("/api/v1/items/search/query?q=Test")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total_items"] >= 0

    def test_search_empty_query(self):
        """Test search with empty query fails."""
        response = client.get("/api/v1/items/search/query?q=")
        assert response.status_code == 422  # Validation error

    def test_batch_create_items(self, multiple_items_data):
        """Test batch creating items."""
        batch_data = {"items": multiple_items_data}
        response = client.post("/api/v1/items/batch", json=batch_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["created"] == len(multiple_items_data)

    def test_batch_create_empty(self):
        """Test batch create with empty list fails."""
        batch_data = {"items": []}
        response = client.post("/api/v1/items/batch", json=batch_data)
        assert response.status_code == 422

    def test_get_stats(self, sample_item_data):
        """Test getting statistics."""
        # Create some items
        client.post("/api/v1/items", json=sample_item_data)

        response = client.get("/api/v1/items/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "total_items" in data["data"]
        assert "categories" in data["data"]
        assert "statuses" in data["data"]

    def test_list_items_filter_by_category(self, sample_item_data):
        """Test filtering items by category."""
        client.post("/api/v1/items", json=sample_item_data)

        response = client.get("/api/v1/items?category=test")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["category"] == "test"

    def test_response_includes_version(self, sample_item_data):
        """Test that responses include API version."""
        response = client.post("/api/v1/items", json=sample_item_data)
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"] is not None

    def test_response_includes_timestamp(self, sample_item_data):
        """Test that responses include timestamp."""
        response = client.post("/api/v1/items", json=sample_item_data)
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
