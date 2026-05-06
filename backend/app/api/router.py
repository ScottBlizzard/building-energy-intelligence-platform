from fastapi import APIRouter

from app.api.routes import analytics, assistant, building_detail, data, export, health


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(data.router, tags=["data"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(building_detail.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
api_router.include_router(export.router, prefix="/export", tags=["export"])

