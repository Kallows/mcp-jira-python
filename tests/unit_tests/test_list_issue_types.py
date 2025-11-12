import unittest
import asyncio
from unittest.mock import Mock
from mcp_jira_python.tools.list_issue_types import ListIssueTypesTool

class TestListIssueTypesTool(unittest.TestCase):
    def setUp(self):
        self.tool = ListIssueTypesTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira

        # Mock issue types
        self.mock_issue_type1 = Mock()
        self.mock_issue_type1.id = "1"
        self.mock_issue_type1.name = "Bug"
        self.mock_issue_type1.description = "A problem which impairs functionality"
        self.mock_issue_type1.subtask = False

        self.mock_issue_type2 = Mock()
        self.mock_issue_type2.id = "2"
        self.mock_issue_type2.name = "Task"
        self.mock_issue_type2.description = "A task that needs to be done"
        self.mock_issue_type2.subtask = False

        self.mock_issue_type3 = Mock()
        self.mock_issue_type3.id = "3"
        self.mock_issue_type3.name = "Sub-task"
        self.mock_issue_type3.description = "A subtask of another issue"
        self.mock_issue_type3.subtask = True

    def test_execute_success(self):
        """Test listing all issue types"""
        # Setup mock
        self.mock_jira.issue_types.return_value = [
            self.mock_issue_type1,
            self.mock_issue_type2,
            self.mock_issue_type3
        ]

        # Test input (no arguments required)
        test_input = {}

        # Execute
        result = asyncio.run(self.tool.execute(test_input))

        # Verify result
        self.assertEqual(result[0].type, "text")
        result_text = result[0].text

        # Verify all issue types are in the result
        self.assertIn("Bug", result_text)
        self.assertIn("Task", result_text)
        self.assertIn("Sub-task", result_text)
        self.assertIn("problem which impairs", result_text)

        # Verify JIRA API call
        self.mock_jira.issue_types.assert_called_once()

    def test_execute_empty_issue_types(self):
        """Test listing issue types when none are returned"""
        # Setup mock to return empty list
        self.mock_jira.issue_types.return_value = []

        # Test input
        test_input = {}

        # Execute
        result = asyncio.run(self.tool.execute(test_input))

        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn("[]", result[0].text)

        # Verify JIRA API call
        self.mock_jira.issue_types.assert_called_once()

    def test_execute_subtask_flag(self):
        """Test that subtask flag is properly included in result"""
        # Setup mock with only subtask type
        self.mock_jira.issue_types.return_value = [self.mock_issue_type3]

        # Test input
        test_input = {}

        # Execute
        result = asyncio.run(self.tool.execute(test_input))

        # Verify result contains subtask info
        self.assertEqual(result[0].type, "text")
        result_text = result[0].text
        self.assertIn("subtask", result_text.lower())
        self.assertIn("True", result_text)
