import json
import sys
import io
from typing import List
from mcp.types import Tool, TextContent
from .base import BaseTool

# Force UTF-8 encoding for stdout on Windows
# This is critical for emoji output on Windows systems
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class GetIssueTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="get_issue",
            description="Get complete issue details including comments and attachments",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Issue key (e.g., MRR-86)"
                    }
                },
                "required": ["issueKey"]
            }
        )

    async def execute(self, arguments: dict) -> List[TextContent]:
        issue_key = arguments.get("issueKey")
        if not issue_key:
            raise ValueError("issueKey is required")
            
        try:
            issue = self.jira.issue(issue_key, expand='comments,attachments')
            
            comments = [{
                "id": comment.id,
                "author": str(comment.author),
                "body": comment.body,
                "created": str(comment.created)
            } for comment in issue.fields.comment.comments]
            
            attachments = [{
                "id": attachment.id,
                "filename": attachment.filename,
                "size": attachment.size,
                "created": str(attachment.created)
            } for attachment in issue.fields.attachment]
            
            # Create a dictionary with all the issue data
            issue_data = {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": str(issue.fields.status),
                "priority": str(issue.fields.priority) if hasattr(issue.fields, 'priority') else None,
                "assignee": str(issue.fields.assignee) if hasattr(issue.fields, 'assignee') else None,
                "type": str(issue.fields.issuetype),
                "comments": comments,
                "attachments": attachments
            }
            
            # Use json.dumps with ensure_ascii=False to properly handle Unicode characters
            return [TextContent(
                type="text",
                text=json.dumps(issue_data, ensure_ascii=False)
            )]
            
        except Exception as e:
            if isinstance(e, UnicodeError):
                # Handle Unicode errors specifically
                return [TextContent(
                    type="text",
                    text=f"Unicode encoding error while processing the issue: {str(e)}",
                    isError=True
                )]
            else:
                raise Exception(f"Failed to get issue: {str(e)}")
