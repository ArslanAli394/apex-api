"""
Integration tests for database operations.
"""

import pytest
from sqlalchemy.orm import Session
from app.models import Item
from app.database import Base, engine


class TestDatabaseIntegration:
    """Test database connectivity and operations."""

    def test_database_connection(self, test_db: Session):
        """Test that database connection works."""
        result = test_db.execute("SELECT 1")
        assert result is not None

    def test_item_creation(self, test_db: Session):
        """Test creating item in database."""
        item = Item(
            name="Test Item",
            description="Test Description",
            category="test",
            status="active",
        )
        test_db.add(item)
        test_db.commit()
        test_db.refresh(item)

        assert item.id is not None
        assert item.name == "Test Item"

    def test_item_retrieval(self, test_db: Session):
        """Test retrieving item from database."""
        item = Item(
            name="Retrieve Test",
            description="Test",
            category="test",
            status="active",
        )
        test_db.add(item)
        test_db.commit()

        retrieved = test_db.query(Item).filter(Item.id == item.id).first()
        assert retrieved is not None
        assert retrieved.name == "Retrieve Test"

    def test_item_update(self, test_db: Session):
        """Test updating item in database."""
        item = Item(
            name="Original",
            description="Test",
            category="test",
            status="active",
        )
        test_db.add(item)
        test_db.commit()

        item.name = "Updated"
        test_db.add(item)
        test_db.commit()
        test_db.refresh(item)

        assert item.name == "Updated"

    def test_item_deletion(self, test_db: Session):
        """Test deleting item from database."""
        item = Item(
            name="Delete Test",
            description="Test",
            category="test",
            status="active",
        )
        test_db.add(item)
        test_db.commit()
        item_id = item.id

        test_db.delete(item)
        test_db.commit()

        deleted = test_db.query(Item).filter(Item.id == item_id).first()
        assert deleted is None

    def test_model_to_dict(self, test_db: Session):
        """Test model to_dict conversion."""
        item = Item(
            name="Dict Test",
            description="Test",
            category="test",
            status="active",
        )
        test_db.add(item)
        test_db.commit()

        item_dict = item.to_dict()
        assert item_dict["name"] == "Dict Test"
        assert "created_at" in item_dict
        assert "updated_at" in item_dict

    def test_item_timestamps(self, test_db: Session):
        """Test that timestamps are set correctly."""
        item = Item(
            name="Timestamp Test",
            description="Test",
            category="test",
            status="active",
        )
        test_db.add(item)
        test_db.commit()
        test_db.refresh(item)

        assert item.created_at is not None
        assert item.updated_at is not None
        assert item.created_at == item.updated_at
