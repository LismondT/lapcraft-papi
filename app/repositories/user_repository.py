from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import get_password_hash, verify_password


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create(self, user_data: Dict[str, Any]) -> User:
        # Хешируем пароль
        if 'password' in user_data:
            password = user_data['password']
            user_data['hashed_password'] = get_password_hash(password)
            del user_data['password']

        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(email)
        if not user:
            return None
        if not user.hashed_password or not verify_password(password, user.hashed_password):
            return None
        return user

    def update_last_login(self, user_id: str) -> None:
        from datetime import datetime
        user = self.get_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()