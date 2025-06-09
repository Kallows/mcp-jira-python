import unittest
import asyncio
import json
from unittest.mock import Mock
from mcp_jira_python.tools.create_issue_link import CreateIssueLinkTool

class TestCreateIssueLinkTool(unittest.TestCase):
    def setUp(self):
        self.tool = CreateIssueLinkTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira
        
        # Test data
        self.inward_issue = "TEST-123"
        self.outward_issue = "TEST-456"
        self.link_type = "Relates"

    def test_execute(self):
        """Test creating an issue link"""
        # Mock response
        self.mock_jira.create_issue_link.return_value = None  # create_issue_link doesn't return anything
        
        # Test input
        test_input = {
            "inwardIssueKey": self.inward_issue,
            "outwardIssueKey": self.outward_issue,
            "linkType": self.link_type
        }
        
        # Execute tool using asyncio.run
        result = asyncio.run(self.tool.execute(test_input))
        
        # Parse result JSON for proper comparison
        result_json = json.loads(result[0].text)
        
        # Verify result with case-insensitive comparison
        self.assertEqual(result[0].type, "text")
        self.assertEqual(result_json["inwardIssue"].upper(), self.inward_issue.upper())
        self.assertEqual(result_json["outwardIssue"].upper(), self.outward_issue.upper())
        self.assertEqual(result_json["linkType"].upper(), self.link_type.upper())
        
        # Verify JIRA API call
        self.mock_jira.create_issue_link.assert_called_once_with(
            type=self.link_type,
            inwardIssue=self.inward_issue,
            outwardIssue=self.outward_issue
        )