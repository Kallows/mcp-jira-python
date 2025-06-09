from typing import List
from mcp.types import Tool, TextContent
from .base import BaseTool

class CreateIssueTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="create_jira_issue",
            description="""Create a new Jira issue. 
            
Supported Jira emoticons in description:
- Smileys: :) :( :P :D ;)
- Symbols: (y) (n) (i) (/) (x) (!)
- Notation: (+) (-) (?) (on) (off) (*) (*r) (*g) (*b) (*y) (flag)

Note: Only use these Jira-specific emoticons. Unicode emojis will not display correctly.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "projectKey": {
                        "type": "string",
                        "description": "Project key where the issue will be created (e.g., 'TEST')"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Issue summary/title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Issue description. Supports Jira emoticons like :) (y) (i) - see tool description for full list"
                    },
                    "issueType": {
                        "type": "string",
                        "description": "Type of issue (e.g., 'Bug', 'Task', 'Story')"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Issue priority"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Email of the assignee"
                    }
                },
                "required": ["projectKey", "summary", "issueType"]
            }
        )

    async def execute(self, arguments: dict) -> List[TextContent]:
        project_key = arguments.get("projectKey")
        summary = arguments.get("summary") 
        issue_type = arguments.get("issueType")
        
        if not all([project_key, summary, issue_type]):
            raise ValueError("projectKey, summary, and issueType are required")
        
        issue_dict = {
            'project': {'key': project_key},
            'summary': summary,
            'issuetype': {'name': issue_type}
        }
        
        for field in ["description", "priority", "assignee"]:
            if field in arguments:
                if field == "assignee":
                    issue_dict[field] = {'emailAddress': arguments[field]}
                elif field == "priority":
                    issue_dict[field] = {'name': arguments[field]}
                else:
                    issue_dict[field] = arguments[field]
        
        issue = self.jira.create_issue(fields=issue_dict)
        
        return [TextContent(
            type="text",
            text=str({
                "key": issue.key,
                "id": issue.id,
                "self": issue.self
            })
        )]
