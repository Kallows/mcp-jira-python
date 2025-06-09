import unittest
import base64
import asyncio
from unittest.mock import Mock
from mcp_jira_python.tools.add_comment_with_attachment import AddCommentWithAttachmentTool

class TestAddCommentWithAttachmentTool(unittest.TestCase):
    def setUp(self):
        self.tool = AddCommentWithAttachmentTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira
        
        # Test data
        self.test_issue_key = "TEST-123"
        self.test_comment = "Test comment with attachment"
        self.test_file_content = b"Test file content"
        self.test_file_name = "test.txt"
        
        # Mock attachment
        self.mock_attachment = Mock()
        self.mock_attachment.id = "67890"
        self.mock_attachment.filename = self.test_file_name
        
        # Mock comment
        self.mock_comment = Mock()
        self.mock_comment.id = "12345"
        self.mock_comment.body = self.test_comment

    def test_execute_success(self):
        """Test adding a comment with attachment successfully"""
        # Setup mock responses
        self.mock_jira.add_attachment.return_value = [self.mock_attachment]
        self.mock_jira.add_comment.return_value = self.mock_comment
        
        # Test input with base64 encoded file content
        test_input = {
            "issueKey": self.test_issue_key,
            "comment": self.test_comment,
            "attachment": {
                "filename": self.test_file_name,
                "content": base64.b64encode(self.test_file_content).decode(),
                "mimeType": "text/plain"
            }
        }
        
        # Execute tool using asyncio.run
        result = asyncio.run(self.tool.execute(test_input))
        
        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn("12345", result[0].text)  # Comment ID
        self.assertIn(self.test_file_name, result[0].text)  # File name should be in result
        
        # Verify JIRA API calls
        self.mock_jira.add_attachment.assert_called_once()
        self.mock_jira.add_comment.assert_called_with(
            self.test_issue_key,
            self.test_comment
        )