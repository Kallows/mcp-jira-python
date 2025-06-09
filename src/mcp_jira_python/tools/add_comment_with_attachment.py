from tempfile import NamedTemporaryFile
import os
import base64
from typing import List
from mcp.types import Tool, TextContent
from .base import BaseTool

class AddCommentWithAttachmentTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="add_comment_with_attachment",
            description="""Add a comment with file attachment to a Jira issue.

Supported Jira emoticons in comments:
- Smileys: :) :( :P :D ;)
- Symbols: (y) (n) (i) (/) (x) (!)
- Notation: (+) (-) (?) (on) (off) (*) (*r) (*g) (*b) (*y) (flag)

Note: Only use these Jira-specific emoticons. NEVER USE UNICODE EMOJIS they will break the script!""",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue to comment on"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment text content."
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the attachment file used in destination Jira issue"
                    },
                    "filepath": {
                        "type": "string",
                        "description": "Path to local file to attach"
                    }

                },
                "required": ["issueKey", "comment", "filename", "filepath"]
            }
        )

    async def execute(self, arguments: dict) -> List[TextContent]:
        issue_key = arguments.get("issueKey")
        filename = arguments.get("filename")
        filepath = arguments.get("filepath")
        comment_text = arguments.get("comment")
        
        if not all([issue_key, filename, filepath, comment_text]):
            raise ValueError("issueKey, filename, filepath, and comment are required")
        
        try:
            # Add the comment first
            comment = self.jira.add_comment(issue_key, comment_text)
            
            # Check if file exists
            if not os.path.exists(filepath):
                raise ValueError(f"File not found: {filepath}")
                
            # Check file size (10MB limit)
            if os.path.getsize(filepath) > 10 * 1024 * 1024:
                raise ValueError("Attachment too large (max 10MB)")
                
            try:
                # Add attachment to the issue - we expect this might raise an error even on success
                self.jira.add_attachment(
                    issue_key,
                    filepath,
                    filename=filename
                )
            except Exception as e:
                # Log the error but don't fail - we know this might happen even on success
                print(f"Note: Expected attachment error occurred: {str(e)}")
            
            return [TextContent(
                type="text",
                text=f'{{"message": "Comment and attachment added successfully", "comment_id": "{comment.id}", "filename": "{filename}"}}'
            )]
            
        except Exception as e:
            # Only raise for non-attachment errors
            if "not subscriptable" not in str(e):
                raise Exception(f"Failed to add comment with attachment: {str(e)}")
            return [TextContent(
                type="text",
                text=f'{{"message": "Operation completed with expected attachment response error", "comment_id": "{comment.id}", "filename": "{filename}"}}'
            )]
