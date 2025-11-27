from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar('T')


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool = True


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int



