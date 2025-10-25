from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base_class import BaseModel


class Category(BaseModel):
    __tablename__ = "categories"

    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(String, ForeignKey('categories.id'), nullable=True, index=True)
    icon = Column(String, nullable=True)
    color = Column(String, nullable=True)
    product_count = Column(Integer, default=0)

    # Связь с родительской категорией
    parent = relationship(
        "Category",
        remote_side="Category.id",
        backref="children",
        foreign_keys=[parent_id]
    )

    # Связь с продуктами
    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"