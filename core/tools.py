import json
from typing import Optional, List
from mcp.types import CallToolResult, Tool, TextContent
from mcp_client import MCPClient
from google.genai import types


def _clean_schema(schema: dict) -> dict:
    """Remove JSON Schema keys that Gemini doesn't support."""
    if not schema:
        return schema
    cleaned = {}
    unsupported_keys = {
        "$schema",
        "additionalProperties",
        "$ref",
        "definitions",
    }
    for key, value in schema.items():
        if key in unsupported_keys:
            continue
        if isinstance(value, dict):
            cleaned[key] = _clean_schema(value)
        elif isinstance(value, list):
            cleaned[key] = [
                _clean_schema(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            cleaned[key] = value
    return cleaned


class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]) -> list:
        """Gets all tools from the provided clients as Gemini function declarations."""
        declarations = []
        for client in clients.values():
            tool_models = await client.list_tools()
            for t in tool_models:
                schema = (
                    _clean_schema(t.inputSchema) if t.inputSchema else None
                )
                declarations.append(
                    types.FunctionDeclaration(
                        name=t.name,
                        description=t.description or "",
                        parameters=schema,
                    )
                )
        if not declarations:
            return []
        return [types.Tool(function_declarations=declarations)]

    @classmethod
    async def _find_client_with_tool(
        cls, clients: list[MCPClient], tool_name: str
    ) -> Optional[MCPClient]:
        """Finds the first client that has the specified tool."""
        for client in clients:
            tools = await client.list_tools()
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                return client
        return None

    @classmethod
    async def execute_tool_requests(
        cls, clients: dict[str, MCPClient], function_calls: list[dict]
    ) -> list[dict]:
        """Executes function calls and returns function response dicts.

        function_calls: list of {"name": str, "args": dict}
        Returns: list of {"name": str, "response": dict}
        """
        function_responses = []
        for fc in function_calls:
            tool_name = fc["name"]
            tool_input = fc["args"]

            client = await cls._find_client_with_tool(
                list(clients.values()), tool_name
            )

            if not client:
                function_responses.append(
                    {
                        "name": tool_name,
                        "response": {"error": "Could not find that tool"},
                    }
                )
                continue

            try:
                tool_output: CallToolResult | None = await client.call_tool(
                    tool_name, tool_input
                )
                items = tool_output.content if tool_output else []
                content_list = [
                    item.text
                    for item in items
                    if isinstance(item, TextContent)
                ]
                result = {"result": json.dumps(content_list)}
                if tool_output and tool_output.isError:
                    result = {"error": json.dumps(content_list)}
                function_responses.append(
                    {
                        "name": tool_name,
                        "response": result,
                    }
                )
            except Exception as e:
                error_message = f"Error executing tool '{tool_name}': {e}"
                print(error_message)
                function_responses.append(
                    {
                        "name": tool_name,
                        "response": {"error": error_message},
                    }
                )

        return function_responses
