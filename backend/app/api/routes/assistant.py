from fastapi import APIRouter, HTTPException

from app.schemas.assistant import AssistantQuery, AssistantReply
from app.services.assistant_service import build_assistant_reply
from app.services.knowledge_search_service import search_and_format_citations


router = APIRouter()


def _enrich_citations(existing, kb_result):
    """Merge hardcoded citations with knowledge-search citations, deduplicating by path."""
    seen_paths = {item["path"] for item in existing}
    merged = list(existing)
    for citation in kb_result.get("citations", []):
        if citation["path"] not in seen_paths:
            seen_paths.add(citation["path"])
            merged.append(citation)
    return merged


@router.post("/query", response_model=AssistantReply)
def query_assistant(payload: AssistantQuery):
    try:
        reply = build_assistant_reply(payload.question)
        kb_result = search_and_format_citations(payload.question)
        reply["citations"] = _enrich_citations(reply["citations"], kb_result)
        return reply
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

