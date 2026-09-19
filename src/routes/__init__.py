from fastapi import APIRouter

from src.routes import health

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
