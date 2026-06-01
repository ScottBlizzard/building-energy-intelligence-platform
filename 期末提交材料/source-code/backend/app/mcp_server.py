from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP

from app.core.config import get_settings
from app.services.analysis_service import (
    build_analysis_frame,
    build_anomaly_explanation,
    build_anomaly_reason_counts,
    build_anomaly_summary,
    build_anomaly_work_orders,
    build_building_comparison,
    build_cop_ranking,
    build_display_frame,
    build_equipment_summary,
    build_floor_summary,
    build_operation_report,
    build_optimization_recommendations,
    build_overview,
    build_time_summary,
    filter_display_frame_by_floor,
    to_serializable_records,
)
from app.services.assistant_service import build_assistant_reply
from app.services.data_loader import (
    get_building_options,
    get_dataset_meta as load_dataset_meta,
    get_filtered_dataset,
    read_dataset,
)
from app.services.knowledge_search_service import search_and_format_citations
from app.services.llm_client import build_external_assistant_answer
from app.services.work_order_store import list_work_orders


def _mcp_port() -> int:
    try:
        return int(os.getenv("MCP_PORT", "8765"))
    except ValueError:
        return 8765


mcp = FastMCP(
    "Building Energy Intelligence MCP",
    instructions=(
        "Expose building-energy dataset access, statistical analysis, anomaly "
        "diagnosis, operation reports, local knowledge search, and assistant "
        "question answering for the course project."
    ),
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=_mcp_port(),
    json_response=True,
    stateless_http=True,
)


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            "Invalid datetime. Use ISO format such as 2026-03-01T00:00:00."
        ) from exc

    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _limit(value: int, maximum: int = 500) -> int:
    return max(1, min(int(value), maximum))


def _load_analysis_frame(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
):
    frame = build_analysis_frame(
        get_filtered_dataset(
            building_id=building_id,
            start_time=_parse_datetime(start_time),
            end_time=_parse_datetime(end_time),
        )
    )
    if floor_label:
        frame = filter_display_frame_by_floor(frame, floor_label)
    return frame


def _merge_citations(existing, kb_result):
    seen_paths = {item["path"] for item in existing}
    merged = list(existing)
    for citation in kb_result.get("citations", []):
        if citation["path"] not in seen_paths:
            seen_paths.add(citation["path"])
            merged.append(citation)
    return merged


