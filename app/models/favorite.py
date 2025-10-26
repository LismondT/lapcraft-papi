from sqlalchemy import Column, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.database.base_class import BaseModel


class Favorite(BaseModel):
    __tablename__ = "favorites"

    user_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    product_id = Column(String, ForeignKey('products.id'), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    # Связи
    user = relationship("User", backref="favorites")
    product = relationship("Product")

    def __repr__(self):
        return f"<Favorite user_id={self.user_id} product_id={self.product_id}>"