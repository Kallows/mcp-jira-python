import unittest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch
from mcp_jira_python.tools.attach_file import AttachFileTool

class TestAttachFileTool(unittest.TestCase):
    def setUp(self):
        self.tool = AttachFileTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira

        # Test data
        self.test_issue_key = "TEST-123"
        self.test_filename = "test.txt"

    def test_execute_success(self):
        """Test attaching a file to an issue"""
        # Setup mock
        self.mock_jira.add_attachment.return_value = None

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write("Test file content")
            tmp_path = tmp.name

        try:
            # Test input
            test_input = {
                "issueKey": self.test_issue_key,
                "filename": self.test_filename,
                "filepath": tmp_path
            }

            # Execute
            result = asyncio.run(self.tool.execute(test_input))

            # Verify result
            self.assertEqual(result[0].type, "text")
            self.assertIn("File attached successfully", result[0].text)
            self.assertIn(self.test_filename, result[0].text)

            # Verify JIRA API call
            self.mock_jira.add_attachment.assert_called_once_with(
                self.test_issue_key,
                tmp_path,
                filename=self.test_filename
            )
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_execute_missing_required_fields(self):
        """Test error handling for missing required fields"""
        test_input = {
            "issueKey": self.test_issue_key,
            "filename": self.test_filename
            # Missing filepath
        }

        with self.assertRaises(ValueError) as context:
            asyncio.run(self.tool.execute(test_input))

        self.assertIn("required", str(context.exception).lower())

    def test_execute_file_not_found(self):
        """Test error handling for non-existent file"""
        test_input = {
            "issueKey": self.test_issue_key,
            "filename": self.test_filename,
            "filepath": "/nonexistent/file.txt"
        }

        # ValueError gets wrapped in Exception by the tool
        with self.assertRaises(Exception) as context:
            asyncio.run(self.tool.execute(test_input))

        self.assertIn("not found", str(context.exception).lower())

    @patch('os.path.getsize')
    def test_execute_file_too_large(self, mock_getsize):
        """Test error handling for files exceeding size limit"""
        # Mock getsize to return a large value
        mock_getsize.return_value = 11 * 1024 * 1024  # 11MB

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write("small content")
            tmp_path = tmp.name

        try:
            test_input = {
                "issueKey": self.test_issue_key,
                "filename": self.test_filename,
                "filepath": tmp_path
            }

            # ValueError gets wrapped in Exception by the tool
            with self.assertRaises(Exception) as context:
                asyncio.run(self.tool.execute(test_input))

            self.assertIn("too large", str(context.exception).lower())
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
