from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database.database import get_db
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    RefreshTokenRequest
)
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_token_expiration
)

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserCreate,
        db: Session = Depends(get_db)
):
    user_repo = UserRepository(db)
    refresh_token_repo = RefreshTokenRepository(db)

    # Проверяем, нет ли пользователя с таким email
    existing_user = user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Создаем пользователя
    user = user_repo.create(user_data.dict())

    # Создаем access token
    user_token_data = {
        "id": str(user.id),
        "email": user.email,
        "name": user.name
    }
    access_token = create_access_token(user_token_data)

    refresh_token = create_refresh_token()
    expires_at = get_token_expiration("refresh")

    # Сохраняем refresh token в базе
    refresh_token_repo.create(str(user.id), refresh_token, expires_at)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
async def login(
        login_data: UserLogin,
        db: Session = Depends(get_db)
):
    user_repo = UserRepository(db)
    refresh_token_repo = RefreshTokenRepository(db)

    # Аутентифицируем пользователя
    user = user_repo.authenticate(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Обновляем время последнего входа
    user_repo.update_last_login(user.id)

    # Создаем access token
    user_data = {
        "id": str(user.id),
        "email": user.email,
        "name": user.name
    }
    access_token = create_access_token(user_data)

    # Создаем refresh token
    refresh_token = create_refresh_token()
    expires_at = get_token_expiration("refresh")

    # Сохраняем refresh token в базе
    refresh_token_repo.create(str(user.id), refresh_token, expires_at)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
        refresh_data: RefreshTokenRequest,
        db: Session = Depends(get_db)
):
    refresh_token_repo = RefreshTokenRepository(db)
    user_repo = UserRepository(db)

    # Проверяем refresh token
    if not refresh_token_repo.is_valid(refresh_data.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Получаем токен из базы
    token_obj = refresh_token_repo.get_by_token(refresh_data.refresh_token)
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )

    # Получаем пользователя
    user = user_repo.get_by_id(token_obj.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Отзываем старый refresh token
    refresh_token_repo.revoke(refresh_data.refresh_token)

    # Создаем новые токены
    user_data = {
        "id": str(user.id),
        "email": user.email,
        "name": user.name
    }
    access_token = create_access_token(user_data)

    new_refresh_token = create_refresh_token()
    expires_at = get_token_expiration("refresh")

    # Сохраняем новый refresh token
    refresh_token_repo.create(str(user.id), new_refresh_token, expires_at)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(
        refresh_data: RefreshTokenRequest,
        db: Session = Depends(get_db)
):
    refresh_token_repo = RefreshTokenRepository(db)

    # Отзываем refresh token
    success = refresh_token_repo.revoke(refresh_data.refresh_token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token"
        )

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(current_user["id"])
    return user
