from typing import Optional, List
from pydantic import BaseModel, validator
from uuid import UUID


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    product_count: int = 0
    children_count: int = 0  # Добавляем в схему


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: UUID

    class Config:
        from_attributes = True


# Для рекурсивной структуры дерева категорий
class CategoryTreeResponse(CategoryResponse):
    children: List['CategoryTreeResponse'] = []


# Обновляем forward references после определения класса
CategoryTreeResponse.update_forward_refs()