from typing import List
from mcp.types import Tool, TextContent
from .base import BaseTool

class ListIssueTypesTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="list_issue_types",
            description="List all available issue types",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )

    async def execute(self, arguments: dict) -> List[TextContent]:
        issue_types = self.jira.issue_types()
        return [TextContent(
            type="text",
            text=str([{
                "id": it.id,
                "name": it.name,
                "description": it.description,
                "subtask": it.subtask
            } for it in issue_types])
        )]