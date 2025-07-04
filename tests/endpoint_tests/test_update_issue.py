import unittest
import os
import sys
import asyncio
from datetime import datetime
from jira.client import JIRA
import dotenv

# Add the src directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from mcp_jira_python.tools.update_issue import UpdateIssueTool

class TestUpdateIssueIntegration(unittest.TestCase):
    """Integration test for UpdateIssueTool"""
    
    def setUp(self):
        """Set up test environment"""
        # Load environment variables
        dotenv.load_dotenv(os.path.join(project_root, '.env'))
        
        # Get required environment variables
        required_vars = ["JIRA_HOST", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Initialize JIRA client for test setup/teardown
        self.jira = JIRA(
            server=f"https://{os.getenv('JIRA_HOST')}",
            basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
        )
        
        self.project_key = os.getenv("JIRA_PROJECT_KEY")
        self.test_issue_key = None
        
        # Create a test issue
        issue_dict = {
            'project': {'key': self.project_key},
            'summary': 'Test Issue for Update Tests',
            'description': 'This is a test issue for update_issue integration tests',
            'issuetype': {'name': 'Task'}
        }
        self.test_issue = self.jira.create_issue(fields=issue_dict)
        self.test_issue_key = self.test_issue.key

    def tearDown(self):
        """Clean up test issue"""
        if self.test_issue_key:
            try:
                issue = self.jira.issue(self.test_issue_key)
                issue.delete()
            except Exception as e:
                print(f"Warning: Failed to delete test issue {self.test_issue_key}: {str(e)}")

    def test_update_issue(self):
        """Test updating an issue"""
        # Initialize the tool
        update_tool = UpdateIssueTool()
        update_tool.jira = self.jira
        
        # Run the tool asynchronously
        test_input = {
            "issueKey": self.test_issue_key,
            "summary": "Updated Test Issue",
            "description": "Updated test description"
        }
        
        # Run async code
        result = asyncio.run(update_tool.execute(test_input))
        
        # Verify response indicates success
        self.assertEqual(result[0].type, "text")
        response_text = result[0].text.lower()
        self.assertTrue("updated" in response_text and "success" in response_text)
        
        # Verify issue was actually updated
        updated_issue = self.jira.issue(self.test_issue_key)
        self.assertEqual(updated_issue.fields.summary, "Updated Test Issue")
        self.assertEqual(updated_issue.fields.description, "Updated test description")

    def test_update_nonexistent_issue(self):
        """Test attempting to update a non-existent issue"""
        # Initialize the tool
        update_tool = UpdateIssueTool()
        update_tool.jira = self.jira
        
        # Run the tool asynchronously
        test_input = {
            "issueKey": "NONEXISTENT-123",
            "summary": "This should fail",
            "description": "This update should fail"
        }
        
        try:
            asyncio.run(update_tool.execute(test_input))
            self.fail("Expected an error for non-existent issue")
        except Exception as e:
            self.assertTrue("Issue does not exist" in str(e) or "404" in str(e))

if __name__ == '__main__':
    unittest.main()