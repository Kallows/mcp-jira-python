import asyncio
import os
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from jira import JIRA
#from tools import get_all_tools, get_tool  # Changed from relative import
from mcp_jira_python.tools import get_all_tools, get_tool

server = Server("jira-api")

# Jira client setup 
JIRA_HOST = os.getenv("JIRA_HOST")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

if not all([JIRA_HOST, JIRA_EMAIL, JIRA_API_TOKEN]):
    raise ValueError("Missing required environment variables")

jira_client = JIRA(
    server=f"https://{JIRA_HOST}",
    basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return get_all_tools()

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    try:
        tool = get_tool(name)
        tool.jira = jira_client
        return await tool.execute(arguments or {})
    except Exception as e:
        return [types.TextContent(
            type="text", 
            text=f"Operation failed: {str(e)}",
            isError=True
        )]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jira-api",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
