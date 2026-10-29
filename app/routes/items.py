"""
CRUD API endpoints for items.
Main business logic routes.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.schemas import (
    Item,
    ItemCreate,
    ItemUpdate,
    ItemBatch,
    PaginatedResponse,
    ApiResponse,
)
from app.services.item_service import ItemService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/items", tags=["Items"])


@router.get("", response_model=PaginatedResponse)
async def list_items(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        20, ge=1, le=100, description="Items per page"
    ),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
) -> PaginatedResponse:
    """
    List all items with pagination.
    Supports optional category filtering.
    """
    skip = (page - 1) * page_size
    items, total = ItemService.list_items(
        db, skip=skip, limit=page_size, category=category
    )

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
        items=[Item.model_validate(item) for item in items],
    )


@router.post("", response_model=ApiResponse)
async def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
) -> ApiResponse:
    """
    Create a new item.
    Returns the created item with generated ID.
    """
    try:
        db_item = ItemService.create_item(db, item)
        return ApiResponse(
            status="success",
            data=Item.model_validate(db_item),
            timestamp=datetime.utcnow(),
            version=settings.app_version,
        )
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{item_id}", response_model=ApiResponse)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse:
    """
    Get a specific item by ID.
    """
    db_item = ItemService.get_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    return ApiResponse(
        status="success",
        data=Item.model_validate(db_item),
        timestamp=datetime.utcnow(),
        version=settings.app_version,
    )


@router.put("/{item_id}", response_model=ApiResponse)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse:
    """
    Update an existing item.
    Only provided fields are updated.
    """
    db_item = ItemService.update_item(db, item_id, item_update)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    return ApiResponse(
        status="success",
        data=Item.model_validate(db_item),
        timestamp=datetime.utcnow(),
        version=settings.app_version,
    )


@router.delete("/{item_id}", response_model=ApiResponse)
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse:
    """
    Delete an item.
    """
    success = ItemService.delete_item(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")

    return ApiResponse(
        status="success",
        data={"id": item_id, "deleted": True},
        timestamp=datetime.utcnow(),
        version=settings.app_version,
    )


@router.get("/search/query", response_model=PaginatedResponse)
async def search_items(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse:
    """
    Search items by name or description.
    """
    skip = (page - 1) * page_size
    items, total = ItemService.search_items(
        db, query_str=q, skip=skip, limit=page_size
    )

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
        items=[Item.model_validate(item) for item in items],
    )


@router.post("/batch", response_model=ApiResponse)
async def batch_create_items(
    batch: ItemBatch,
    db: Session = Depends(get_db),
) -> ApiResponse:
    """
    Create multiple items in a single request.
    Useful for bulk operations.
    """
    try:
        db_items = ItemService.create_batch(db, batch.items)
        return ApiResponse(
            status="success",
            data={
                "created": len(db_items),
                "items": [Item.model_validate(item) for item in db_items],
            },
            timestamp=datetime.utcnow(),
            version=settings.app_version,
        )
    except Exception as e:
        logger.error(f"Error in batch creation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats/overview", response_model=ApiResponse)
async def get_stats(
    db: Session = Depends(get_db),
) -> ApiResponse:
    """
    Get statistics about items in the database.
    """
    stats = ItemService.get_stats(db)
    return ApiResponse(
        status="success",
        data=stats,
        timestamp=datetime.utcnow(),
        version=settings.app_version,
    )
