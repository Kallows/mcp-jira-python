import unittest
import asyncio
from unittest.mock import Mock
from mcp_jira_python.tools.search_issues import SearchIssuesTool

class TestSearchIssuesTool(unittest.TestCase):
    def setUp(self):
        self.tool = SearchIssuesTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira

        # Test data
        self.test_project_key = "TEST"
        self.test_issue_key = "TEST-123"
        
        # Mock issue for search results
        self.mock_issue = Mock()
        self.mock_issue.key = self.test_issue_key
        self.mock_issue.fields = Mock()
        self.mock_issue.fields.summary = "Test issue"
        self.mock_issue.fields.status = "Open"
        self.mock_issue.fields.priority = "High"
        self.mock_issue.fields.assignee = "testuser"
        self.mock_issue.fields.issuetype = "Bug"
        
    def test_execute_basic_search(self):
        """Test basic issue search"""
        # Mock search response
        self.mock_jira.search_issues.return_value = [self.mock_issue]
        
        # Test input
        test_input = {
            "projectKey": self.test_project_key,
            "jql": 'status = "Open"'
        }
        
        # Execute tool
        result = asyncio.run(self.tool.execute(test_input))
        
        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn(self.test_issue_key, result[0].text)
        self.assertIn("Open", result[0].text)
        
        # Verify JIRA API call
        expected_jql = f'project = {self.test_project_key} AND status = "Open"'
        self.mock_jira.search_issues.assert_called_once_with(
            expected_jql,
            maxResults=30,
            fields="summary,description,status,priority,assignee,issuetype"
        )

    def test_execute_complex_jql(self):
        """Test search with complex JQL"""
        # Mock search response
        self.mock_jira.search_issues.return_value = [self.mock_issue]
        
        # Test input with complex JQL
        test_input = {
            "projectKey": self.test_project_key,
            "jql": 'status = "Open" AND assignee = currentUser() AND updated >= "-1w"'
        }
        
        # Execute tool
        result = asyncio.run(self.tool.execute(test_input))
        
        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn(self.test_issue_key, result[0].text)
        
        # Verify complex JQL
        expected_jql = (
            f'project = {self.test_project_key} AND '
            'status = "Open" AND assignee = currentUser() AND updated >= "-1w"'
        )
        self.mock_jira.search_issues.assert_called_once_with(
            expected_jql,
            maxResults=30,
            fields="summary,description,status,priority,assignee,issuetype"
        )