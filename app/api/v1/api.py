from fastapi import APIRouter

from app.api.v1.endpoints import products, category, auth, favorites, cart

api_router = APIRouter()

api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(category.router, prefix="/categories", tags=["categories"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
