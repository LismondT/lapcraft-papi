import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets


from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Секретные ключи
SECRET_KEY = settings.secret_key
REFRESH_SECRET_KEY = settings.refresh_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 минут
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 дней


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, Exception):
        return False


def get_password_hash(password: str) -> str:
    """Хеширует пароль"""
    if len(password.encode("utf-8")) > 72:
        password = hashlib.sha256(password.encode("utf-8")).hexdigest()

    return pwd_context.hash(password)


def create_access_token(user: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Создает access token"""
    to_encode = {
        "sub": str(user["id"]),
        "email": user["email"],
        "name": user["name"]
    }

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token() -> str:
    """Создает refresh token (случайная строка)"""
    return secrets.token_urlsafe(32)


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Проверяет access token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_token_expiration(token_type: str = "access") -> datetime:
    """Получает время истечения токена"""
    if token_type == "access":
        return datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        return datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)