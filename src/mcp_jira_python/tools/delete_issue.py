from typing import List
from mcp.types import Tool, TextContent
from .base import BaseTool

class DeleteIssueTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="delete_issue",
            description="Delete a Jira issue or subtask",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string", 
                        "description": "Key of the issue to delete"
                    }
                },
                "required": ["issueKey"]
            }
        )

    async def execute(self, arguments: dict) -> List[TextContent]:
        issue_key = arguments.get("issueKey")
        if not issue_key:
            raise ValueError("issueKey is required")
        
        issue = self.jira.issue(issue_key)
        issue.delete()
        
        return [TextContent(
            type="text",
            text=f'{{"message": "Issue {issue_key} deleted successfully"}}'
        )]