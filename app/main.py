from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import settings
from app.database.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.include_router(api_router, prefix="/api/v1")

@app.get("/api/health")
def health():
    return {"status": "ok"}
