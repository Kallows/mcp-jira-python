import unittest
import asyncio
from unittest.mock import Mock
from mcp_jira_python.tools.update_issue import UpdateIssueTool

class TestUpdateIssueTool(unittest.TestCase):
    def setUp(self):
        self.tool = UpdateIssueTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira
        
        # Test data
        self.test_issue_key = "TEST-123"
        self.test_summary = "Updated Test Issue"
        self.test_description = "Updated Test Description"
        
        # Mock issue
        self.mock_issue = Mock()
        self.mock_issue.key = self.test_issue_key
        self.mock_issue.update.return_value = None  # update doesn't return anything
        self.mock_jira.issue.return_value = self.mock_issue

    def test_execute(self):
        """Test updating an issue"""
        # Test input - note: fields are at root level
        test_input = {
            "issueKey": self.test_issue_key,
            "summary": self.test_summary,
            "description": self.test_description
        }
        
        # Execute tool using asyncio.run
        result = asyncio.run(self.tool.execute(test_input))
        
        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn(self.test_issue_key, result[0].text)
        self.assertIn("successfully", result[0].text.lower())
        
        # Verify JIRA API calls
        self.mock_jira.issue.assert_called_once_with(self.test_issue_key)
        self.mock_issue.update.assert_called_once_with(fields={
            "summary": self.test_summary,
            "description": self.test_description
        })