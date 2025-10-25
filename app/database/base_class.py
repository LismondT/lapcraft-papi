import uuid

from sqlalchemy import Column, String

from app.database.database import Base


class BaseModel(Base):
    __abstract__ = True

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
