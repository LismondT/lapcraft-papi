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

        # Обновляем children_count у родительской категории
        if category.parent_id:
            self.update_children_count(category.parent_id)

        return category

    def update(self, category_id: str, update_data: Dict[str, Any]) -> Optional[Category]:
        category = self.get_by_id(category_id)
        old_parent_id = category.parent_id if category else None

        if category:
            for field, value in update_data.items():
                if hasattr(category, field):
                    setattr(category, field, value)
            self.db.commit()
            self.db.refresh(category)

            # Если изменился parent_id, обновляем children_count у старого и нового родителя
            new_parent_id = category.parent_id
            if old_parent_id != new_parent_id:
                if old_parent_id:
                    self.update_children_count(old_parent_id)
                if new_parent_id:
                    self.update_children_count(new_parent_id)

        return category

    def delete(self, category_id: str) -> bool:
        category = self.get_by_id(category_id)
        if category:
            parent_id = category.parent_id

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

            # Обновляем children_count у родительской категории
            if parent_id:
                self.update_children_count(parent_id)

            return True
        return False

    def update_children_count(self, category_id: str) -> None:
        """Обновляет счетчик дочерних категорий"""
        children_count = self.db.query(Category).filter(Category.parent_id == category_id).count()
        category = self.get_by_id(category_id)
        if category:
            category.children_count = children_count
            self.db.commit()

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
        """Обновление счетчика продуктов в категории (включая дочерние категории)"""
        # Получаем все ID категорий (включая дочерние)
        all_category_ids = self.get_all_subcategory_ids(category_id)

        # Считаем общее количество продуктов
        total_product_count = self.db.query(Product).filter(
            Product.category_id.in_(all_category_ids)
        ).count()

        # Обновляем счетчик для основной категории
        category = self.get_by_id(category_id)
        if category:
            category.product_count = total_product_count
            self.db.commit()

        return total_product_count

    def update_all_product_counts(self) -> None:
        """Обновляет счетчики продуктов для всех категорий"""
        categories = self.get_all_categories()
        for category in categories:
            self.update_product_count(category.id)

    def update_product_counts_for_category_tree(self, category_id: str) -> None:
        """Рекурсивно обновляет счетчики продуктов для категории и всех её родителей"""
        category = self.get_by_id(category_id)
        if not category:
            return

        # Обновляем текущую категорию
        self.update_product_count(category_id)

        # Рекурсивно обновляем всех родителей
        if category.parent_id:
            self.update_product_counts_for_category_tree(category.parent_id)

    def search_categories(self, search_term: str) -> List[Category]:
        """Поиск категорий по названию"""
        return self.db.query(Category).filter(Category.name.ilike(f"%{search_term}%")).all()