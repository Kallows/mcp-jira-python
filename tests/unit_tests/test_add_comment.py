import asyncio
import unittest
from unittest.mock import Mock, patch
from mcp_jira_python.tools.add_comment import AddCommentTool

class TestAddCommentTool(unittest.TestCase):
    def setUp(self):
        self.tool = AddCommentTool()
        # Create mock JIRA instance
        self.mock_jira = Mock()
        # Directly set the mocked JIRA instance
        self.tool.jira = self.mock_jira
        
        # Test data
        self.test_issue_key = "TEST-123"
        
    def test_execute(self):
        """Test adding a comment to an issue"""
        # Mock response
        mock_comment = Mock()
        mock_comment.id = "12345"
        mock_comment.body = "Test comment"
        self.mock_jira.add_comment.return_value = mock_comment
        
        # Test input
        test_input = {
            "issueKey": self.test_issue_key,
            "comment": "Test comment"
        }
        
        # Execute tool using asyncio.run to handle the coroutine
        result = asyncio.run(self.tool.execute(test_input))
        
        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn("12345", result[0].text)
        
        # Verify JIRA API call
        self.mock_jira.add_comment.assert_called_with(
            self.test_issue_key,
            "Test comment"
        )