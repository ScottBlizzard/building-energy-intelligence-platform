from fastapi import APIRouter

from app.services.demo_service import reset_demo

router = APIRouter()


@router.post("/reset")
def reset(seed: bool = True):
    """Reset the demo to its initial state (clear runtime + reseed references)."""
    return {"item": reset_demo(seed=seed)}
