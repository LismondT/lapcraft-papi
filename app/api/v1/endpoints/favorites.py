from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database.database import get_db
from app.repositories.favorite_repository import FavoriteRepository
from app.schemas.favorite import (
    FavoriteCreate,
    FavoriteWithProductResponse,
    FavoriteListResponse
)

router = APIRouter()


@router.get("/", response_model=FavoriteListResponse)
async def get_user_favorites(
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    favorite_repo = FavoriteRepository(db)

    favorites_with_products = favorite_repo.get_user_favorites_with_products(current_user["id"])
    total = favorite_repo.get_favorite_count(current_user["id"])

    return FavoriteListResponse(
        favorites=favorites_with_products,
        total=total
    )


@router.post("/{product_id}", status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
        product_id: str,
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    favorite_repo = FavoriteRepository(db)

    # Проверяем, не добавлен ли уже товар в избранное
    if favorite_repo.is_product_in_favorites(current_user["id"], product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already in favorites"
        )

    favorite = favorite_repo.add_to_favorites(current_user["id"], product_id)

    return {
        "message": "Product added to favorites",
        "favorite_id": favorite.id
    }


@router.delete("/{product_id}")
async def remove_from_favorites(
        product_id: str,
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    favorite_repo = FavoriteRepository(db)

    success = favorite_repo.remove_from_favorites(current_user["id"], product_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in favorites"
        )

    return {"message": "Product removed from favorites"}


@router.get("/check/{product_id}")
async def check_product_in_favorites(
        product_id: str,
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    favorite_repo = FavoriteRepository(db)

    is_favorite = favorite_repo.is_product_in_favorites(current_user["id"], product_id)

    return {"is_favorite": is_favorite}


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_favorites(
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    favorite_repo = FavoriteRepository(db)
    favorites = favorite_repo.get_user_favorites(current_user["id"])

    for favorite in favorites:
        db.delete(favorite)

    db.commit()

    return None