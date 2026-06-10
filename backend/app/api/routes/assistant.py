from fastapi import APIRouter, HTTPException

from app.schemas.assistant import AssistantProviderList, AssistantQuery, AssistantReply
from app.services.assistant_service import build_assistant_reply
from app.services.grounding_service import (
    build_grounded_fallback_reply,
    build_work_order_grounding_context,
    format_grounding_context_for_llm,
    validate_grounded_answer,
)
from app.services.knowledge_search_service import search_and_format_citations
from app.services.llm_client import build_external_assistant_answer, list_llm_model_options


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
        reply["llm_provider"] = payload.provider
        reply["llm_model"] = payload.model
        grounding_context = build_work_order_grounding_context(payload.question)
        grounding_text = format_grounding_context_for_llm(grounding_context)
        if grounding_context.get("applies"):
            reply = build_grounded_fallback_reply(payload.question, grounding_context, reply)
            reply["llm_provider"] = payload.provider
            reply["llm_model"] = payload.model
        else:
            reply.setdefault("grounding_used", False)
            reply.setdefault("grounding_sources", [])
            reply.setdefault("grounding_status", "none")
            reply.setdefault("validation_warnings", [])
            reply.setdefault("referenced_entities", {})

        external_answer = build_external_assistant_answer(
            payload.question,
            reply,
            kb_result,
            grounding_context_text=grounding_text,
        )
        if external_answer:
            validation = validate_grounded_answer(external_answer["answer"], grounding_context)
            if validation["valid"]:
                reply["answer"] = external_answer["answer"]
                reply["llm_used"] = True
                reply["llm_provider"] = external_answer["provider"]
                reply["llm_model"] = external_answer["model"]
                if grounding_context.get("applies"):
                    reply["grounding_status"] = "validated"
                    reply["grounding_used"] = True
                    reply["grounding_sources"] = ["work_orders", "knowledge_base", "external_llm"]
                    if validation.get("referenced_entities"):
                        reply["referenced_entities"] = validation["referenced_entities"]
                reply["validation_warnings"] = []
            else:
                reply["llm_used"] = False
                reply["grounding_status"] = "fallback_after_validation"
                reply["validation_warnings"] = validation["warnings"]
        else:
            reply["llm_used"] = False
        return reply
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/providers", response_model=AssistantProviderList)
def get_assistant_providers():
    return list_llm_model_options()

