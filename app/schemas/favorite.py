from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.schemas.product import ProductResponse


class FavoriteBase(BaseModel):
    user_id: str
    product_id: str


class FavoriteCreate(BaseModel):
    product_id: str


class FavoriteResponse(FavoriteBase):
    id: UUID
    # created_at: str

    class Config:
        from_attributes = True


class FavoriteWithProductResponse(BaseModel):
    id: UUID
    user_id: str
    product_id: str
    # created_at: str
    product: ProductResponse

    class Config:
        from_attributes = True


class FavoriteListResponse(BaseModel):
    favorites: List[FavoriteWithProductResponse]
    total: int