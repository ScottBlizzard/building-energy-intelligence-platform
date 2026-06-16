from fastapi import APIRouter, Header

from app.api.deps import require_admin_user
from app.services.demo_service import reset_demo

router = APIRouter()


@router.post("/reset")
def reset(seed: bool = True, operator_id: str = "admin", authorization: str = Header(default="")):
    """Reset the demo to its initial state (clear runtime + reseed references)."""
    require_admin_user(
        operator_id=operator_id,
        authorization=authorization,
        action="reset the demo state",
    )
    return {"item": reset_demo(seed=seed)}
