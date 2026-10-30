"""
Pydantic schemas for API request/response validation.
Defines data contracts for all API endpoints.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Base schemas
class ItemBase(BaseModel):
    """Base schema for item data."""

    name: str = Field(..., min_length=1, max_length=255, description="Item name")
    description: Optional[str] = Field(
        None, max_length=2000, description="Item description"
    )
    category: str = Field(..., min_length=1, max_length=50, description="Item category")
    status: str = Field(
        default="active",
        pattern="^(active|inactive|archived)$",
        description="Item status",
    )
    created_by: Optional[str] = Field(None, max_length=100, description="Creator name")
    attributes: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional attributes"
    )


class ItemCreate(ItemBase):
    """Schema for creating a new item."""

    pass


class ItemUpdate(BaseModel):
    """Schema for updating an item."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = Field(None, pattern="^(active|inactive|archived)$")
    created_by: Optional[str] = Field(None, max_length=100)
    attributes: Optional[Dict[str, Any]] = Field(None)


class Item(ItemBase):
    """Full item schema including database fields."""

    id: int = Field(..., description="Item ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ItemBatch(BaseModel):
    """Schema for batch creating items."""

    items: List[ItemCreate] = Field(..., min_items=1, max_items=100)


class PaginationParams(BaseModel):
    """Schema for pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Items per page"
    )

    @property
    def skip(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Return limit for database query."""
        return self.page_size


class PaginatedResponse(BaseModel):
    """Generic paginated response schema."""

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether next page exists")
    has_prev: bool = Field(..., description="Whether previous page exists")
    items: List[Item] = Field(..., description="Items in current page")


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str = Field(..., description="Health status (healthy/degraded/unhealthy)")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="API version")
    checks: Dict[str, str] = Field(..., description="Individual component checks")


class MetricsResponse(BaseModel):
    """Schema for metrics response."""

    timestamp: datetime = Field(..., description="Metrics timestamp")
    requests_total: int = Field(..., description="Total requests")
    requests_success: int = Field(..., description="Successful requests")
    requests_error: int = Field(..., description="Failed requests")
    request_duration_avg: float = Field(..., description="Average request duration (ms)")
    database_queries: int = Field(..., description="Total database queries")
    db_connection_active: int = Field(..., description="Active DB connections")


class ApiResponse(BaseModel):
    """Generic API response wrapper."""

    status: str = Field(..., description="Response status (success/error)")
    data: Any = Field(..., description="Response data")
    timestamp: datetime = Field(..., description="Response timestamp")
    version: str = Field(..., description="API version")
    error: Optional[str] = Field(None, description="Error message if status is error")


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    status: str = Field(default="error", description="Error status")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
