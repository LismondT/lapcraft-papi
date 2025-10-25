from typing import Optional, Dict, Any, List, Set
from sqlalchemy.orm import Session, Query
from sqlalchemy import asc, desc, or_, func

from app.models.product import Product
from app.models.category import Category


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, product_id: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_by_id_with_category_name(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Получает продукт с названием категории в виде словаря"""
        result = self.db.query(
            Product,
            Category.name.label('category_name')
        ).outerjoin(
            Category, Product.category_id == Category.id
        ).filter(Product.id == product_id).first()

        if result:
            product, category_name = result
            return self._product_to_dict(product, category_name)
        return None

    def get_by_article(self, article: int) -> Optional[Product]:
        return self.db.query(Product).filter(Product.article == article).first()

    def get_next_article(self) -> int:
        max_article = self.db.query(func.max(Product.article)).scalar()
        return 1 if max_article is None else max_article + 1

    def create(self, product_data: Dict[str, Any]) -> Product:
        if product_data.get('article') is None:
            product_data['article'] = self.get_next_article()

        product = Product(**product_data)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)

        # Обновляем счетчики продуктов в категории и её родителях
        if product.category_id:
            from app.repositories.category_repository import CategoryRepository
            category_repo = CategoryRepository(self.db)
            category_repo.update_product_counts_for_category_tree(product.category_id)

        return product

    def update(self, product_id: str, update_data: Dict[str, Any]) -> Optional[Product]:
        old_product = self.get_by_id(product_id)
        old_category_id = old_product.category_id if old_product else None

        product = self.get_by_id(product_id)
        if product:
            for field, value in update_data.items():
                if hasattr(product, field):
                    setattr(product, field, value)
            self.db.commit()
            self.db.refresh(product)

            # Обновляем счетчики продуктов если изменилась категория
            new_category_id = product.category_id
            if old_category_id != new_category_id:
                from app.repositories.category_repository import CategoryRepository
                category_repo = CategoryRepository(self.db)

                # Обновляем старую категорию и её родителей
                if old_category_id:
                    category_repo.update_product_counts_for_category_tree(old_category_id)

                # Обновляем новую категорию и её родителей
                if new_category_id:
                    category_repo.update_product_counts_for_category_tree(new_category_id)

        return product

    def delete(self, product_id: str) -> bool:
        product = self.get_by_id(product_id)
        if product:
            category_id = product.category_id

            self.db.delete(product)
            self.db.commit()

            # Обновляем счетчики продуктов в категории и её родителях
            if category_id:
                from app.repositories.category_repository import CategoryRepository
                category_repo = CategoryRepository(self.db)
                category_repo.update_product_counts_for_category_tree(category_id)

            return True
        return False

    def get_paginated(
            self,
            page: int,
            count: int,
            filters: Optional[Dict[str, Any]] = None,
            sort: str = "id",
            order: str = "asc"
    ) -> List[Dict[str, Any]]:
        """Получение продуктов с названиями категорий в виде словарей"""
        # Создаем запрос с join для получения названия категории
        query = self.db.query(
            Product,
            Category.name.label('category_name')
        ).outerjoin(
            Category, Product.category_id == Category.id
        )

        # Применяем фильтры
        if filters:
            query = self._apply_filters(query, filters)

        # Применяем сортировку
        query = self._apply_sorting_with_join(query, sort, order)

        # Применяем пагинацию
        offset = (page - 1) * count
        results = query.offset(offset).limit(count).all()

        # Преобразуем в словари
        products_dict = []
        for product, category_name in results:
            products_dict.append(self._product_to_dict(product, category_name))

        return products_dict

    def get_total_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        query = self.db.query(Product)

        if filters:
            query = self._apply_filters(query, filters)

        return query.count()

    def _product_to_dict(self, product: Product, category_name: Optional[str] = None) -> Dict[str, Any]:
        """Преобразует объект Product в словарь"""
        product_dict = {
            "id": product.id,
            "article": product.article,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "category_id": product.category_id,
            "image_urls": product.image_urls or [],
            "stock_quantity": product.stock_quantity,
            "category_name": category_name
        }
        return product_dict

    def _apply_filters(self, query: Query, filters: Dict[str, Any]) -> Query:
        for field, value in filters.items():
            if value is None:
                continue

            # Обработка специальных фильтров
            if field == "min_price":
                query = query.filter(Product.price >= value)
                continue
            elif field == "max_price":
                query = query.filter(Product.price <= value)
                continue
            elif field == "category":
                # Фильтр по категории (включая подкатегории)
                query = self._apply_category_filter(query, value)
                continue

            # Обычные фильтры
            if hasattr(Product, field):
                column = getattr(Product, field)

                if isinstance(value, str):
                    query = query.filter(column.ilike(f"%{value}%"))
                elif isinstance(value, list):
                    query = query.filter(column.in_(value))
                else:
                    query = query.filter(column == value)
        return query

    def _apply_category_filter(self, query: Query, category_id: str) -> Query:
        """
        Применяет фильтр по категории, включая все подкатегории
        """
        # Получаем все ID категорий (основная + все подкатегории)
        category_ids = self._get_all_category_ids(category_id)

        # Фильтруем товары по всем найденным category_id
        return query.filter(Product.category_id.in_(category_ids))

    def _get_all_category_ids(self, category_id: str) -> List[str]:
        """
        Рекурсивно получает все ID категорий для заданной категории
        """

        def get_children_ids(parent_id: str, ids_set: Set[str]) -> Set[str]:
            # Находим все дочерние категории
            children = self.db.query(Category.id).filter(Category.parent_id == parent_id).all()
            children_ids = {child.id for child in children}

            # Добавляем найденные ID
            ids_set.update(children_ids)

            # Рекурсивно ищем детей для каждой дочерней категории
            for child_id in children_ids:
                get_children_ids(child_id, ids_set)

            return ids_set

        # Начинаем с основной категории
        all_ids = {category_id}
        get_children_ids(category_id, all_ids)

        return list(all_ids)

    def _apply_sorting_with_join(self, query: Query, sort: str, order: str) -> Query:
        """Сортировка для запроса с join"""
        if hasattr(Product, sort):
            column = getattr(Product, sort)
            if order.lower() == "desc":
                return query.order_by(desc(column))
            else:
                return query.order_by(asc(column))
        return query.order_by(Product.id)

    # Дополнительные методы

    def search_products(self, search_term: str, fields: List[str] = None) -> List[Dict[str, Any]]:
        if fields is None:
            fields = ["title", "description"]

        query = self.db.query(Product)
        conditions = []

        for field in fields:
            if hasattr(Product, field):
                column = getattr(Product, field)
                conditions.append(column.ilike(f"%{search_term}%"))

        if conditions:
            query = query.filter(or_(*conditions))

        products = query.all()
        return [self._product_to_dict(product) for product in products]

    def filter_by_price_range(self, min_price: Optional[float] = None,
                              max_price: Optional[float] = None) -> List[Dict[str, Any]]:
        query = self.db.query(Product)

        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        products = query.all()
        return [self._product_to_dict(product) for product in products]

    def get_by_category(self, category_id: str, include_subcategories: bool = True) -> List[Dict[str, Any]]:
        """
        Фильтрация по категории с опциональным включением подкатегорий
        """
        if include_subcategories:
            category_ids = self._get_all_category_ids(category_id)
            products = self.db.query(Product).filter(Product.category_id.in_(category_ids)).all()
        else:
            products = self.db.query(Product).filter(Product.category_id == category_id).all()

        return [self._product_to_dict(product) for product in products]