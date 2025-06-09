from typing import List
from mcp.types import Tool, TextContent
from .base import BaseTool

class AddCommentTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="add_comment",
            description="""Add a comment to a Jira issue.

Supported Jira emoticons comments:
- Smileys: :) :( :P :D ;)
- Symbols: (y) (n) (i) (/) (x) (!)
- Notation: (+) (-) (?) (on) (off) (*) (*r) (*g) (*b) (*y) (flag)

Note: Only use these Jira-specific emoticons. Unicode emojis will not display correctly.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue to comment on"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment text content. Supports Jira emoticons like :) (y) (i) - see tool description for full list"
                    }
                },
                "required": ["issueKey", "comment"]
            }
        )

    async def execute(self, arguments: dict) -> List[TextContent]:
        issue_key = arguments.get("issueKey")
        comment_text = arguments.get("comment")
        
        if not issue_key or not comment_text:
            raise ValueError("issueKey and comment are required")
            
        comment = self.jira.add_comment(issue_key, comment_text)
        
        return [TextContent(
            type="text",
            text=f'{{"message": "Comment added successfully", "id": "{comment.id}"}}'
        )]
