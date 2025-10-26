from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database.database import get_db
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
    CartSummary
)

router = APIRouter()


@router.get("/", response_model=CartResponse)
async def get_cart(
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    cart_repo = CartRepository(db)

    cart_items = cart_repo.get_user_cart_with_products(current_user["id"])
    total = cart_repo.get_cart_total(current_user["id"])
    items_count = cart_repo.get_cart_items_count(current_user["id"])

    return CartResponse(
        items=cart_items,
        total=total,
        items_count=items_count
    )


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_to_cart(
        cart_item: CartItemCreate,
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    cart_repo = CartRepository(db)
    product_repo = ProductRepository(db)

    # Проверяем существование продукта
    product = product_repo.get_by_id(cart_item.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Проверяем доступное количество
    if product.stock_quantity < cart_item.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough stock available"
        )

    cart_item_obj = cart_repo.add_to_cart(
        current_user["id"],
        cart_item.product_id,
        cart_item.quantity
    )

    return {
        "message": "Product added to cart",
        "cart_item_id": cart_item_obj.id
    }


@router.put("/items/{product_id}")
async def update_cart_item(
        product_id: str,
        cart_update: CartItemUpdate,
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    cart_repo = CartRepository(db)
    product_repo = ProductRepository(db)

    # Проверяем существование продукта
    product = product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Проверяем доступное количество
    if product.stock_quantity < cart_update.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough stock available"
        )

    cart_item = cart_repo.update_cart_item_quantity(
        current_user["id"],
        product_id,
        cart_update.quantity
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in cart"
        )

    return {"message": "Cart item updated"}


@router.delete("/items/{product_id}")
async def remove_from_cart(
        product_id: str,
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    cart_repo = CartRepository(db)

    success = cart_repo.remove_from_cart(current_user["id"], product_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in cart"
        )

    return {"message": "Product removed from cart"}


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    cart_repo = CartRepository(db)
    cart_repo.clear_cart(current_user["id"])

    return None


@router.get("/summary", response_model=CartSummary)
async def get_cart_summary(
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    cart_repo = CartRepository(db)

    total = cart_repo.get_cart_total(current_user["id"])
    items_count = cart_repo.get_cart_items_count(current_user["id"])

    return CartSummary(
        total_price=total,
        items_count=items_count
    )
