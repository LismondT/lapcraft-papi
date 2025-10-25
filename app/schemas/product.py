from typing import Optional, List
from pydantic import BaseModel, validator, Field
from uuid import UUID

from app.schemas.category import CategoryResponse


class ProductBase(BaseModel):
    article: Optional[int] = Field(None, description="Auto-generated article number")
    title: str
    description: Optional[str] = None
    price: float
    category_id: Optional[str] = None
    image_urls: List[str] = []
    stock_quantity: int = 0

    @validator('price')
    def price_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Price must be positive')
        return v

    @validator('stock_quantity')
    def stock_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Stock quantity must be non-negative')
        return v


class ProductCreate(ProductBase):
    article: Optional[int] = Field(None, description="Leave empty for auto-generation")


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[str] = None
    image_urls: Optional[List[str]] = None
    stock_quantity: Optional[int] = None

    @validator('price')
    def price_must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price must be positive')
        return v

    @validator('stock_quantity')
    def stock_must_be_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('Stock quantity must be non-negative')
        return v


class ProductResponse(ProductBase):
    id: UUID
    article: int
    category_name: Optional[str] = None

    class Config:
        from_attributes = True