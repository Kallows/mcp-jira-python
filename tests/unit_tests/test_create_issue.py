import unittest
import asyncio
from unittest.mock import Mock
from mcp_jira_python.tools.create_issue import CreateIssueTool

class TestCreateIssueTool(unittest.TestCase):
    def setUp(self):
        self.tool = CreateIssueTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira
        
        # Test data
        self.test_project_key = "TEST"
        self.test_issue_key = "TEST-123"
        self.test_summary = "Test issue"
        self.test_description = "Test description"
        
        # Mock issue response
        self.mock_issue = Mock()
        self.mock_issue.key = self.test_issue_key

    def test_execute(self):
        """Test creating a new Jira issue"""
        # Setup mock response
        self.mock_jira.create_issue.return_value = self.mock_issue
        
        # Test input
        test_input = {
            "projectKey": self.test_project_key,
            "summary": self.test_summary,
            "description": self.test_description,
            "issueType": "Task"
        }
        
        # Execute tool using asyncio.run
        result = asyncio.run(self.tool.execute(test_input))
        
        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn(self.test_issue_key, result[0].text)
        
        # Verify JIRA API call - now with correct field structure
        expected_fields = {
            'project': {'key': self.test_project_key},
            'summary': self.test_summary,
            'description': self.test_description,
            'issuetype': {'name': 'Task'}
        }
        self.mock_jira.create_issue.assert_called_once_with(fields=expected_fields)