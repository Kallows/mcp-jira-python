import unittest
import asyncio
from unittest.mock import Mock, patch
from jira.exceptions import JIRAError
from mcp_jira_python.tools.delete_issue import DeleteIssueTool

class TestDeleteIssueTool(unittest.TestCase):
    def setUp(self):
        self.tool = DeleteIssueTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira
        
        # Test data
        self.test_issue_key = "TEST-123"
        
        # Mock issue
        self.mock_issue = Mock()
        self.mock_jira.issue.return_value = self.mock_issue

    def test_execute(self):
        """Test deleting an issue"""
        # Test input
        test_input = {
            "issueKey": self.test_issue_key
        }
        
        # Execute tool using asyncio.run
        result = asyncio.run(self.tool.execute(test_input))
        
        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn(self.test_issue_key, result[0].text)
        
        # Verify JIRA API calls
        self.mock_jira.issue.assert_called_once_with(self.test_issue_key)
        self.mock_issue.delete.assert_called_once()
        
    def test_execute_nonexistent_issue(self):
        """Test deleting a nonexistent issue"""
        # Mock JIRA to raise exception for nonexistent issue
        self.mock_jira.issue.side_effect = JIRAError(status_code=404)
        
        # Test input
        test_input = {
            "issueKey": self.test_issue_key
        }
        
        # Execute tool and verify exception
        with self.assertRaises(Exception):
            asyncio.run(self.tool.execute(test_input))