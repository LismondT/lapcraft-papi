from sqlalchemy import Column, Integer, String, Float, Text, JSON, ForeignKey

from sqlalchemy.orm import relationship
from app.database.base_class import BaseModel


class Product(BaseModel):
    __tablename__ = "products"

    article = Column(Integer, unique=True, index=True, nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category_id = Column(String, ForeignKey('categories.id'), nullable=True, index=True)
    image_urls = Column(JSON, default=list)
    stock_quantity = Column(Integer, default=0)

    # Связь с категорией
    category = relationship("Category", back_populates="products")

    def __repr__(self):
        return f"<Product {self.title}>"
