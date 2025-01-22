# MCP JIRA Python 🚀

[![smithery badge](https://smithery.ai/badge/@Kallows/mcp-jira-python)](https://smithery.ai/go/@Kallows/mcp-jira-python)

A Python implementation of a MCP server for JIRA integration. MCP is a communication protocol designed to provide tools to your AI and keep your data secure (and local if you like). The server runs on the same computer as your AI application and the Claude Desktop is the first application to run MCP Servers (and is considered a client. See the examples folder for a simple python MCP client).

## Installation

### Installing via Smithery

To install JIRA for Claude Desktop automatically via [Smithery](https://smithery.ai/go/@Kallows/mcp-jira-python):

```bash
npx -y @smithery/cli install @Kallows/mcp-jira-python --client claude
```

### Manual Installation
```bash
# Install the server locally
git clone https://github.com/kallows/mcp-jira-python.git 
```

## Tools Available

This MCP server provides the following JIRA integration tools:

- `delete_issue`: Delete a Jira issue or subtask using its issue key
- `create_jira_issue`: Create a new Jira issue with customizable fields including summary, description, type, priority, and assignee
- `get_issue`: Retrieve complete issue details including comments and attachments for a given issue key
- `create_issue_link`: Create relationships between issues (e.g., "blocks", "is blocked by", etc.)
- `update_issue`: Update existing issues with new values for fields like summary, description, status, priority, or assignee
- `get_user`: Look up a user's account ID using their email address
- `list_fields`: Get a list of all available JIRA fields and their properties
- `list_issue_types`: Retrieve all available issue types in your JIRA instance
- `list_link_types`: Get all possible relationship types for issue linking
- `search_issues`: Search for issues using JQL (JIRA Query Language) within a specific project
- `add_comment`: Add a text comment to an existing issue
- `add_comment_with_attachment`: Add a comment to an issue with an attached file

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
        "src/jira-api/server.py"
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
TODO - add description of running the tests (unittest)
TODO - add some code to make it easier for the tests to get the env vars as the integration and system tests require the following environment variables:

```bash
export JIRA_HOST="your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```
TODO - generate a test coverage report:

## Project Structure

```
mcp-jira-python/
├── README.md
├── pyproject.toml
├── src/
│   └── jira_api/
│       ├── __init__.py
│       └── server.py
└── tests/
    ├── __init__.py
    ├── test_jira_api.py
    ├── test_jira_integration.py
    └── test_jira_mcp_system.py
```
