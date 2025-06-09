import unittest
import asyncio
import os
import json
import base64
import warnings
import sys
import tracemalloc
import datetime
import time
from io import StringIO
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class TestOutputCapture:
    """Helper class to capture test output"""
    def __init__(self):
        self.output = StringIO()
    
    def __enter__(self):
        sys.stdout = self.output
        return self.output
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = sys.__stdout__

class _JsonTestResult(unittest.TextTestResult):
    """Custom test result class that captures detailed test information"""
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = {}
        self.current_test_start = None

    def startTest(self, test):
        self.current_test_start = time.time()
        super().startTest(test)

    def addSuccess(self, test):
        super().addSuccess(test)
        self._store_result(test, "PASS")
        
    def addError(self, test, err):
        super().addError(test, err)
        self._store_result(test, "ERROR", err)
        
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._store_result(test, "FAIL", err)

    def _store_result(self, test, status, error=None):
        test_name = test._testMethodName
        test_method = getattr(test, test_name)
        duration = time.time() - self.current_test_start
        
        self.test_results[test_name] = {
            'description': test_method.__doc__ or '',
            'status': status,
            'output': getattr(test, 'output', ''),
            'duration': duration,
            'error': self._exc_info_to_string(error, test) if error else None
        }

class JsonTestRunner(unittest.TextTestRunner):
    """Custom test runner that uses JsonTestResult"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _makeResult(self):
        return _JsonTestResult(self.stream, self.descriptions, self.verbosity)

class TestJiraMCPIntegration(unittest.TestCase):
    """Test Jira operations through the MCP interface"""
    available_tools = []  # Class variable to store tools

    @classmethod
    def setUpClass(cls):
        cls.server_script = os.getenv("MCP_SERVER_SCRIPT", "../src/mcp_jira_python/server.py")
        cls.command = "python" if cls.server_script.endswith(".py") else "node"
        cls.project_key = "TEST"
        cls.test_user_email = os.getenv("JIRA_EMAIL")

    def setUp(self):
        """Set up test environment for each test"""
        self.output = ''
        self.output_capture = TestOutputCapture()
        self.output_capture.__enter__()
        self.issue_key = None

    def tearDown(self):
        """Clean up after each test"""
        self.output = self.output_capture.output.getvalue()
        self.output_capture.__exit__(None, None, None)
        
        # Delete test issue if it exists
        if self.issue_key:
            self.run_async_test(self.delete_test_issue(self.issue_key))

    async def setup_session(self):
        """Set up the MCP client session."""
        self.exit_stack = AsyncExitStack()
        server_params = StdioServerParameters(
            command=self.command,
            args=[self.server_script],
            env=dict(os.environ),
        )
        self.stdio, self.write = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()

    async def teardown_session(self):
        """Tear down the MCP client session."""
        await self.exit_stack.aclose()

    def run_async_test(self, coroutine):
        """Helper to run async tests."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(coroutine)
            return result
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    async def setup_session(self):
        """Set up the MCP client session."""
        self.exit_stack = AsyncExitStack()
        server_params = StdioServerParameters(
            command=self.command,
            args=[self.server_script],
            env=dict(os.environ),
        )
        self.stdio, self.write = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()

        # Get and store available tools after initialization
        tools_response = await self.session.list_tools()
        self.__class__.available_tools = [tool.name for tool in tools_response.tools]

    async def delete_test_issue(self, issue_key):
        """Helper to delete a test issue."""
        try:
            await self.setup_session()
            await self.call_tool("delete_issue", {"issueKey": issue_key})
        finally:
            await self.teardown_session()

    async def call_tool(self, tool_name, arguments):
        """Call an MCP tool and return its parsed response."""
        response = await self.session.call_tool(tool_name, arguments)
        
        # Get the TextContent from the response
        if isinstance(response.content, list):
            if not response.content:
                return []
            content = response.content[0]
        else:
            content = response.content
        
        # Check for error response before parsing
        if hasattr(content, 'isError') and content.isError:
            raise Exception(content.text)
        
        # Get the text from TextContent
        if hasattr(content, 'text'):
            text = content.text
            
            if not isinstance(text, str):
                return text
                
            # Try JSON-style (double quotes) first
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                # Try Python-style (single quotes)
                try:
                    import ast
                    return ast.literal_eval(text)
                except (SyntaxError, ValueError):
                    # If text starts with '[', it might be a string representation of a list
                    if text.strip().startswith('['):
                        try:
                            return ast.literal_eval(text)
                        except (SyntaxError, ValueError):
                            return text
                    return text
                    
        return content

    def test_0_create_jira_issue(self):
        """Test creating a new Jira issue"""
        async def test_create():
            await self.setup_session()
            try:
                result = await self.call_tool(
                    "create_jira_issue",
                    {
                        "projectKey": self.project_key,
                        "summary": "Test Issue Created via MCP",
                        "description": "This is a test issue created by the MCP integration tests",
                        "issueType": "Task",
                        "priority": "Medium",
                        "assignee": self.test_user_email
                    }
                )
                
                # print("\n=== RESPONSE HANDLING ===")
                # print(f"Result: {result}")
                # print(f"Result type: {type(result)}")
                
                if isinstance(result, str) and result.startswith('{'):
                    # print("Converting string result to dict")
                    try:
                        result = json.loads(result.replace("'", '"'))
                    except json.JSONDecodeError:
                        import ast
                        result = ast.literal_eval(result)
                
                if isinstance(result, dict):
                    # print("Extracting key from dict")
                    self.issue_key = result.get('key')
                    # print(f"Extracted key: {self.issue_key}")
                # else:
                #     print(f"Result is not a dict: {type(result)}")
                
                # print("=== END RESPONSE HANDLING ===\n")
                
                self.assertIsNotNone(self.issue_key, f"No issue key in response. Response was: {result}")
                print(f"Successfully created new issue: {self.issue_key}")
                
            finally:
                await self.teardown_session()

        self.run_async_test(test_create())

    def test_1_add_comment(self):
        """Test adding a comment to an issue"""
        async def test_comment():
            await self.setup_session()
            try:
                # Create test issue
                issue_result = await self.call_tool(
                    "create_jira_issue",
                    {
                        "projectKey": self.project_key,
                        "summary": "Test Issue for Comments",
                        "description": "This is a test issue for comment testing",
                        "issueType": "Task"
                    }
                )
                self.issue_key = issue_result["key"]

                # Add comment
                comment_result = await self.call_tool(
                    "add_comment",
                    {
                        "issueKey": self.issue_key,
                        "comment": "Test comment from MCP integration tests"
                    }
                )
                self.assertTrue("id" in comment_result)
                print(f"Successfully added comment to {self.issue_key}")
            finally:
                await self.teardown_session()

        self.run_async_test(test_comment())

    def test_2_add_comment_with_attachment(self):
        """Test adding a comment with an attachment"""
        async def test_attachment():
            await self.setup_session()
            try:
                # Create test issue
                issue_result = await self.call_tool(
                    "create_jira_issue",
                    {
                        "projectKey": self.project_key,
                        "summary": "Test Issue for Attachments",
                        "description": "This is a test issue for attachment testing",
                        "issueType": "Task"
                    }
                )
                
                print(f"Created issue result: {issue_result}")
                self.issue_key = issue_result.get('key')

                # Create test content
                test_content = "This is a test file content"
                test_content_b64 = base64.b64encode(test_content.encode()).decode()

                # Add comment with attachment
                result = await self.call_tool(
                    "add_comment_with_attachment",
                    {
                        "issueKey": self.issue_key,
                        "comment": "Test comment with attachment",
                        "attachment": {
                            "filename": "test.txt",
                            "content": test_content_b64,
                            "mimeType": "text/plain"
                        }
                    }
                )
                
                print(f"Add comment result: {result}")
                if isinstance(result, str):
                    try:
                        import ast
                        result = ast.literal_eval(result)
                    except (SyntaxError, ValueError):
                        print(f"Failed to parse result: {result}")
                
                self.assertTrue(isinstance(result, dict), 
                              f"Expected dict, got {type(result)}: {result}")
                self.assertTrue("id" in result or "message" in result, 
                              f"Expected id or message in response: {result}")
                print(f"Successfully added comment with attachment to {self.issue_key}")
            finally:
                await self.teardown_session()

        self.run_async_test(test_attachment())

    def test_3_search_issues(self):
        """Test searching for issues"""
        async def test_search():
            await self.setup_session()
            try:
                # Create test issue
                issue_result = await self.call_tool(
                    "create_jira_issue",
                    {
                        "projectKey": self.project_key,
                        "summary": "Test Issue for Search",
                        "description": "This is a test issue for search testing",
                        "issueType": "Task"
                    }
                )
                
                self.issue_key = issue_result.get('key')
                print(f"Created test issue: {self.issue_key}")

                # Search for the issue
                search_result = await self.call_tool(
                    "search_issues",
                    {
                        "projectKey": self.project_key,
                        "jql": f"key = {self.issue_key}"
                    }
                )
                
                print(f"Search result: {search_result}")
                
                # Ensure result is list-like
                if isinstance(search_result, str):
                    try:
                        import ast
                        search_result = ast.literal_eval(search_result)
                    except (SyntaxError, ValueError):
                        pass
                        
                self.assertTrue(isinstance(search_result, (list, tuple)), 
                              f"Expected list, got {type(search_result)}: {search_result}")
                self.assertTrue(len(search_result) > 0)
                print(f"Successfully searched for issues in project {self.project_key}")
                
            finally:
                await self.teardown_session()

        self.run_async_test(test_search())

    def test_4_get_issue(self):
        """Test getting issue details"""
        async def test_get():
            await self.setup_session()
            try:
                # Create test issue
                issue_result = await self.call_tool(
                    "create_jira_issue",
                    {
                        "projectKey": self.project_key,
                        "summary": "Test Issue for Get Details",
                        "description": "This is a test issue for getting details",
                        "issueType": "Task"
                    }
                )
                self.issue_key = issue_result["key"]

                # Get issue details
                result = await self.call_tool(
                    "get_issue",
                    {
                        "issueKey": self.issue_key
                    }
                )
                self.assertEqual(result["key"], self.issue_key)
                print(f"Successfully retrieved issue details for {self.issue_key}")
            finally:
                await self.teardown_session()

        self.run_async_test(test_get())

    def test_5_create_issue_link(self):
        """Test creating issue links"""
        async def test_link():
            await self.setup_session()
            try:
                # Create first issue
                first_issue = await self.call_tool(
                    "create_jira_issue",
                    {
                        "projectKey": self.project_key,
                        "summary": "Test Issue for Linking (1)",
                        "description": "This is a test issue for link testing",
                        "issueType": "Task"
                    }
                )
                self.issue_key = first_issue["key"]

                # Create second issue
                second_issue = await self.call_tool(
                    "create_jira_issue",
                    {
                        "projectKey": self.project_key,
                        "summary": "Test Issue for Linking (2)",
                        "description": "This is a test issue for link testing",
                        "issueType": "Task"
                    }
                )

                # Create link
                result = await self.call_tool(
                    "create_issue_link",
                    {
                        "inwardIssueKey": self.issue_key,
                        "outwardIssueKey": second_issue["key"],
                        "linkType": "Relates"
                    }
                )
                print(f"Successfully created issue link between {self.issue_key} and {second_issue['key']}")

                # Clean up second issue
                await self.call_tool(
                    "delete_issue",
                    {
                        "issueKey": second_issue["key"]
                    }
                )
            finally:
                await self.teardown_session()

        self.run_async_test(test_link())

    def test_6_update_issue(self):
        """Test updating an issue"""
        async def test_update():
            await self.setup_session()
            try:
                # Create test issue
                issue_result = await self.call_tool(
                    "create_jira_issue",
                    {
                        "projectKey": self.project_key,
                        "summary": "Test Issue for Update",
                        "description": "This is a test issue for update testing",
                        "issueType": "Task"
                    }
                )
                self.issue_key = issue_result["key"]

                # Update the issue
                result = await self.call_tool(
                    "update_issue",
                    {
                        "issueKey": self.issue_key,
                        "summary": "Updated Test Issue",
                        "description": "Updated test description"
                    }
                )
                print(f"Successfully updated issue {self.issue_key}")
            finally:
                await self.teardown_session()

        self.run_async_test(test_update())

    def test_7_get_user(self):
        """Test getting user details"""
        async def test_user():
            await self.setup_session()
            try:
                result = await self.call_tool(
                    "get_user",
                    {
                        "email": self.test_user_email
                    }
                )
                self.assertEqual(result["emailAddress"], self.test_user_email)
                print(f"Successfully retrieved user details for {self.test_user_email}")
            finally:
                await self.teardown_session()

        self.run_async_test(test_user())

    def test_8_list_fields(self):
        """Test listing available fields"""
        async def test_fields():
            await self.setup_session()
            try:
                result = await self.call_tool("list_fields", {})
                self.assertTrue(len(result) > 0)
                print("Successfully retrieved field list")
            finally:
                await self.teardown_session()

        self.run_async_test(test_fields())

    def test_9_list_issue_types(self):
        """Test listing issue types"""
        async def test_types():
            await self.setup_session()
            try:
                result = await self.call_tool(
                    "list_issue_types", 
                    {"projectKey": self.project_key}  # Add project key as argument
                )
                # print(f"Issue types result: {result}")
                
                # First check if result is string and attempt to parse it
                if isinstance(result, str):
                    try:
                        import ast
                        result = ast.literal_eval(result)
                    except (SyntaxError, ValueError):
                        print(f"Failed to parse result: {result}")
                        raise AssertionError(f"Failed to parse response: {result}")
                
                # Now validate result
                self.assertTrue(isinstance(result, (list, tuple)), 
                              f"Expected list, got {type(result)}: {result}")
                
                # Convert dicts if they're strings
                parsed_result = []
                for item in result:
                    if isinstance(item, str):
                        try:
                            parsed_item = ast.literal_eval(item)
                            parsed_result.append(parsed_item)
                        except (SyntaxError, ValueError):
                            parsed_result.append(item)
                    else:
                        parsed_result.append(item)
                
                # Check for Task type
                self.assertTrue(
                    any(isinstance(t, dict) and 'name' in t and 'Task' in t['name'] 
                        for t in parsed_result),
                    f"No Task type found in results: {parsed_result}"
                )
                print("Successfully retrieved issue types")
                
            finally:
                await self.teardown_session()

        self.run_async_test(test_types())

    def test_a_list_link_types(self):
        """Test listing link types"""
        async def test_link_types():
            await self.setup_session()
            try:
                result = await self.call_tool("list_link_types", {})
                self.assertTrue(len(result) > 0)
                print("Successfully retrieved link types")
            finally:
                await self.teardown_session()

        self.run_async_test(test_link_types())

    def test_b_delete_issue(self):
        """Test deleting an issue"""
        async def test_delete():
            await self.setup_session()
            try:
                # Create test issue
                issue_result = await self.call_tool(
                    "create_jira_issue",
                    {
                        "projectKey": self.project_key,
                        "summary": "Test Issue to be Deleted",
                        "description": "This is a test issue that will be deleted",
                        "issueType": "Task"
                    }
                )
                
                issue_key = issue_result.get('key')
                print(f"Created issue {issue_key} for deletion test")

                # Delete the issue
                await self.call_tool(
                    "delete_issue",
                    {
                        "issueKey": issue_key
                    }
                )

                # Add a small delay to ensure deletion is processed
                await asyncio.sleep(1)

                # Try to get the issue - should fail with 404
                try:
                    await self.call_tool(
                        "get_issue",
                        {
                            "issueKey": issue_key
                        }
                    )
                    self.fail("Issue still exists after deletion")
                except Exception as e:
                    error_msg = str(e)
                    # Check for either 404 error or existence error
                    self.assertTrue(
                        "HTTP 404" in error_msg or 
                        "does not exist" in error_msg,
                        f"Unexpected error response: {error_msg}"
                    )
                    
            finally:
                await self.teardown_session()

        self.run_async_test(test_delete())

