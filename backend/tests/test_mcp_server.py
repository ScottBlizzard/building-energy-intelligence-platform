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

    assert payload["record_count"] == 2976
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

    assert overview["average_cop"] == 2.99
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
    assert payload["record_count"] == 2976
