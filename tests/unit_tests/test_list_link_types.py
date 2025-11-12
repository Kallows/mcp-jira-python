import unittest
import asyncio
from unittest.mock import Mock
from mcp_jira_python.tools.list_link_types import ListLinkTypesTool

class TestListLinkTypesTool(unittest.TestCase):
    def setUp(self):
        self.tool = ListLinkTypesTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira

        # Mock link types
        self.mock_link_type1 = Mock()
        self.mock_link_type1.id = "1"
        self.mock_link_type1.name = "Blocks"
        self.mock_link_type1.inward = "is blocked by"
        self.mock_link_type1.outward = "blocks"

        self.mock_link_type2 = Mock()
        self.mock_link_type2.id = "2"
        self.mock_link_type2.name = "Relates"
        self.mock_link_type2.inward = "relates to"
        self.mock_link_type2.outward = "relates to"

        self.mock_link_type3 = Mock()
        self.mock_link_type3.id = "3"
        self.mock_link_type3.name = "Duplicates"
        self.mock_link_type3.inward = "is duplicated by"
        self.mock_link_type3.outward = "duplicates"

    def test_execute_success(self):
        """Test listing all link types"""
        # Setup mock
        self.mock_jira.issue_link_types.return_value = [
            self.mock_link_type1,
            self.mock_link_type2,
            self.mock_link_type3
        ]

        # Test input (no arguments required)
        test_input = {}

        # Execute
        result = asyncio.run(self.tool.execute(test_input))

        # Verify result
        self.assertEqual(result[0].type, "text")
        result_text = result[0].text

        # Verify all link types are in the result
        self.assertIn("Blocks", result_text)
        self.assertIn("blocks", result_text)
        self.assertIn("is blocked by", result_text)
        self.assertIn("Relates", result_text)
        self.assertIn("relates to", result_text)
        self.assertIn("Duplicates", result_text)
        self.assertIn("duplicates", result_text)
        self.assertIn("is duplicated by", result_text)

        # Verify JIRA API call
        self.mock_jira.issue_link_types.assert_called_once()

    def test_execute_empty_link_types(self):
        """Test listing link types when none are returned"""
        # Setup mock to return empty list
        self.mock_jira.issue_link_types.return_value = []

        # Test input
        test_input = {}

        # Execute
        result = asyncio.run(self.tool.execute(test_input))

        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn("[]", result[0].text)

        # Verify JIRA API call
        self.mock_jira.issue_link_types.assert_called_once()

    def test_execute_inward_outward_directions(self):
        """Test that inward and outward link directions are properly included"""
        # Setup mock with single link type
        self.mock_jira.issue_link_types.return_value = [self.mock_link_type1]

        # Test input
        test_input = {}

        # Execute
        result = asyncio.run(self.tool.execute(test_input))

        # Verify result contains both directions
        self.assertEqual(result[0].type, "text")
        result_text = result[0].text
        self.assertIn("inward", result_text.lower())
        self.assertIn("outward", result_text.lower())
        self.assertIn("is blocked by", result_text)
        self.assertIn("blocks", result_text)
