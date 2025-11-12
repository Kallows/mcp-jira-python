import unittest
import asyncio
from unittest.mock import Mock
from mcp_jira_python.tools.get_user import GetUserTool

class TestGetUserTool(unittest.TestCase):
    def setUp(self):
        self.tool = GetUserTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira

        # Test data
        self.test_email = "test@example.com"

        # Mock user
        self.mock_user = Mock()
        self.mock_user.accountId = "abc123"
        self.mock_user.displayName = "Test User"
        self.mock_user.emailAddress = self.test_email
        self.mock_user.active = True

    def test_execute_success(self):
        """Test getting user by email address"""
        # Setup mock
        self.mock_jira.search_users.return_value = [self.mock_user]

        # Test input
        test_input = {
            "email": self.test_email
        }

        # Execute
        result = asyncio.run(self.tool.execute(test_input))

        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn(self.mock_user.accountId, result[0].text)
        self.assertIn(self.mock_user.displayName, result[0].text)
        self.assertIn(self.test_email, result[0].text)

        # Verify JIRA API call
        self.mock_jira.search_users.assert_called_once_with(query=self.test_email)

    def test_execute_missing_email(self):
        """Test error handling for missing email"""
        test_input = {}

        with self.assertRaises(ValueError) as context:
            asyncio.run(self.tool.execute(test_input))

        self.assertIn("required", str(context.exception).lower())

    def test_execute_user_not_found(self):
        """Test error handling when user is not found"""
        # Setup mock to return empty list
        self.mock_jira.search_users.return_value = []

        test_input = {
            "email": "nonexistent@example.com"
        }

        with self.assertRaises(ValueError) as context:
            asyncio.run(self.tool.execute(test_input))

        self.assertIn("no user found", str(context.exception).lower())
