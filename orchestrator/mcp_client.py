"""
MCP Client — connects to Model Context Protocol servers and converts
their tools into LangChain-compatible StructuredTools.

Supports both **stdio** (local process) and **SSE** (remote HTTP) transports.

Usage:
    # In config or .env, define MCP servers:
    MCP_SERVERS = {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        },
        "remote-api": {
            "url": "http://localhost:8080/sse"
        }
    }

    tools = await load_mcp_tools(MCP_SERVERS)
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from langchain_core.tools import StructuredTool

from .config import MCP_SERVERS


async def _load_stdio_tools(name: str, server_config: dict) -> list[StructuredTool]:
    """Connect to a stdio MCP server and extract its tools."""
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        print(f"  [MCP] 'mcp' package not installed — skipping server '{name}'")
        return []

    command = server_config.get("command", "")
    args = server_config.get("args", [])
    env = server_config.get("env")

    params = StdioServerParameters(command=command, args=args, env=env)

    tools: list[StructuredTool] = []

    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()

                for mcp_tool in result.tools:
                    tool = _wrap_mcp_tool(session, mcp_tool)
                    tools.append(tool)
                    print(f"  [MCP] {name}/{mcp_tool.name} loaded")

    except Exception as exc:
        print(f"  [MCP] Failed to connect to '{name}': {exc}")

    return tools


async def _load_sse_tools(name: str, server_config: dict) -> list[StructuredTool]:
    """Connect to an SSE (HTTP) MCP server and extract its tools."""
    try:
        from mcp import ClientSession
        from mcp.client.sse import sse_client
    except ImportError:
        print(f"  [MCP] 'mcp' package not installed — skipping server '{name}'")
        return []

    url = server_config.get("url", "")
    tools: list[StructuredTool] = []

    try:
        async with sse_client(url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()

                for mcp_tool in result.tools:
                    tool = _wrap_mcp_tool(session, mcp_tool)
                    tools.append(tool)
                    print(f"  [MCP] {name}/{mcp_tool.name} loaded")

    except Exception as exc:
        print(f"  [MCP] Failed to connect to '{name}': {exc}")

    return tools


def _wrap_mcp_tool(session, mcp_tool) -> StructuredTool:
    """Convert a single MCP tool into a LangChain StructuredTool."""

    tool_name = mcp_tool.name
    description = mcp_tool.description or tool_name

    # Create a callable that invokes the MCP tool
    # We capture the session and tool name in the closure
    _session = session
    _tool_name = tool_name

    def call_mcp_tool(**kwargs: Any) -> str:
        """Call the MCP tool synchronously by running the async call in a new loop."""
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                _session.call_tool(_tool_name, arguments=kwargs)
            )
            loop.close()

            # MCP returns a list of content items
            parts = []
            for item in result.content:
                if hasattr(item, "text"):
                    parts.append(item.text)
                else:
                    parts.append(str(item))
            return "\n".join(parts)

        except Exception as exc:
            return f"[MCP tool {_tool_name} error] {exc}"

    call_mcp_tool.__name__ = tool_name
    call_mcp_tool.__doc__ = description

    return StructuredTool.from_function(
        func=call_mcp_tool,
        name=tool_name,
        description=description,
    )


async def _load_all_mcp_tools(servers: dict) -> list[StructuredTool]:
    """Load tools from all configured MCP servers."""
    all_tools: list[StructuredTool] = []

    for name, config in servers.items():
        if "url" in config:
            tools = await _load_sse_tools(name, config)
        elif "command" in config:
            tools = await _load_stdio_tools(name, config)
        else:
            print(f"  [MCP] Unknown server config for '{name}' — skipping")
            continue
        all_tools.extend(tools)

    return all_tools


def load_mcp_tools(servers: dict | None = None) -> list[StructuredTool]:
    """Synchronous entry point: load tools from configured MCP servers.

    Returns an empty list if no servers are configured or if the mcp
    package is not installed.
    """
    servers = servers or MCP_SERVERS
    if not servers:
        return []

    print("\n[MCP] Loading tools from configured servers ...")

    try:
        loop = asyncio.new_event_loop()
        tools = loop.run_until_complete(_load_all_mcp_tools(servers))
        loop.close()
    except Exception as exc:
        print(f"[MCP] Error loading tools: {exc}")
        tools = []

    print(f"[MCP] {len(tools)} tool(s) loaded from {len(servers)} server(s)")
    return tools
