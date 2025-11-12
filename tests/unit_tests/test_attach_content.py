import unittest
import asyncio
import base64
from unittest.mock import Mock
from mcp_jira_python.tools.attach_content import AttachContentTool

class TestAttachContentTool(unittest.TestCase):
    def setUp(self):
        self.tool = AttachContentTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira

        # Test data
        self.test_issue_key = "TEST-123"
        self.test_filename = "test.txt"
        self.test_content = "Test file content"

    def test_execute_text_content(self):
        """Test attaching text content to an issue"""
        # Setup mock
        self.mock_jira.add_attachment.return_value = None

        # Test input
        test_input = {
            "issueKey": self.test_issue_key,
            "filename": self.test_filename,
            "content": self.test_content,
            "encoding": "none"
        }

        # Execute
        result = asyncio.run(self.tool.execute(test_input))

        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn("Content attached successfully", result[0].text)
        self.assertIn(self.test_filename, result[0].text)

        # Verify JIRA API call
        self.mock_jira.add_attachment.assert_called_once()
        call_args = self.mock_jira.add_attachment.call_args
        self.assertEqual(call_args[0][0], self.test_issue_key)
        self.assertEqual(call_args[1]["filename"], self.test_filename)

    def test_execute_base64_content(self):
        """Test attaching base64 encoded content"""
        # Setup mock
        self.mock_jira.add_attachment.return_value = None

        # Encode content as base64
        encoded_content = base64.b64encode(self.test_content.encode('utf-8')).decode('utf-8')

        # Test input
        test_input = {
            "issueKey": self.test_issue_key,
            "filename": self.test_filename,
            "content": encoded_content,
            "encoding": "base64"
        }

        # Execute
        result = asyncio.run(self.tool.execute(test_input))

        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn("Content attached successfully", result[0].text)

        # Verify JIRA API call
        self.mock_jira.add_attachment.assert_called_once()

    def test_execute_missing_required_fields(self):
        """Test error handling for missing required fields"""
        test_input = {
            "issueKey": self.test_issue_key,
            "filename": self.test_filename
            # Missing content
        }

        with self.assertRaises(ValueError) as context:
            asyncio.run(self.tool.execute(test_input))

        self.assertIn("required", str(context.exception).lower())

    def test_execute_invalid_base64(self):
        """Test error handling for invalid base64 content"""
        # Setup mock
        self.mock_jira.add_attachment.return_value = None

        # Test input with invalid base64
        test_input = {
            "issueKey": self.test_issue_key,
            "filename": self.test_filename,
            "content": "not-valid-base64!!!",
            "encoding": "base64"
        }

        # ValueError gets wrapped in Exception by the tool
        with self.assertRaises(Exception) as context:
            asyncio.run(self.tool.execute(test_input))

        self.assertIn("base64", str(context.exception).lower())
