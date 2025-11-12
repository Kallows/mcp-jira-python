import unittest
import asyncio
from unittest.mock import Mock
from mcp_jira_python.tools.list_fields import ListFieldsTool

class TestListFieldsTool(unittest.TestCase):
    def setUp(self):
        self.tool = ListFieldsTool()
        self.mock_jira = Mock()
        self.tool.jira = self.mock_jira

        # Mock fields data
        self.mock_fields = [
            {
                "id": "summary",
                "name": "Summary",
                "custom": False,
                "schema": {"type": "string"}
            },
            {
                "id": "description",
                "name": "Description",
                "custom": False,
                "schema": {"type": "string"}
            },
            {
                "id": "customfield_10001",
                "name": "Custom Field",
                "custom": True,
                "schema": {"type": "string"}
            }
        ]

    def test_execute_success(self):
        """Test listing all JIRA fields"""
        # Setup mock
        self.mock_jira.fields.return_value = self.mock_fields

        # Test input (no arguments required)
        test_input = {}

        # Execute
        result = asyncio.run(self.tool.execute(test_input))

        # Verify result
        self.assertEqual(result[0].type, "text")
        result_text = result[0].text

        # Verify all fields are in the result
        self.assertIn("summary", result_text)
        self.assertIn("Summary", result_text)
        self.assertIn("description", result_text)
        self.assertIn("Description", result_text)
        self.assertIn("customfield_10001", result_text)
        self.assertIn("Custom Field", result_text)

        # Verify JIRA API call
        self.mock_jira.fields.assert_called_once()

    def test_execute_empty_fields(self):
        """Test listing fields when none are returned"""
        # Setup mock to return empty list
        self.mock_jira.fields.return_value = []

        # Test input
        test_input = {}

        # Execute
        result = asyncio.run(self.tool.execute(test_input))

        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn("[]", result[0].text)

        # Verify JIRA API call
        self.mock_jira.fields.assert_called_once()

    def test_execute_fields_without_schema(self):
        """Test handling fields without schema"""
        # Mock fields without schema
        fields_no_schema = [
            {
                "id": "field1",
                "name": "Field 1",
                "custom": False
            }
        ]
        self.mock_jira.fields.return_value = fields_no_schema

        # Test input
        test_input = {}

        # Execute - should not raise an error
        result = asyncio.run(self.tool.execute(test_input))

        # Verify result
        self.assertEqual(result[0].type, "text")
        self.assertIn("field1", result[0].text)
        self.assertIn("Field 1", result[0].text)
