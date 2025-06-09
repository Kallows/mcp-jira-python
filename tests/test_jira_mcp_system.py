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
import re
from io import StringIO
from contextlib import AsyncExitStack, redirect_stdout
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
    def addSuccess(self, test):
        super().addSuccess(test)
        TestJiraMCPSystem.test_details[test._testMethodName]['status'] = 'PASS'
        
    def addError(self, test, err):
        super().addError(test, err)
        TestJiraMCPSystem.test_details[test._testMethodName]['status'] = 'ERROR'
        TestJiraMCPSystem.test_details[test._testMethodName]['error'] = self._exc_info_to_string(err, test)
        
    def addFailure(self, test, err):
        super().addFailure(test, err)
        TestJiraMCPSystem.test_details[test._testMethodName]['status'] = 'FAIL'
        TestJiraMCPSystem.test_details[test._testMethodName]['error'] = self._exc_info_to_string(err, test)

class JsonTestRunner(unittest.TextTestRunner):
    """Custom test runner that uses JsonTestResult"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_results = []

    def _makeResult(self):
        return _JsonTestResult(self.stream, self.descriptions, self.verbosity)

class TestJiraMCPSystem(unittest.TestCase):
    available_tools = []  # Class variable to store tools
    test_details = {}    # Class variable to store test details

    @classmethod
    def setUpClass(cls):
        cls.server_script = os.getenv("MCP_SERVER_SCRIPT", "../src/mcp_jira_python/server.py")
        cls.command = "python" if cls.server_script.endswith(".py") else "node"

    def setUp(self):
        self.output_capture = TestOutputCapture()
        self.start_time = time.time()
        
    def tearDown(self):
        # Store test details after each test
        test_name = self._testMethodName
        self.__class__.test_details[test_name] = {
            'description': getattr(self, test_name).__doc__ or '',
            'output': self.output_capture.output.getvalue(),
            'duration': time.time() - self.start_time,
            'status': 'PASS'  # Will be updated if test fails
        }
        
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

    async def get_tools(self):
        """Retrieve the list of tools from the MCP session."""
        tools_response = await self.session.list_tools()
        return tools_response.tools

    async def simulate_llm_request(self, tool_name, arguments):
        """Simulate an LLM request to a tool via MCP."""
        try:
            tools = await self.get_tools()
            tool_found = next((tool for tool in tools if tool.name == tool_name), None)
            if not tool_found:
                raise ValueError(f"Tool {tool_name} not found")
            response = await self.session.call_tool(tool_name, arguments)

            if isinstance(response.content, list) and len(response.content) > 0:
                first_item = response.content[0]
                if hasattr(first_item, "text"):
                    return json.loads(first_item.text.replace("'", '"'))
                else:
                    return first_item
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"

    def run_async_test(self, coroutine):
        """Helper to run async tests."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            with self.output_capture as captured:
                result = loop.run_until_complete(coroutine)
            return result
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def test_1_server_initialization(self):
        """Test server initialization and available tools."""
        async def test_init():
            await self.setup_session()
            try:
                tools = await self.get_tools()
                self.assertTrue(len(tools) > 0)
                self.assertTrue(any(tool.name == "create_jira_issue" for tool in tools))
                tool_names = [tool.name for tool in tools]
                print("Server initialized successfully with tools:", tool_names)
                # Store tools in class variable
                self.__class__.available_tools = tool_names
            finally:
                await self.teardown_session()

        self.run_async_test(test_init())

    def test_2_llm_workflow_success(self):
        """Test a typical LLM workflow with multiple connected operations."""
        async def test_workflow():
            await self.setup_session()
            try:
                # 1. Create a test issue
                create_result = await self.simulate_llm_request(
                    "create_jira_issue",
                    {
                        "projectKey": "TEST",
                        "summary": "Test Issue from LLM Workflow",
                        "description": "This is a test issue created by the LLM workflow",
                        "issueType": "Task",
                        "priority": "Medium",
                        "assignee": os.getenv("JIRA_EMAIL")
                    }
                )
                self.assertTrue("key" in create_result)
                issue_key = create_result["key"]

                # 2. Add a comment to the issue
                comment_result = await self.simulate_llm_request(
                    "add_comment",
                    {
                        "issueKey": issue_key,
                        "comment": "Testing from LLM workflow"
                    }
                )
                self.assertTrue("message" in comment_result)
                
                # 3. Search for the issue
                search_result = await self.simulate_llm_request(
                    "search_issues",
                    {
                        "projectKey": "TEST",
                        "jql": f"key = {issue_key}"
                    }
                )
                self.assertTrue(isinstance(search_result, list))
                print("LLM workflow completed successfully")
            finally:
                await self.teardown_session()

        self.run_async_test(test_workflow())

    def test_3_error_handling(self):
        """Test how the system handles various error scenarios an LLM might encounter."""
        async def test_errors():
            await self.setup_session()
            try:
                # Test invalid issue key
                result = await self.simulate_llm_request(
                    "get_issue",
                    {
                        "issueKey": "INVALID-999"
                    }
                )
                self.assertTrue("Error" in str(result))
                
                # Test missing required arguments
                result = await self.simulate_llm_request(
                    "add_comment",
                    {
                        "issueKey": "TEST-123"
                        # Missing required 'comment' field
                    }
                )
                self.assertTrue("Error" in str(result))
                
                # Test invalid tool name
                result = await self.simulate_llm_request(
                    "nonexistent_tool",
                    {}
                )
                self.assertTrue("Error" in str(result))
                print("Error handling tests completed")
            finally:
                await self.teardown_session()
            
        self.run_async_test(test_errors())

    def test_5_complex_data_handling(self):
        """Test handling of complex data types and attachments."""
        async def test_complex_data():
            await self.setup_session()
            try:
                # Test comment with attachment
                test_content = "Test file content"
                test_content_b64 = base64.b64encode(test_content.encode()).decode()
                
                result = await self.simulate_llm_request(
                    "add_comment_with_attachment",
                    {
                        "issueKey": "TEST-123",
                        "comment": "Test comment with attachment",
                        "attachment": {
                            "filename": "test.txt",
                            "content": test_content_b64,
                            "mimeType": "text/plain"
                        }
                    }
                )
                self.assertTrue("message" in result)
                print("Complex data handling tests completed")
            finally:
                await self.teardown_session()
            
        self.run_async_test(test_complex_data())

    def test_6_rate_limiting(self):
        """Test system behavior under rapid LLM requests."""
        async def test_rate_limits():
            await self.setup_session()
            try:
                # Make multiple rapid requests
                tasks = []
                for _ in range(5):
                    tasks.append(self.simulate_llm_request(
                        "get_issue",
                        {"issueKey": "TEST-123"}
                    ))
                
                # Run requests concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Verify all requests completed
                self.assertEqual(len(results), 5)
                # Check if any rate limiting errors occurred
                rate_limited = any("rate" in str(r).lower() for r in results if isinstance(r, str))
                print(f"Rate limiting test completed {'with rate limits' if rate_limited else 'without rate limits'}")
            finally:
                await self.teardown_session()
            
        self.run_async_test(test_rate_limits())

def main():
    # Suppress all warnings from anyio.streams.memory
    warnings.filterwarnings(
        "ignore",
        category=ResourceWarning,
        message=".*MemoryObject.*",
        module="anyio.streams.memory"
    )
    
    # Also suppress at runtime for any that slip through
    warnings.filterwarnings(
        "ignore",
        category=ResourceWarning,
        message=".*MemoryObject.*"
    )
    
    # Enable tracemalloc for debugging
    tracemalloc.start()

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
        test_suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestJiraMCPSystem)
        runner = JsonTestRunner(verbosity=2, stream=StringIO())
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
                "MemoryObject" in str(warning.message) and
                "anyio/streams/memory.py" in warning.filename
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

    # Process test results using the class variable
    test_results["tests"] = [
        {
            "name": name,
            "description": details['description'],
            "status": details['status'],
            "output": details['output'],
            "duration": round(details['duration'], 3),
            "error": details.get('error')
        }
        for name, details in TestJiraMCPSystem.test_details.items()
    ]

    # Get tools from class variable
    test_results["available_tools"] = TestJiraMCPSystem.available_tools

    # Output JSON
    print(json.dumps(test_results, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == "__main__":
    main()