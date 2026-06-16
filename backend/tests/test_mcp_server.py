import json

import pytest

from app.mcp_server import mcp


async def _call_tool(name: str, arguments: dict):
    result = await mcp.call_tool(name, arguments)
    assert result
    return json.loads(result[0].text)


@pytest.mark.anyio
async def test_mcp_lists_energy_tools():
    tools = await mcp.list_tools()
    tool_names = {tool.name for tool in tools}

    assert "get_dataset_meta" in tool_names
    assert "query_energy_records" in tool_names
    assert "get_time_summary" in tool_names
    assert "explain_anomaly" in tool_names
    assert "ask_energy_assistant" in tool_names


@pytest.mark.anyio
async def test_mcp_dataset_meta_tool_returns_project_dataset():
    payload = await _call_tool("get_dataset_meta", {})

    assert payload["record_count"] == 4864
    assert payload["building_count"] == 4
    assert "electricity_kwh" in payload["fields"]


@pytest.mark.anyio
async def test_mcp_query_records_supports_building_filter_and_limit():
    payload = await _call_tool(
        "query_energy_records",
        {"building_id": "BLD-C", "limit": 3},
    )

    assert payload["count"] == 3
    assert payload["total_filtered_count"] > 3
    assert all(item["building_id"] == "BLD-C" for item in payload["items"])


@pytest.mark.anyio
async def test_mcp_analytics_and_anomaly_tools():
    overview = await _call_tool("get_energy_overview", {})
    anomalies = await _call_tool("get_anomalies", {"limit": 1})
    explanation = await _call_tool(
        "explain_anomaly",
        {"record_id": anomalies["items"][0]["record_id"]},
    )

    assert overview["average_cop"] == pytest.approx(2.99, abs=0.05)
    assert anomalies["items"]
    assert explanation["item"]["record_id"] == anomalies["items"][0]["record_id"]
    assert explanation["item"]["recommended_action"]


@pytest.mark.anyio
async def test_mcp_resources_are_available():
    resources = await mcp.list_resources()
    resource_uris = {str(resource.uri) for resource in resources}

    assert "energy://dataset/meta" in resource_uris
    assert "energy://buildings" in resource_uris
    assert "energy://operation/report" in resource_uris

    contents = await mcp.read_resource("energy://dataset/meta")
    payload = json.loads(contents[0].content)
    assert payload["record_count"] == 4864


@pytest.mark.anyio
async def test_mcp_assistant_uses_work_order_grounding():
    from app.services.work_order_store import create_work_order

    order = create_work_order(
        {
            "work_order_id": "WO-MCP-GROUND-1",
            "source_record_id": "R-MCP-GROUND-1",
            "priority": "high",
            "building_id": "BLD-C",
            "building_name": "Library",
            "floor_label": "4F",
            "zone_name": "Reading",
            "equipment_id": "AHU-C-4F-06",
            "equipment_type": "AHU",
            "timestamp": "2026-05-01 10:00:00",
            "anomaly_reason": "equipment status abnormal",
            "possible_cause": "alarm",
            "recommended_action": "inspect AHU",
            "owner_role": "worker",
            "assignee_id": "worker_ahu",
            "status": "closed",
            "actual_cause": "filter blockage",
            "resolution_note": "cleaned filter",
        }
    )

    payload = await _call_tool("ask_energy_assistant", {"question": "刚关闭的工单是什么？"})
    assert payload["grounding_used"] is True
    assert payload["grounding_status"] == "grounded"
    assert order["work_order_id"] in payload["answer"]
