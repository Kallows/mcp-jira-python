from typing import List
from mcp.types import Tool, TextContent
from .base import BaseTool

class GetUserTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="get_user",
            description="Get a user's account ID by email address",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "User's email address"
                    }
                },
                "required": ["email"]
            }
        )

    async def execute(self, arguments: dict) -> List[TextContent]:
        email = arguments.get("email")
        if not email:
            raise ValueError("email is required")
            
        users = self.jira.search_users(query=email)
        if not users:
            raise ValueError(f"No user found with email: {email}")
            
        user = users[0]
        return [TextContent(
            type="text",
            text=str({
                "accountId": user.accountId,
                "displayName": user.displayName,
                "emailAddress": user.emailAddress,
                "active": user.active
            })
        )]