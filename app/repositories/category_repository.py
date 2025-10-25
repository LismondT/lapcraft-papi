from typing import Optional, Dict, Any, List, Set
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, desc, func

from app.models.category import Category
from app.models.product import Product


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, category_id: str, include_children: bool = False) -> Optional[Category]:
        query = self.db.query(Category)
        if include_children:
            query = query.options(joinedload(Category.children))
        return query.filter(Category.id == category_id).first()

    def get_by_name(self, name: str) -> Optional[Category]:
        return self.db.query(Category).filter(Category.name == name).first()

    def create(self, category_data: Dict[str, Any]) -> Category:
        category = Category(**category_data)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category_id: str, update_data: Dict[str, Any]) -> Optional[Category]:
        category = self.get_by_id(category_id)
        if category:
            for field, value in update_data.items():
                if hasattr(category, field):
                    setattr(category, field, value)
            self.db.commit()
            self.db.refresh(category)
        return category

    def delete(self, category_id: str) -> bool:
        category = self.get_by_id(category_id)
        if category:
            # Проверяем, есть ли продукты в этой категории
            product_count = self.db.query(Product).filter(Product.category_id == category_id).count()
            if product_count > 0:
                raise ValueError(f"Cannot delete category with {product_count} products")

            # Проверяем, есть ли дочерние категории
            children_count = self.db.query(Category).filter(Category.parent_id == category_id).count()
            if children_count > 0:
                raise ValueError(f"Cannot delete category with {children_count} subcategories")

            self.db.delete(category)
            self.db.commit()
            return True
        return False

    def get_all_categories(self, include_children: bool = False) -> List[Category]:
        query = self.db.query(Category)
        if include_children:
            query = query.options(joinedload(Category.children))
        return query.all()

    def get_all_subcategory_ids(self, category_id: str) -> Set[str]:
        """
        Рекурсивно получает все ID подкатегорий для заданной категории
        """

        def get_children_ids(parent_id: str) -> Set[str]:
            children = self.db.query(Category).filter(Category.parent_id == parent_id).all()
            children_ids = {child.id for child in children}

            # Рекурсивно получаем ID детей детей
            for child in children:
                children_ids.update(get_children_ids(child.id))

            return children_ids

        # Начинаем с основной категории и получаем все дочерние
        all_ids = {category_id}
        all_ids.update(get_children_ids(category_id))
        return all_ids

    def get_category_with_all_children(self, category_id: str) -> List[str]:
        """
        Получает список всех ID категорий (включая переданную и все её подкатегории)
        """
        return list(self.get_all_subcategory_ids(category_id))

    def get_root_categories(self) -> List[Category]:
        """Получение корневых категорий (без родителя)"""
        return self.db.query(Category).filter(Category.parent_id.is_(None)).all()

    def get_children(self, category_id: str) -> List[Category]:
        """Получение дочерних категорий"""
        return self.db.query(Category).filter(Category.parent_id == category_id).all()

    def get_category_tree(self) -> List[Category]:
        """Получение дерева категорий (рекурсивно)"""

        def build_tree(parent_id: Optional[str] = None) -> List[Category]:
            categories = self.db.query(Category).filter(Category.parent_id == parent_id).all()
            for category in categories:
                category.children = build_tree(category.id)
            return categories

        return build_tree()

    def get_category_with_children(self, category_id: str) -> Optional[Category]:
        """Получение категории с дочерними элементами"""
        category = self.get_by_id(category_id)
        if category:
            category.children = self.get_children(category_id)
        return category

    def update_product_count(self, category_id: str) -> int:
        """Обновление счетчика продуктов в категории"""
        product_count = self.db.query(Product).filter(Product.category_id == category_id).count()
        category = self.get_by_id(category_id)
        if category:
            category.product_count = product_count
            self.db.commit()
        return product_count

    def search_categories(self, search_term: str) -> List[Category]:
        """Поиск категорий по названию"""
        return self.db.query(Category).filter(Category.name.ilike(f"%{search_term}%")).all()