def main():
    # Enable tracemalloc for memory stats
    tracemalloc.start()

    # Suppress warnings from anyio.streams.memory
    warnings.filterwarnings(
        "ignore",
        category=ResourceWarning,
        message=".*MemoryObject.*",
        module="anyio.streams.memory"
    )

    # Prepare JSON output structure
    test_results = {
        "summary": {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "execution_time": 0,
            "overall_status": "",
            "timestamp": datetime.datetime.now().isoformat()
        },
        "tests": [],
        "warnings": [],
        "memory_stats": [],
        "available_tools": []
    }

    # Capture warnings
    with warnings.catch_warnings(record=True) as captured_warnings:
        warnings.simplefilter("always")

        # Run the tests
        start_time = time.time()
        test_suite = unittest.TestLoader().loadTestsFromTestCase(TestJiraMCPIntegration)
        runner = JsonTestRunner(stream=StringIO(), verbosity=2)
        result = runner.run(test_suite)
        execution_time = time.time() - start_time

        # Process warnings
        test_results["warnings"] = [
            {
                "message": str(warning.message),
                "category": warning.category.__name__,
                "filename": warning.filename,
                "lineno": warning.lineno
            }
            for warning in captured_warnings
            if not (
                isinstance(warning.message, ResourceWarning) and
                "MemoryObject" in str(warning.message)
            )
        ]

    # Get memory statistics
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")
    
    for stat in top_stats[:10]:
        test_results["memory_stats"].append({
            "size": stat.size,
            "count": stat.count,
            "traceback": str(stat.traceback)
        })

    # Update summary
    test_results["summary"].update({
        "total_tests": result.testsRun,
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failed": len(result.failures) + len(result.errors),
        "execution_time": round(execution_time, 3),
        "overall_status": "PASS" if result.wasSuccessful() else "FAIL"
    })

    # Process test results
    test_results["tests"] = [
        {
            "name": name,
            "description": details['description'],
            "status": details['status'],
            "output": details['output'],
            "duration": round(details['duration'], 3),
            "error": details['error']
        }
        for name, details in result.test_results.items()
    ]

    # Get tools from class variable if available
    test_results["available_tools"] = TestJiraMCPIntegration.available_tools

    # Output JSON
    print(json.dumps(test_results, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == "__main__":
    main()