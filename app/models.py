"""
SQLAlchemy ORM models for the Apex API.
Defines the database schema.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class Item(Base):
    """
    Item model representing a data entity.
    Generic item with random attributes for assessment purposes.
    """

    __tablename__ = "items"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Core fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    status = Column(String(20), default="active", index=True, nullable=False)

    # Metadata fields
    created_by = Column(String(100), nullable=True)
    attributes = Column(JSONB, default={}, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime,
        server_default=func.now(),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, name={self.name}, category={self.category})>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "status": self.status,
            "created_by": self.created_by,
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Create indexes for better query performance
Index("idx_items_category_status", Item.category, Item.status)
Index("idx_items_created_at_desc", Item.created_at.desc())
