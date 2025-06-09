from typing import List
from mcp.types import Tool, TextContent
from .base import BaseTool
import os

class GetIssueAttachmentTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="get_issue_attachment",
            description="Download an attachment from a Jira issue to a local file. If neither attachmentId nor filename is provided, all attachments will be downloaded. Original filenames preserved.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue containing the attachment"
                    },
                    "attachmentId": {
                        "type": "string",
                        "description": "ID of the attachment to download (optional if filename is provided)"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the attachment file to download (optional if attachmentId is provided)"
                    },
                    "outputPath": {
                        "type": "string",
                        "description": "Local path where to save the downloaded file (optional, defaults to current directory with original filename)"
                    }
                },
                "required": ["issueKey"]
            }
        )


    async def execute(self, arguments: dict) -> List[TextContent]:
        issue_key = arguments.get("issueKey")
        attachment_id = arguments.get("attachmentId")
        filename = arguments.get("filename")
        output_path = arguments.get("outputPath", ".")
        
        if not issue_key:
            raise ValueError("issueKey is required")
            
        # If neither attachment_id nor filename is provided, download all attachments
        download_all = not attachment_id and not filename
            
        # If no output path specified, use current directory but maintain original filename
        if not output_path:
            output_path = "."
            
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.abspath(output_path), exist_ok=True)
            
            # If attachment_id is provided, download directly
            if attachment_id:
                attachment = self.jira.attachment(attachment_id)
                file_path = os.path.join(output_path, attachment.filename)
                
                # Download the content
                attachment_data = attachment.get()
                
                # Write to file
                with open(file_path, 'wb') as f:
                    f.write(attachment_data)
                
                return [TextContent(
                    type="text",
                    text=str({
                        "message": "Attachment downloaded successfully",
                        "filename": attachment.filename,
                        "path": file_path,
                        "size": attachment.size
                    })
                )]
            
            # Get issue with attachments
            issue = self.jira.issue(issue_key, expand='attachments')
            
            if not hasattr(issue.fields, 'attachment') or not issue.fields.attachment:
                raise ValueError(f"No attachments found in issue {issue_key}")
            
            # If download_all is True, download all attachments
            if download_all:
                downloaded_files = []
                
                for attachment in issue.fields.attachment:
                    file_path = os.path.join(output_path, attachment.filename)
                    
                    # Download the content
                    attachment_data = attachment.get()
                    
                    # Write to file
                    with open(file_path, 'wb') as f:
                        f.write(attachment_data)
                    
                    downloaded_files.append({
                        "filename": attachment.filename,
                        "path": file_path,
                        "size": attachment.size,
                        "id": attachment.id
                    })
                
                return [TextContent(
                    type="text",
                    text=str({
                        "message": f"Downloaded {len(downloaded_files)} attachments successfully",
                        "files": downloaded_files,
                        "outputPath": output_path
                    })
                )]
            
            # If filename is provided, find the specific attachment
            found = False
            for attachment in issue.fields.attachment:
                if attachment.filename == filename:
                    file_path = os.path.join(output_path, attachment.filename)
                    
                    # Download the content
                    attachment_data = attachment.get()
                    
                    # Write to file
                    with open(file_path, 'wb') as f:
                        f.write(attachment_data)
                    
                    found = True
                    return [TextContent(
                        type="text",
                        text=str({
                            "message": "Attachment downloaded successfully",
                            "filename": attachment.filename,
                            "path": file_path,
                            "size": attachment.size,
                            "id": attachment.id
                        })
                    )]
            
            if not found:
                raise ValueError(f"Attachment '{filename}' not found in issue {issue_key}")
            
        except Exception as e:
            raise Exception(f"Failed to download attachment: {str(e)}")