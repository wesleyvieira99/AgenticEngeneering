import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_real_mcp_handshake_discovery_and_denied_write():
    parameters = StdioServerParameters(command=sys.executable, args=["-m", "packages.mcp.server"], cwd=str(Path(__file__).resolve().parents[2]), env={**os.environ, "ATLAS_MCP_SCOPES": "tickets:read", "ATLAS_MCP_TOKEN": "not-used-for-denied-write"})
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            assert initialized.serverInfo.name == "Atlas scoped tools"
            tools = await session.list_tools()
            assert {t.name for t in tools.tools} == {"tickets_list", "tickets_propose", "documents_list"}
            denied = await session.call_tool("tickets_propose", {"title": "Must not execute"})
            assert denied.isError
            assert "Scope required" in str(denied.content)
            resources = await session.list_resources()
            assert str(resources.resources[0].uri) == "atlas://security-policy"
            policy = await session.read_resource("atlas://security-policy")
            assert "human approval" in str(policy.contents)
