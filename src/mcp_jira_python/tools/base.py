from abc import ABC, abstractmethod
from typing import List
from mcp.types import Tool, TextContent
from jira import JIRA

class BaseTool(ABC):
    def __init__(self):
        self.jira: JIRA = None
    
    @abstractmethod
    def get_tool_definition(self) -> Tool:
        """Return tool metadata."""
        pass
        
    @abstractmethod
    async def execute(self, arguments: dict) -> List[TextContent]:
        """Execute tool with given arguments."""
        pass