def _json(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def get_dataset_meta() -> dict:
    """Return dataset fields, building options, record count, and time range."""
    return load_dataset_meta()


@mcp.tool()
def list_buildings() -> dict:
    """List all buildings covered by the energy dataset."""
    return {"items": get_building_options()}


@mcp.tool()
def query_energy_records(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
) -> dict:
    """Query display-ready energy records by building, floor, time range, and limit."""
    frame = get_filtered_dataset(
        building_id=building_id,
        start_time=_parse_datetime(start_time),
        end_time=_parse_datetime(end_time),
    )
    display_frame = build_display_frame(frame)
    if floor_label:
        display_frame = filter_display_frame_by_floor(display_frame, floor_label)

    limited = display_frame.head(_limit(limit))
    return {
        "count": int(len(limited)),
        "total_filtered_count": int(len(display_frame)),
        "items": to_serializable_records(limited),
    }


@mcp.tool()
def get_energy_overview(
    building_id: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> dict:
    """Return total records, building count, average COP, anomalies, and totals."""
    frame = get_filtered_dataset(
        building_id=building_id,
        start_time=_parse_datetime(start_time),
        end_time=_parse_datetime(end_time),
    )
    return build_overview(frame)


@mcp.tool()
def get_time_summary(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    freq: Literal["H", "D", "W", "M"] = "D",
    limit: int = 120,
) -> dict:
    """Return hourly, daily, weekly, or monthly energy summary and average COP."""
    frame = _load_analysis_frame(building_id, floor_label, start_time, end_time)
    items = build_time_summary(frame, freq=freq)
    return {"items": items[: _limit(limit, 500)]}


@mcp.tool()
def get_building_comparison(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> dict:
    """Compare energy, water, HVAC, cooling load, and COP across buildings."""
    frame = get_filtered_dataset(
        start_time=_parse_datetime(start_time),
        end_time=_parse_datetime(end_time),
    )
    return {"items": build_building_comparison(frame)}


@mcp.tool()
def get_cop_ranking(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> dict:
    """Rank buildings by average cooling COP."""
    frame = get_filtered_dataset(
        start_time=_parse_datetime(start_time),
        end_time=_parse_datetime(end_time),
    )
    return {"items": build_cop_ranking(frame)}


@mcp.tool()
def get_anomalies(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 30,
) -> dict:
    """Return recent anomaly records with reason, equipment, floor, and status."""
    frame = _load_analysis_frame(building_id, floor_label, start_time, end_time)
    return {"items": build_anomaly_summary(frame)[: _limit(limit, 200)]}


@mcp.tool()
def get_anomaly_reasons(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> dict:
    """Count anomaly records by reason for charting and diagnosis."""
    frame = _load_analysis_frame(building_id, floor_label, start_time, end_time)
    return {"items": build_anomaly_reason_counts(frame)}


@mcp.tool()
def explain_anomaly(record_id: str) -> dict:
    """Explain one anomaly record and return triggered rules and actions."""
    explanation = build_anomaly_explanation(build_analysis_frame(read_dataset()), record_id)
    return {"item": explanation or None}


@mcp.tool()
def get_floor_summary(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> dict:
    """Return floor and zone level energy, COP, anomaly rate, and operation focus."""
    frame = _load_analysis_frame(building_id, floor_label, start_time, end_time)
    return {"items": build_floor_summary(frame)}


@mcp.tool()
def get_equipment_summary(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 120,
) -> dict:
    """Return equipment status, latest seen time, priority, and maintenance hint."""
    frame = _load_analysis_frame(building_id, floor_label, start_time, end_time)
    return {"items": build_equipment_summary(frame)[: _limit(limit, 500)]}


@mcp.tool()
def suggest_anomaly_work_orders(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 30,
) -> dict:
    """Suggest work orders from current anomaly records without writing to storage."""
    frame = _load_analysis_frame(building_id, floor_label, start_time, end_time)
    return {"items": build_anomaly_work_orders(frame)[: _limit(limit, 100)]}


@mcp.tool()
def get_optimization_recommendations(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> dict:
    """Return energy optimization recommendations ranked by priority."""
    frame = _load_analysis_frame(building_id, floor_label, start_time, end_time)
    return {"items": build_optimization_recommendations(frame)}


@mcp.tool()
def get_operation_report(
    building_id: Optional[str] = None,
    floor_label: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> dict:
    """Generate an operation report summary for the selected scope."""
    frame = _load_analysis_frame(building_id, floor_label, start_time, end_time)
    return {"item": build_operation_report(frame, list_work_orders())}


@mcp.tool()
def search_energy_knowledge(query: str, top_k: int = 3) -> dict:
    """Search local energy-operation knowledge base and return citations."""
    return search_and_format_citations(query, top_k=_limit(top_k, 10))


@mcp.tool()
def ask_energy_assistant(
    question: str,
    use_external_llm: bool = False,
) -> dict:
    """Answer an energy O&M question using local rules, KB citations, and optional LLM."""
    reply = build_assistant_reply(question)
    kb_result = search_and_format_citations(question)
    reply["citations"] = _merge_citations(reply["citations"], kb_result)
    reply["llm_used"] = False

    if use_external_llm:
        external_answer = build_external_assistant_answer(question, reply, kb_result)
        if external_answer:
            reply["answer"] = external_answer["answer"]
            reply["llm_used"] = True
            reply["llm_provider"] = external_answer["provider"]
            reply["llm_model"] = external_answer["model"]

    return reply


@mcp.resource(
    "energy://dataset/meta",
    mime_type="application/json",
    description="Dataset metadata including fields, buildings, record count, and time range.",
)
def dataset_meta_resource() -> str:
    return _json(load_dataset_meta())


@mcp.resource(
    "energy://buildings",
    mime_type="application/json",
    description="Building options covered by the project energy dataset.",
)
def buildings_resource() -> str:
    return _json({"items": get_building_options()})


@mcp.resource(
    "energy://operation/report",
    mime_type="application/json",
    description="Current whole-project building energy operation report.",
)
def operation_report_resource() -> str:
    frame = build_analysis_frame(read_dataset())
    return _json({"item": build_operation_report(frame, list_work_orders())})


@mcp.resource(
    "energy://knowledge/readme",
    mime_type="text/markdown",
    description="Knowledge base entry document.",
)
def knowledge_readme_resource() -> str:
    path = get_settings().knowledge_base_dir / "README.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


@mcp.prompt()
def energy_operation_prompt(question: str) -> str:
    """Create a course-demo prompt for the building energy assistant."""
    return (
        "You are the building energy intelligent operation assistant for this "
        "course project. Use MCP tools first to inspect dataset metadata, "
        "records, COP, anomalies, work-order suggestions, and knowledge-base "
        f"citations. User question: {question}"
    )


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise ValueError("MCP_TRANSPORT must be stdio, sse, or streamable-http")
    try:
        mcp.run(transport=transport)
    except KeyboardInterrupt:
        print("MCP server stopped by user.", file=sys.stderr)


if __name__ == "__main__":
    main()
