from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    description="建筑能源智能管理与运维优化系统后端骨架",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["root"])
def root():
    return {
        "message": "Building Energy Intelligence Platform backend is running.",
        "docs": "/docs",
        "api_prefix": settings.api_v1_prefix,
    }

