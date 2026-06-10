from fastapi import APIRouter

from app.api.routes import (
    admin,
    analytics,
    anomaly_events,
    assistant,
    auth,
    building_detail,
    data,
    export,
    health,
    work_orders,
)


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(data.router, tags=["data"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(building_detail.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(anomaly_events.router, prefix="/anomaly-events", tags=["anomaly-events"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(work_orders.router, prefix="/work-orders", tags=["work-orders"])

