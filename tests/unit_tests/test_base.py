import unittest
from unittest.mock import Mock, patch
from mcp_jira_python.tools.base import BaseTool

class MockBaseTool(BaseTool):
    """Mock implementation of BaseTool for testing"""
    async def execute(self, arguments):
        return {"status": "success"}

    def get_tool_definition(self):
        return {
            "name": "mock_tool",
            "description": "Mock tool for testing"
        }

class TestBaseTool(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.tool = MockBaseTool()  # Use MockBaseTool instead of BaseTool
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira
        
    # Rest of the test cases remain the same...
