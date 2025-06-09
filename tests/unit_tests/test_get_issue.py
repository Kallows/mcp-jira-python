import unittest
import asyncio
from unittest.mock import Mock
from mcp_jira_python.tools.get_issue import GetIssueTool

class TestGetIssueTool(unittest.TestCase):
    def setUp(self):
        self.tool = GetIssueTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira
        
        # Test data
        self.test_issue_key = "TEST-123"
        
        # Mock issue
        self.mock_issue = Mock()
        self.mock_issue.key = self.test_issue_key
        self.mock_issue.fields = Mock()
        self.mock_issue.fields.summary = "Test Issue"
        self.mock_issue.fields.description = "Test Description"
        self.mock_issue.fields.status = Mock(name="Open")
        self.mock_issue.fields.priority = Mock(name="High")
        self.mock_issue.fields.assignee = Mock(displayName="Test Assignee")
        self.mock_issue.fields.issuetype = Mock(name="Bug")
        
        # Mock comments
        mock_comment = Mock()
        mock_comment.id = "10001"
        mock_comment.author = Mock(displayName="Test Author")
        mock_comment.body = "Test Comment"
        mock_comment.created = "2024-01-30T12:00:00.000+0000"
        self.mock_issue.fields.comment = Mock()
        self.mock_issue.fields.comment.comments = [mock_comment]
        
        # Mock attachments
        mock_attachment = Mock()
        mock_attachment.id = "20001"
        mock_attachment.filename = "test.txt"
        mock_attachment.size = 1024
        mock_attachment.created = "2024-01-30T12:00:00.000+0000"
        self.mock_issue.fields.attachment = [mock_attachment]

    def test_execute(self):
        """Test getting issue details"""
        # Setup mock response
        self.mock_jira.issue.return_value = self.mock_issue
        
        # Test input
        test_input = {
            "issueKey": self.test_issue_key
        }
        
        # Execute tool using asyncio.run
        result = asyncio.run(self.tool.execute(test_input))
        
        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn(self.test_issue_key, result[0].text)
        self.assertIn("Test Issue", result[0].text)
        self.assertIn("Test Description", result[0].text)
        self.assertIn("Test Comment", result[0].text)
        self.assertIn("test.txt", result[0].text)
        
        # Verify JIRA API call
        self.mock_jira.issue.assert_called_once_with(
            self.test_issue_key,
            expand='comments,attachments'
        )