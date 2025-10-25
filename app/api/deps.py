from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import verify_access_token
from app.repositories.user_repository import UserRepository

security = HTTPBearer()


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> dict:
    """Получает текущего пользователя из JWT токена"""
    token = credentials.credentials
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(payload.get("sub"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "phone": user.phone,
        "is_superuser": user.is_superuser
    }


def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Проверяет, что пользователь активен"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )
    return current_user


def get_current_superuser(current_user: dict = Depends(get_current_user)) -> dict:
    """Проверяет, что пользователь - суперпользователь"""
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


def get_optional_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
) -> Optional[dict]:
    """Получает пользователя если токен есть, но не требует аутентификации"""
    if not credentials:
        return None

    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None
