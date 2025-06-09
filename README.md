[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/kallows-mcp-jira-python-badge.png)](https://mseep.ai/app/kallows-mcp-jira-python)

# MCP JIRA Python 🚀

A Python implementation of a MCP server for JIRA integration. MCP is a communication protocol designed to provide tools to your AI and keep your data secure (and local if you like). The server runs on the same computer as your AI application and the Claude Desktop is the first application to run MCP Servers (and is considered a client. See the examples folder for a simple python MCP client).

## Installation

```bash
# Install the server locally
git clone https://github.com/kallows/mcp-jira-python.git 
```

## Tools Available

This MCP server provides the following JIRA integration tools:

- `delete_issue`: Delete a Jira issue or subtask using its issue key
- `create_jira_issue`: Create a new Jira issue with customizable fields including summary, description, type, priority, and assignee
- `get_issue`: Retrieve complete issue details including comments and attachments for a given issue key
- `get_issue_attachment`: Download an attachment from a Jira issue to a local file
- `create_issue_link`: Create relationships between issues (e.g., "blocks", "is blocked by", etc.)
- `update_issue`: Update existing issues with new values for fields like summary, description, status, priority, or assignee
- `get_user`: Look up a user's account ID using their email address
- `list_fields`: Get a list of all available JIRA fields and their properties
- `list_issue_types`: Retrieve all available issue types in your JIRA instance
- `list_link_types`: Get all possible relationship types for issue linking
- `search_issues`: Search for issues using JQL (JIRA Query Language) within a specific project
- `add_comment`: Add a text comment to an existing issue
- `add_comment_with_attachment`: Add a comment to an issue with an attached file
- `attach_file`: Add a file attachment to an existing issue
- `attach_content`: Create and attach content directly to a Jira issue (allows creating attachments from any text or data content)

## Claude Desktop Configuration
This requires you update claude_desktop_config.json. The file's location varies depending on Apple, Windows, or Linux.
 
### Windows
Note: location of claude_desktop_config.json in Windows is:
```
%AppData%\\Claude\\claude_desktop_config.json
```
This will resolve (usually) to: 
C:\\Users\\YOURUSERNAME\\AppData\\Roaming\\Claude

Below is the configuration block to add to claude_desktop_config.json.
With Windows we always use full paths. You will update "command", set your directory path, and add your JIRA env settings
<pre>
    "jira-api": {
      "command": "C:\\\\Users\\\\YOURUSERNAME\\\\.local\\\\bin\\\\uv.exe",
      "args": [
        "--directory",
        "D:\\\\mcp\\\\mcp-jira-python",
        "run",
        "-m",
        "mcp_jira_python.server"
      ],
      "env": {
        "JIRA_HOST": "YOURNAME.atlassian.net",
        "JIRA_EMAIL": "yourname@example.com",
        "JIRA_API_TOKEN": "YOURJIRATOKEN"
      }      
    }
</pre>
#### ☠️WARNING - you MUST close Claude Desktop AND kill all Claude processes to enable the updated claude_desktop_config.json!😬

### Mac and Linux
Update the filepath to mcp-jira-python and fill in your JIRA env values:
<pre>
    "mcp-jira-python": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/your/filepath/mcp-jira-python",
        "-m", "mcp_jira_python.server"
      ],
      "env": {
        "JIRA_HOST": "your_org.atlassian.net",
        "JIRA_EMAIL": "you@your_org.com",
        "JIRA_API_TOKEN": "your_api_token"
      }      
    }
</pre>

#### Note:
You must restart Claude Desktop after saving changes to claude_desktop_config.json.

## Running MCP JIRA Python Tools
These MCP Tools are listed under jira-api server. You can see the listing by clicking on the tiny hammer in the lower right corner of the Claude Desktop text entry box. Please verify that the jira-api tools are available in the list. To 'run' a tool, just ask Claude specifically to do a Jira task. Notably, Claude may not see the tools at first and has to be nudged. In some cases, he will refuse to use tools. Updating the system prompt is recommended.

## Running Tests    

The test suite provides comprehensive coverage of the MCP JIRA server functionality. To run tests, you need to set up environment variables for integration tests:

```bash
export JIRA_HOST="your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
export JIRA_PROJECT_KEY="TEST"  # Project key for test issues
```

Run the full test suite:
```bash
python -m unittest discover tests
```

Run specific test categories:
```bash
# Integration tests
python -m unittest tests/test_jira_mcp_integration.py

# Unit tests for individual tools
python -m unittest discover tests/unit_tests

# Endpoint-specific tests
python -m unittest discover tests/endpoint_tests
```

Generate test coverage report:
```bash
python -m coverage run -m unittest discover tests
python -m coverage report
```

## Project Structure

```
mcp-jira-python/
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── examples/
│   └── client.py
├── src/
│   └── mcp_jira_python/
│       ├── __init__.py
│       ├── server.py
│       └── tools/
│           ├── __init__.py
│           ├── base.py
│           ├── add_comment.py
│           ├── add_comment_with_attachment.py
│           ├── attach_content.py
│           ├── attach_file.py
│           ├── create_issue.py
│           ├── create_issue_link.py
│           ├── delete_issue.py
│           ├── get_issue.py
│           ├── get_issue_attachment.py
│           ├── get_user.py
│           ├── list_fields.py
│           ├── list_issue_types.py
│           ├── list_link_types.py
│           ├── search_issues.py
│           └── update_issue.py
└── tests/
    ├── __init__.py
    ├── README.md
    ├── conftest.py
    ├── test_jira_connection.py
    ├── test_jira_endpoints.py
    ├── test_jira_mcp_integration.py
    ├── test_jira_mcp_system.py
    ├── test_integration.py
    └── test_unit.py
    ├── endpoint_tests/
    │   ├── test_add_comment.py
    │   ├── test_create_issue.py
    │   ├── test_get_issue.py
    │   └── test_update_issue.py
    └── unit_tests/
        ├── __init__.py
        ├── test_base.py
        ├── test_add_comment.py
        ├── test_add_comment_with_attachment.py
        ├── test_create_issue.py
        ├── test_create_issue_link.py
        ├── test_delete_issue.py
        ├── test_get_issue.py
        ├── test_search_issues.py
        └── test_update_issue.py
```