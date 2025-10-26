from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, func

from app.database.base_class import BaseModel


class CartItem(BaseModel):
    __tablename__ = "cart_items"

    user_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    product_id = Column(String, ForeignKey('products.id'), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<CartItem user_id={self.user_id} product_id={self.product_id} quantity={self.quantity}>"
