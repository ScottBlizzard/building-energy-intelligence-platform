import json
import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.anyio
async def test_mcp_stdio_server_can_be_initialized_and_called(tmp_path):
    backend_dir = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir)
    env["LLM_ENABLED"] = "false"
    env["MCP_TRANSPORT"] = "stdio"
    env["WORK_ORDER_FILE"] = str(tmp_path / "work_orders.json")
    env["BUDGET_FILE"] = str(tmp_path / "budgets.json")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_server"],
        env=env,
        cwd=str(backend_dir.parent),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}
            assert "get_energy_overview" in tool_names

            result = await session.call_tool("get_energy_overview", {})
            payload = json.loads(result.content[0].text)
            assert payload["total_records"] == 4864
            assert payload["average_cop"] == pytest.approx(2.99, abs=0.05)
