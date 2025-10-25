from sqlalchemy import Column, String, Boolean, DateTime, func

from app.database.base_class import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    hashed_password = Column(String)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<User {self.email}>"
