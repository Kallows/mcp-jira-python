from typing import List
from mcp.types import Tool, TextContent
from .base import BaseTool

class ListFieldsTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="list_fields",
            description="List all available Jira fields",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )

    async def execute(self, arguments: dict) -> List[TextContent]:
        fields = self.jira.fields()
        return [TextContent(
            type="text",
            text=str([{
                "id": field["id"],
                "name": field["name"],
                "custom": field["custom"],
                "type": field["schema"]["type"] if "schema" in field else None
            } for field in fields])
        )]