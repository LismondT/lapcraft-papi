from typing import Optional
from uuid import UUID

from fastapi import Query, Depends, APIRouter, HTTPException, status
from sqlmodel import Session

from app.database.database import get_db
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductResponse, ProductCreate, ProductUpdate

router = APIRouter()


@router.get("/", response_model=dict)
async def get_products(
        page: int = Query(1, ge=1),
        count: int = Query(10, ge=1, le=100),
        category: Optional[str] = Query(None),
        name: Optional[str] = Query(None),
        min_price: Optional[float] = Query(None),
        max_price: Optional[float] = Query(None),
        sort: str = Query("id"),
        order: str = Query("asc", regex="^(asc|desc)$"),
        db: Session = Depends(get_db)
):
    # Формируем все фильтры
    filters = {}
    if category:
        category_repo = CategoryRepository(db)
        category_exists = category_repo.get_by_id(category)
        if not category_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found"
            )
        filters["category_id"] = category
    if name:
        filters["title"] = name
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price

    repo = ProductRepository(db)
    products = repo.get_paginated(page, count, filters, sort, order)
    total = repo.get_total_count(filters)

    return {
        "products": products,
        "page": page,
        "count": count,
        "total": total
    }


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
        product_id: UUID,
        db: Session = Depends(get_db)
):
    repo = ProductRepository(db)
    product = repo.get_by_id_with_category_name(str(product_id))

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Продукт не найден"
        )

    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
        product_data: ProductCreate,
        db: Session = Depends(get_db)
):
    repo = ProductRepository(db)

    # Если артикул указан вручную, проверяем его уникальность
    if product_data.article is not None:
        existing_product = repo.get_by_article(product_data.article)
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product with this article already exists"
            )

    product = repo.create(product_data.model_dump())
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
        product_id: UUID,
        product_data: ProductUpdate,
        db: Session = Depends(get_db)
):
    repo = ProductRepository(db)

    # Проверяем существование продукта
    existing_product = repo.get_by_id(str(product_id))
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Проверяем уникальность артикула, если он изменяется
    if product_data.article is not None and product_data.article != existing_product.article:
        product_with_article = repo.get_by_article(product_data.article)
        if product_with_article:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product with this article already exists"
            )

    updated_product = repo.update(str(product_id), product_data.model_dump(exclude_unset=True))
    return updated_product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
        product_id: UUID,
        db: Session = Depends(get_db)
):
    repo = ProductRepository(db)

    success = repo.delete(str(product_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return None
