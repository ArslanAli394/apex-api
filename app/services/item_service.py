"""
Business logic for item operations.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
import logging

from app.models import Item
from app.schemas import ItemCreate, ItemUpdate

logger = logging.getLogger(__name__)


class ItemService:
    """Service for item-related business logic."""

    @staticmethod
    def create_item(db: Session, item: ItemCreate) -> Item:
        """Create a new item."""
        db_item = Item(**item.model_dump())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        logger.info(f"Item created: {db_item.id}")
        return db_item

    @staticmethod
    def get_item(db: Session, item_id: int) -> Optional[Item]:
        """Get item by ID."""
        return db.query(Item).filter(Item.id == item_id).first()

    @staticmethod
    def list_items(
        db: Session, skip: int = 0, limit: int = 20, category: Optional[str] = None
    ) -> tuple[List[Item], int]:
        """List items with pagination and optional filtering."""
        query = db.query(Item)

        if category:
            query = query.filter(Item.category == category)

        total = query.count()
        items = query.order_by(desc(Item.created_at)).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def search_items(db: Session, query_str: str, skip: int = 0, limit: int = 20) -> tuple[List[Item], int]:
        """Search items by name or description."""
        query = db.query(Item).filter(
            or_(
                Item.name.ilike(f"%{query_str}%"),
                Item.description.ilike(f"%{query_str}%"),
            )
        )
        total = query.count()
        items = query.order_by(desc(Item.created_at)).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def update_item(db: Session, item_id: int, item_update: ItemUpdate) -> Optional[Item]:
        """Update an item."""
        db_item = db.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            return None

        update_data = item_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_item, key, value)

        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        logger.info(f"Item updated: {db_item.id}")
        return db_item

    @staticmethod
    def delete_item(db: Session, item_id: int) -> bool:
        """Delete an item."""
        db_item = db.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            return False

        db.delete(db_item)
        db.commit()
        logger.info(f"Item deleted: {item_id}")
        return True

    @staticmethod
    def create_batch(db: Session, items: List[ItemCreate]) -> List[Item]:
        """Create multiple items in batch."""
        db_items = [Item(**item.model_dump()) for item in items]
        db.add_all(db_items)
        db.commit()
        for item in db_items:
            db.refresh(item)
        logger.info(f"Batch created: {len(db_items)} items")
        return db_items

    @staticmethod
    def get_stats(db: Session) -> dict:
        """Get item statistics."""
        total_items = db.query(Item).count()
        categories = db.query(Item.category, Item).filter().all()

        category_stats = {}
        for cat in db.query(Item.category).distinct().all():
            count = db.query(Item).filter(Item.category == cat[0]).count()
            category_stats[cat[0]] = count

        status_stats = {}
        for status in db.query(Item.status).distinct().all():
            count = db.query(Item).filter(Item.status == status[0]).count()
            status_stats[status[0]] = count

        return {
            "total_items": total_items,
            "categories": category_stats,
            "statuses": status_stats,
        }
