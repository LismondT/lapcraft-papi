from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func

from app.database.base_class import BaseModel


class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"

    user_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<RefreshToken {self.token}>"