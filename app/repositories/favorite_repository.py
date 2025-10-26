from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.favorite import Favorite
from app.models.product import Product


class FavoriteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_and_product(self, user_id: str, product_id: str) -> Optional[Favorite]:
        return self.db.query(Favorite).filter(
            and_(Favorite.user_id == user_id, Favorite.product_id == product_id)
        ).first()

    def get_user_favorites(self, user_id: str) -> List[Favorite]:
        return self.db.query(Favorite).filter(Favorite.user_id == user_id).all()

    def get_user_favorites_with_products(self, user_id: str) -> List[dict]:
        """Получает избранные товары с информацией о продуктах"""
        results = self.db.query(
            Favorite,
            Product
        ).join(
            Product, Favorite.product_id == Product.id
        ).filter(
            Favorite.user_id == user_id
        ).all()

        favorites_with_products = []
        for favorite, product in results:
            favorites_with_products.append({
                "id": favorite.id,
                "user_id": favorite.user_id,
                "product_id": favorite.product_id,
                "created_at": favorite.created_at,
                "product": {
                    "id": product.id,
                    "article": product.article,
                    "title": product.title,
                    "description": product.description,
                    "price": product.price,
                    "image_urls": product.image_urls or [],
                    "stock_quantity": product.stock_quantity
                }
            })

        return favorites_with_products

    def add_to_favorites(self, user_id: str, product_id: str) -> Favorite:
        favorite = Favorite(user_id=user_id, product_id=product_id)
        self.db.add(favorite)
        self.db.commit()
        self.db.refresh(favorite)
        return favorite

    def remove_from_favorites(self, user_id: str, product_id: str) -> bool:
        favorite = self.get_by_user_and_product(user_id, product_id)
        if favorite:
            self.db.delete(favorite)
            self.db.commit()
            return True
        return False

    def is_product_in_favorites(self, user_id: str, product_id: str) -> bool:
        favorite = self.get_by_user_and_product(user_id, product_id)
        return favorite is not None

    def get_favorite_count(self, user_id: str) -> int:
        return self.db.query(Favorite).filter(Favorite.user_id == user_id).count()