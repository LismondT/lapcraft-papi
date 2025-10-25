from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_token(self, token: str) -> Optional[RefreshToken]:
        return self.db.query(RefreshToken).filter(RefreshToken.token == token).first()

    def get_by_user_id(self, user_id: str) -> List[RefreshToken]:
        return self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id).all()

    def create(self, user_id: str, token: str, expires_at: datetime) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)
        return refresh_token

    def revoke(self, token: str) -> bool:
        refresh_token = self.get_by_token(token)
        if refresh_token:
            refresh_token.is_revoked = True
            self.db.commit()
            return True
        return False

    def revoke_all_user_tokens(self, user_id: str) -> None:
        tokens = self.get_by_user_id(user_id)
        for token in tokens:
            token.is_revoked = True
        self.db.commit()

    def is_valid(self, token: str) -> bool:
        refresh_token = self.get_by_token(token)
        if not refresh_token:
            return False
        if refresh_token.is_revoked:
            return False
        if refresh_token.expires_at < datetime.utcnow():
            return False
        return True