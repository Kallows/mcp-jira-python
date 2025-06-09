from typing import List
from mcp.types import Tool, TextContent
from .base import BaseTool

class SearchIssuesTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="search_issues",
            description="Search for issues in a project using JQL",
            inputSchema={
                "type": "object",
                "properties": {
                    "projectKey": {
                        "type": "string",
                        "description": 'Project key (e.g., "MRR")'
                    },
                    "jql": {
                        "type": "string",
                        "description": "JQL filter statement"
                    }
                },
                "required": ["projectKey", "jql"]
            }
        )

    async def execute(self, arguments: dict) -> List[TextContent]:
        project_key = arguments.get("projectKey")
        jql = arguments.get("jql")
        
        if not project_key or not jql:
            raise ValueError("projectKey and jql are required")
            
        full_jql = f"project = {project_key} AND {jql}"
        issues = self.jira.search_issues(
            full_jql,
            maxResults=30,
            fields="summary,description,status,priority,assignee,issuetype"
        )
        
        return [TextContent(
            type="text",
            text=str([{
                "key": issue.key,
                "summary": issue.fields.summary,
                "status": str(issue.fields.status),
                "priority": str(issue.fields.priority) if hasattr(issue.fields, 'priority') else None,
                "assignee": str(issue.fields.assignee) if hasattr(issue.fields, 'assignee') else None,
                "type": str(issue.fields.issuetype)
            } for issue in issues])
        )]