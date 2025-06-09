from typing import List
from mcp.types import Tool, TextContent
from .base import BaseTool

class UpdateIssueTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="update_issue",
            description="Update an existing Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue to update"
                    },
                    "summary": {
                        "type": "string",
                        "description": "New summary/title"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Email of new assignee"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status"
                    },
                    "priority": {
                        "type": "string",
                        "description": "New priority"
                    }
                },
                "required": ["issueKey"]
            }
        )

    async def execute(self, arguments: dict) -> List[TextContent]:
        issue_key = arguments.get("issueKey")
        if not issue_key:
            raise ValueError("issueKey is required")
            
        update_fields = {}
        field_mappings = {
            "summary": lambda x: x,
            "description": lambda x: x,
            "assignee": lambda x: {"emailAddress": x},
            "status": lambda x: {"name": x},
            "priority": lambda x: {"name": x}
        }
        
        for field, transform in field_mappings.items():
            if field in arguments:
                update_fields[field] = transform(arguments[field])

        issue = self.jira.issue(issue_key)
        issue.update(fields=update_fields)
        
        return [TextContent(
            type="text",
            text=f'{{"message": "Issue {issue_key} updated successfully"}}'
        )]