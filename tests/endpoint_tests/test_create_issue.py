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

from mcp_jira_python.tools.create_issue import CreateIssueTool

class TestCreateIssueIntegration(unittest.TestCase):
    """Integration test for CreateIssueTool"""
    
    def setUp(self):
        """Set up test environment"""
        # Load environment variables
        dotenv.load_dotenv(os.path.join(project_root, '.env'))
        
        # Get required environment variables
        required_vars = ["JIRA_HOST", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Create tool and initialize Jira client
        self.tool = CreateIssueTool()
        self.tool.jira = JIRA(
            server=f"https://{os.getenv('JIRA_HOST')}",
            basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
        )
        
        self.test_project_key = os.getenv("JIRA_PROJECT_KEY")
        # Generate unique issue prefix for this test run
        self.issue_prefix = f"IT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.created_issue_key = None

    def tearDown(self):
        """Clean up any created issues"""
        if self.created_issue_key:
            try:
                # Updated to use issue().delete() instead of delete_issue()
                issue = self.tool.jira.issue(self.created_issue_key)
                issue.delete()
            except Exception as e:
                print(f"Warning: Failed to delete test issue {self.created_issue_key}: {str(e)}")

    async def _async_test(self):
        """Async part of the test"""
        test_input = {
            "projectKey": self.test_project_key,
            "summary": f"{self.issue_prefix}_Integration_Test_Issue",
            "description": "Test issue created by integration tests",
            "issueType": "Task"
        }
        
        result = await self.tool.execute(test_input)
        return result

    def test_create_issue(self):
        """Test creating a new Jira issue"""
        # Run the async test using asyncio
        result = asyncio.run(self._async_test())
        
        # Verify response format
        self.assertEqual(result[0].type, "text")
        # Extract and store created issue key for cleanup
        response_dict = eval(result[0].text)  # Safe since we control the input
        self.created_issue_key = response_dict['key']
        
        # Verify issue was actually created
        issue = self.tool.jira.issue(self.created_issue_key)
        self.assertEqual(issue.fields.summary, f"{self.issue_prefix}_Integration_Test_Issue")
        self.assertEqual(issue.fields.description, "Test issue created by integration tests")
        self.assertEqual(issue.fields.issuetype.name, "Task")
        self.assertEqual(issue.fields.project.key, self.test_project_key)

if __name__ == '__main__':
    unittest.main()