from fastapi import APIRouter

from app.core.config import get_settings


router = APIRouter()


@router.get("/health")
def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.app_env,
        "data_file": str(settings.data_file),
        "knowledge_base_dir": str(settings.knowledge_base_dir),
    }

