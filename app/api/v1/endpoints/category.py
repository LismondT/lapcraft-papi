from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database.database import get_db
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategoryTreeResponse
)

router = APIRouter()


@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
        include_children: bool = Query(False, description="Include children categories"),
        db: Session = Depends(get_db)
):
    repo = CategoryRepository(db)
    categories = repo.get_all_categories(include_children=include_children)
    return categories


@router.get("/tree", response_model=List[CategoryTreeResponse])
async def get_category_tree(db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    categories = repo.get_category_tree()
    return categories


@router.get("/root", response_model=List[CategoryResponse])
async def get_root_categories(db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    categories = repo.get_root_categories()
    return categories


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
        category_id: str,
        include_children: bool = Query(False, description="Include children categories"),
        db: Session = Depends(get_db)
):
    repo = CategoryRepository(db)
    if include_children:
        category = repo.get_category_with_children(category_id)
    else:
        category = repo.get_by_id(category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    return category


@router.get("/{category_id}/children", response_model=List[CategoryResponse])
async def get_category_children(
        category_id: str,
        db: Session = Depends(get_db)
):
    repo = CategoryRepository(db)
    children = repo.get_children(category_id)
    return children


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
        category_data: CategoryCreate,
        db: Session = Depends(get_db)
):
    repo = CategoryRepository(db)

    # Проверяем уникальность названия
    existing_category = repo.get_by_name(category_data.name)
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )

    # Проверяем существование родительской категории
    if category_data.parent_id:
        parent_category = repo.get_by_id(category_data.parent_id)
        if not parent_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category not found"
            )

    category = repo.create(category_data.dict())
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
        category_id: str,
        category_data: CategoryUpdate,
        db: Session = Depends(get_db)
):
    repo = CategoryRepository(db)

    existing_category = repo.get_by_id(category_id)
    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Проверяем уникальность названия
    if category_data.name and category_data.name != existing_category.name:
        category_with_name = repo.get_by_name(category_data.name)
        if category_with_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists"
            )

    # Проверяем существование родительской категории
    if category_data.parent_id and category_data.parent_id != existing_category.parent_id:
        if category_data.parent_id == category_id:  # Нельзя сделать категорию родителем самой себе
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be parent of itself"
            )

        parent_category = repo.get_by_id(category_data.parent_id)
        if not parent_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category not found"
            )

    updated_category = repo.update(category_id, category_data.dict(exclude_unset=True))
    return updated_category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
        category_id: str,
        db: Session = Depends(get_db)
):
    repo = CategoryRepository(db)

    try:
        success = repo.delete(category_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return None


@router.get("/search/{search_term}", response_model=List[CategoryResponse])
async def search_categories(
        search_term: str,
        db: Session = Depends(get_db)
):
    repo = CategoryRepository(db)
    categories = repo.search_categories(search_term)
    return categories
