from fastapi import APIRouter, HTTPException

from app.schemas.assistant import AssistantQuery, AssistantReply
from app.services.assistant_service import build_assistant_reply


router = APIRouter()


@router.post("/query", response_model=AssistantReply)
def query_assistant(payload: AssistantQuery):
    try:
        return build_assistant_reply(payload.question)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

