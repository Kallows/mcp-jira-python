import os
from typing import List
from mcp.types import Tool, TextContent
from .base import BaseTool

class AttachFileTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="attach_file",
            description="Add the named filepath file as an attachment to a Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue to attach to"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the attachment file in issue"
                    },
                    "filepath": {
                        "type": "string",
                        "description": "Filepath is file to attach"
                    }
                },
                "required": ["issueKey", "filename", "filepath"]
            }
        )

    async def execute(self, arguments: dict) -> List[TextContent]:
        issue_key = arguments.get("issueKey")
        filename = arguments.get("filename")
        filepath = arguments.get("filepath")
        
        if not all([issue_key, filename, filepath]):
            raise ValueError("issueKey, filename, and filepath are required")
            
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                raise ValueError(f"File not found: {filepath}")
                
            # Check file size (10MB limit)
            if os.path.getsize(filepath) > 10 * 1024 * 1024:
                raise ValueError("Attachment too large (max 10MB)")
            
            # Use add_attachment which is the correct method in the JIRA API
            # This does not involve base64 encoding/decoding when used with file paths
            self.jira.add_attachment(issue_key, filepath, filename=filename)
            
            return [TextContent(
                type="text",
                text=f'{{"message": "File attached successfully", "filename": "{filename}"}}'
            )]
            
        except Exception as e:
            raise Exception(f"Failed to attach file: {str(e)}")
