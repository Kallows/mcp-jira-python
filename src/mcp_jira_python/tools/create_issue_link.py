from typing import List
from mcp.types import Tool, TextContent
from .base import BaseTool

class CreateIssueLinkTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="create_issue_link",
            description="Create a link between two issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "inwardIssueKey": {
                        "type": "string",
                        "description": "Key of the inward issue (e.g., blocked issue)"
                    },
                    "outwardIssueKey": {
                        "type": "string",
                        "description": "Key of the outward issue (e.g., blocking issue)"
                    },
                    "linkType": {
                        "type": "string",
                        "description": "Type of link (e.g., 'blocks')"
                    }
                },
                "required": ["inwardIssueKey", "outwardIssueKey", "linkType"]
            }
        )

    async def execute(self, arguments: dict) -> List[TextContent]:
        inward_issue = arguments.get("inwardIssueKey")
        outward_issue = arguments.get("outwardIssueKey")
        link_type = arguments.get("linkType")
        
        if not all([inward_issue, outward_issue, link_type]):
            raise ValueError("inwardIssueKey, outwardIssueKey, and linkType are required")
            
        self.jira.create_issue_link(
            type=link_type,
            inwardIssue=inward_issue,
            outwardIssue=outward_issue
        )
        
        # Fixed JSON field case to match our test expectations
        return [TextContent(
            type="text",
            text=f'{{"message": "Issue link created successfully", "inwardIssue": "{inward_issue}", "outwardIssue": "{outward_issue}", "linkType": "{link_type}"}}'
        )]