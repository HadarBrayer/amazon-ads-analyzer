from fastapi import APIRouter

from src.routes import health, targeting_report

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(targeting_report.router)
