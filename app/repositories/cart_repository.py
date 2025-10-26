from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.cart import CartItem
from app.models.product import Product


class CartRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_and_product(self, user_id: str, product_id: str) -> Optional[CartItem]:
        return self.db.query(CartItem).filter(
            and_(CartItem.user_id == user_id, CartItem.product_id == product_id)
        ).first()

    def get_user_cart_items(self, user_id: str) -> List[CartItem]:
        return self.db.query(CartItem).filter(CartItem.user_id == user_id).all()

    def get_user_cart_with_products(self, user_id: str) -> List[Dict[str, Any]]:
        """Получает корзину с информацией о продуктах"""
        results = self.db.query(
            CartItem,
            Product
        ).join(
            Product, CartItem.product_id == Product.id
        ).filter(
            CartItem.user_id == user_id
        ).all()

        cart_items = []
        for cart_item, product in results:
            cart_items.append({
                "product_id": product.id,
                "image_url": product.image_urls[0] if product.image_urls else None,
                "title": product.title,
                "description": product.description,
                "price": product.price,
                "count": cart_item.quantity
            })

        return cart_items

    def add_to_cart(self, user_id: str, product_id: str, quantity: int = 1) -> CartItem:
        cart_item = self.get_by_user_and_product(user_id, product_id)

        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
            self.db.add(cart_item)

        self.db.commit()
        self.db.refresh(cart_item)
        return cart_item

    def update_cart_item_quantity(self, user_id: str, product_id: str, quantity: int) -> Optional[CartItem]:
        cart_item = self.get_by_user_and_product(user_id, product_id)
        if cart_item:
            cart_item.quantity = quantity
            self.db.commit()
            self.db.refresh(cart_item)
        return cart_item

    def remove_from_cart(self, user_id: str, product_id: str) -> bool:
        cart_item = self.get_by_user_and_product(user_id, product_id)
        if cart_item:
            self.db.delete(cart_item)
            self.db.commit()
            return True
        return False

    def clear_cart(self, user_id: str) -> bool:
        cart_items = self.get_user_cart_items(user_id)
        for item in cart_items:
            self.db.delete(item)
        self.db.commit()
        return True

    def get_cart_total(self, user_id: str) -> float:
        """Получает общую стоимость корзины"""
        results = self.db.query(
            CartItem.quantity,
            Product.price
        ).join(
            Product, CartItem.product_id == Product.id
        ).filter(
            CartItem.user_id == user_id
        ).all()

        total = 0.0
        for quantity, price in results:
            total += quantity * price

        return total

    def get_cart_items_count(self, user_id: str) -> int:
        """Получает общее количество товаров в корзине"""
        return self.db.query(CartItem).filter(CartItem.user_id == user_id).count()