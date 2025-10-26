from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID


class CartItemBase(BaseModel):
    product_id: str
    quantity: int


class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    product_id: str
    image_url: Optional[str] = None
    title: str
    description: str
    price: float
    count: int

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total: float
    items_count: int


class CartSummary(BaseModel):
    total_price: float
    items_count: int