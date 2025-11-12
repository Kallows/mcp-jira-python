import unittest
import asyncio
import tempfile
import os
from unittest.mock import Mock, MagicMock
from mcp_jira_python.tools.get_issue_attachment import GetIssueAttachmentTool

class TestGetIssueAttachmentTool(unittest.TestCase):
    def setUp(self):
        self.tool = GetIssueAttachmentTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira

        # Test data
        self.test_issue_key = "TEST-123"
        self.test_attachment_id = "12345"
        self.test_filename = "test.txt"
        self.test_content = b"Test file content"

        # Mock attachment
        self.mock_attachment = Mock()
        self.mock_attachment.id = self.test_attachment_id
        self.mock_attachment.filename = self.test_filename
        self.mock_attachment.size = len(self.test_content)
        self.mock_attachment.get.return_value = self.test_content

    def test_execute_by_attachment_id(self):
        """Test downloading attachment by attachment ID"""
        # Setup mock
        self.mock_jira.attachment.return_value = self.mock_attachment

        # Create temporary output directory
        with tempfile.TemporaryDirectory() as tmpdir:
            test_input = {
                "issueKey": self.test_issue_key,
                "attachmentId": self.test_attachment_id,
                "outputPath": tmpdir
            }

            # Execute
            result = asyncio.run(self.tool.execute(test_input))

            # Verify result
            self.assertEqual(result[0].type, "text")
            self.assertIn("downloaded successfully", result[0].text.lower())
            self.assertIn(self.test_filename, result[0].text)

            # Verify JIRA API call
            self.mock_jira.attachment.assert_called_once_with(self.test_attachment_id)

            # Verify file was written
            expected_path = os.path.join(tmpdir, self.test_filename)
            self.assertTrue(os.path.exists(expected_path))

    def test_execute_by_filename(self):
        """Test downloading attachment by filename"""
        # Setup mock issue
        mock_issue = Mock()
        mock_issue.fields.attachment = [self.mock_attachment]
        self.mock_jira.issue.return_value = mock_issue

        # Create temporary output directory
        with tempfile.TemporaryDirectory() as tmpdir:
            test_input = {
                "issueKey": self.test_issue_key,
                "filename": self.test_filename,
                "outputPath": tmpdir
            }

            # Execute
            result = asyncio.run(self.tool.execute(test_input))

            # Verify result
            self.assertEqual(result[0].type, "text")
            self.assertIn("downloaded successfully", result[0].text.lower())
            self.assertIn(self.test_filename, result[0].text)

            # Verify JIRA API call
            self.mock_jira.issue.assert_called_once()

    def test_execute_download_all(self):
        """Test downloading all attachments when no specific attachment is specified"""
        # Setup multiple mock attachments
        mock_attachment2 = Mock()
        mock_attachment2.id = "67890"
        mock_attachment2.filename = "test2.txt"
        mock_attachment2.size = 100
        mock_attachment2.get.return_value = b"Second file content"

        mock_issue = Mock()
        mock_issue.fields.attachment = [self.mock_attachment, mock_attachment2]
        self.mock_jira.issue.return_value = mock_issue

        # Create temporary output directory
        with tempfile.TemporaryDirectory() as tmpdir:
            test_input = {
                "issueKey": self.test_issue_key,
                "outputPath": tmpdir
            }

            # Execute
            result = asyncio.run(self.tool.execute(test_input))

            # Verify result
            self.assertEqual(result[0].type, "text")
            self.assertIn("2", result[0].text)
            self.assertIn("attachments", result[0].text.lower())

            # Verify both files were written
            self.assertTrue(os.path.exists(os.path.join(tmpdir, self.test_filename)))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "test2.txt")))

    def test_execute_missing_issue_key(self):
        """Test error handling for missing issue key"""
        test_input = {
            "attachmentId": self.test_attachment_id
            # Missing issueKey
        }

        with self.assertRaises(ValueError) as context:
            asyncio.run(self.tool.execute(test_input))

        self.assertIn("required", str(context.exception).lower())

    def test_execute_no_attachments_found(self):
        """Test error handling when issue has no attachments"""
        # Setup mock issue with no attachments
        mock_issue = Mock()
        mock_issue.fields.attachment = []
        self.mock_jira.issue.return_value = mock_issue

        with tempfile.TemporaryDirectory() as tmpdir:
            test_input = {
                "issueKey": self.test_issue_key,
                "filename": self.test_filename,
                "outputPath": tmpdir
            }

            # ValueError gets wrapped in Exception by the tool
            with self.assertRaises(Exception) as context:
                asyncio.run(self.tool.execute(test_input))

            self.assertIn("no attachments", str(context.exception).lower())

    def test_execute_filename_not_found(self):
        """Test error handling when specified filename is not found"""
        # Setup mock issue with different attachment
        other_attachment = Mock()
        other_attachment.filename = "other.txt"
        other_attachment.size = 100
        other_attachment.get.return_value = b"other content"

        mock_issue = Mock()
        mock_issue.fields.attachment = [other_attachment]
        self.mock_jira.issue.return_value = mock_issue

        with tempfile.TemporaryDirectory() as tmpdir:
            test_input = {
                "issueKey": self.test_issue_key,
                "filename": self.test_filename,
                "outputPath": tmpdir
            }

            # ValueError gets wrapped in Exception by the tool
            with self.assertRaises(Exception) as context:
                asyncio.run(self.tool.execute(test_input))

            self.assertIn("not found", str(context.exception).lower())
