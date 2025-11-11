#!/usr/bin/env python3
"""
Jira CLI - Fully Standalone Version
All Jira tool functions embedded (no external dependencies except jira-python).

This is a self-contained CLI for interacting with Jira.
Two points of maintenance with mcp-jira-python - but fully portable.
"""

import asyncio
import os
import sys
import json
import argparse
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

# Try to import jira
try:
    from jira import JIRA
except ImportError:
    print("Error: jira-python library not available.", file=sys.stderr)
    print("Install with: pip install jira", file=sys.stderr)
    sys.exit(1)

# ============================================================================
# JIRA CLIENT SETUP
# ============================================================================

def create_jira_client(host: str = None, email: str = None, token: str = None) -> JIRA:
    """Create JIRA client from environment or parameters"""
    host = host or os.getenv("JIRA_HOST")
    email = email or os.getenv("JIRA_EMAIL")
    token = token or os.getenv("JIRA_API_TOKEN")

    if not all([host, email, token]):
        raise ValueError(
            "Missing JIRA credentials. Set JIRA_HOST, JIRA_EMAIL, JIRA_API_TOKEN "
            "environment variables or pass --jira-host, --jira-email, --jira-token"
        )

    return JIRA(
        server=f"https://{host}",
        basic_auth=(email, token)
    )

# ============================================================================
# TOOL FUNCTIONS (Extracted from mcp-jira-python/src/mcp_jira_python/tools)
# ============================================================================

async def create_jira_issue(jira: JIRA, **kwargs) -> str:
    """Create a new Jira issue"""
    project_key = kwargs.get("projectKey")
    summary = kwargs.get("summary")
    issue_type = kwargs.get("issueType")

    if not all([project_key, summary, issue_type]):
        return json.dumps({"error": "projectKey, summary, and issueType are required"})

    issue_dict = {
        'project': {'key': project_key},
        'summary': summary,
        'issuetype': {'name': issue_type}
    }

    for field in ["description", "priority", "assignee"]:
        if field in kwargs:
            if field == "assignee":
                issue_dict[field] = {'emailAddress': kwargs[field]}
            elif field == "priority":
                issue_dict[field] = {'name': kwargs[field]}
            else:
                issue_dict[field] = kwargs[field]

    try:
        issue = jira.create_issue(fields=issue_dict)
        return json.dumps({
            "key": issue.key,
            "id": issue.id,
            "self": issue.self
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to create issue: {str(e)}"})


async def get_issue(jira: JIRA, **kwargs) -> str:
    """Get complete issue details including comments and attachments"""
    issue_key = kwargs.get("issueKey")
    if not issue_key:
        return json.dumps({"error": "issueKey is required"})

    try:
        issue = jira.issue(issue_key, expand='comments,attachments')

        comments = [{
            "id": comment.id,
            "author": str(comment.author),
            "body": comment.body,
            "created": str(comment.created)
        } for comment in issue.fields.comment.comments]

        attachments = [{
            "id": attachment.id,
            "filename": attachment.filename,
            "size": attachment.size,
            "created": str(attachment.created)
        } for attachment in issue.fields.attachment]

        issue_data = {
            "key": issue.key,
            "summary": issue.fields.summary,
            "description": issue.fields.description,
            "status": str(issue.fields.status),
            "priority": str(issue.fields.priority) if hasattr(issue.fields, 'priority') and issue.fields.priority else None,
            "assignee": str(issue.fields.assignee) if hasattr(issue.fields, 'assignee') and issue.fields.assignee else None,
            "type": str(issue.fields.issuetype),
            "comments": comments,
            "attachments": attachments
        }

        return json.dumps(issue_data, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Failed to get issue: {str(e)}"})


async def update_issue(jira: JIRA, **kwargs) -> str:
    """Update an existing Jira issue"""
    issue_key = kwargs.get("issueKey")
    if not issue_key:
        return json.dumps({"error": "issueKey is required"})

    try:
        issue = jira.issue(issue_key)
        fields = {}

        if "summary" in kwargs:
            fields['summary'] = kwargs["summary"]
        if "description" in kwargs:
            fields['description'] = kwargs["description"]
        if "priority" in kwargs:
            fields['priority'] = {'name': kwargs["priority"]}
        if "assignee" in kwargs:
            fields['assignee'] = {'emailAddress': kwargs["assignee"]}

        if fields:
            issue.update(fields=fields)

        return json.dumps({
            "key": issue_key,
            "updated": True,
            "fields": list(fields.keys())
        })

    except Exception as e:
        return json.dumps({"error": f"Failed to update issue: {str(e)}"})


async def delete_issue(jira: JIRA, **kwargs) -> str:
    """Delete a Jira issue"""
    issue_key = kwargs.get("issueKey")
    if not issue_key:
        return json.dumps({"error": "issueKey is required"})

    try:
        issue = jira.issue(issue_key)
        issue.delete()
        return json.dumps({
            "key": issue_key,
            "deleted": True
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to delete issue: {str(e)}"})


async def search_issues(jira: JIRA, **kwargs) -> str:
    """Search for issues using JQL"""
    project_key = kwargs.get("projectKey")
    jql = kwargs.get("jql")

    if not project_key or not jql:
        return json.dumps({"error": "projectKey and jql are required"})

    try:
        full_jql = f"project = {project_key} AND {jql}"
        issues = jira.search_issues(
            full_jql,
            maxResults=30,
            fields="summary,description,status,priority,assignee,issuetype"
        )

        results = [{
            "key": issue.key,
            "summary": issue.fields.summary,
            "status": str(issue.fields.status),
            "priority": str(issue.fields.priority) if hasattr(issue.fields, 'priority') and issue.fields.priority else None,
            "assignee": str(issue.fields.assignee) if hasattr(issue.fields, 'assignee') and issue.fields.assignee else None,
            "type": str(issue.fields.issuetype)
        } for issue in issues]

        return json.dumps(results, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Failed to search issues: {str(e)}"})


async def add_comment(jira: JIRA, **kwargs) -> str:
    """Add a comment to an issue"""
    issue_key = kwargs.get("issueKey")
    comment = kwargs.get("comment")

    if not issue_key or not comment:
        return json.dumps({"error": "issueKey and comment are required"})

    try:
        jira.add_comment(issue_key, comment)
        return json.dumps({
            "key": issue_key,
            "comment_added": True
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to add comment: {str(e)}"})


async def create_issue_link(jira: JIRA, **kwargs) -> str:
    """Create a link between two issues"""
    inward_issue = kwargs.get("inwardIssue")
    outward_issue = kwargs.get("outwardIssue")
    link_type = kwargs.get("linkType")

    if not all([inward_issue, outward_issue, link_type]):
        return json.dumps({"error": "inwardIssue, outwardIssue, and linkType are required"})

    try:
        jira.create_issue_link(link_type, inward_issue, outward_issue)
        return json.dumps({
            "inwardIssue": inward_issue,
            "outwardIssue": outward_issue,
            "linkType": link_type,
            "linked": True
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to create issue link: {str(e)}"})


async def get_user(jira: JIRA, **kwargs) -> str:
    """Get user information"""
    email = kwargs.get("email")
    if not email:
        return json.dumps({"error": "email is required"})

    try:
        users = jira.search_users(query=email)
        if not users:
            return json.dumps({"error": f"User with email {email} not found"})

        user = users[0]
        return json.dumps({
            "accountId": user.accountId,
            "displayName": user.displayName,
            "emailAddress": getattr(user, 'emailAddress', None),
            "active": user.active
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to get user: {str(e)}"})


async def list_fields(jira: JIRA, **kwargs) -> str:
    """List all available fields"""
    try:
        fields = jira.fields()
        field_list = [{
            "id": field['id'],
            "name": field['name'],
            "custom": field.get('custom', False)
        } for field in fields]

        return json.dumps(field_list, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to list fields: {str(e)}"})


async def list_issue_types(jira: JIRA, **kwargs) -> str:
    """List all issue types"""
    try:
        issue_types = jira.issue_types()
        types_list = [{
            "id": it.id,
            "name": it.name,
            "description": it.description
        } for it in issue_types]

        return json.dumps(types_list, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to list issue types: {str(e)}"})


async def list_link_types(jira: JIRA, **kwargs) -> str:
    """List all issue link types"""
    try:
        link_types = jira.issue_link_types()
        types_list = [{
            "id": lt.id,
            "name": lt.name,
            "inward": lt.inward,
            "outward": lt.outward
        } for lt in link_types]

        return json.dumps(types_list, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to list link types: {str(e)}"})


async def attach_file(jira: JIRA, **kwargs) -> str:
    """Attach a file to an issue"""
    issue_key = kwargs.get("issueKey")
    file_path = kwargs.get("filePath")

    if not issue_key or not file_path:
        return json.dumps({"error": "issueKey and filePath are required"})

    try:
        if not os.path.exists(file_path):
            return json.dumps({"error": f"File not found: {file_path}"})

        with open(file_path, 'rb') as f:
            jira.add_attachment(issue_key, attachment=f, filename=os.path.basename(file_path))

        return json.dumps({
            "key": issue_key,
            "filename": os.path.basename(file_path),
            "attached": True
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to attach file: {str(e)}"})


async def attach_content(jira: JIRA, **kwargs) -> str:
    """Attach content as a file to an issue"""
    issue_key = kwargs.get("issueKey")
    filename = kwargs.get("filename")
    content = kwargs.get("content")

    if not all([issue_key, filename, content]):
        return json.dumps({"error": "issueKey, filename, and content are required"})

    try:
        import io
        content_bytes = content.encode('utf-8')
        jira.add_attachment(issue_key, attachment=io.BytesIO(content_bytes), filename=filename)

        return json.dumps({
            "key": issue_key,
            "filename": filename,
            "attached": True
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to attach content: {str(e)}"})


async def get_issue_attachment(jira: JIRA, **kwargs) -> str:
    """Get attachment from an issue and save to file"""
    issue_key = kwargs.get("issueKey")
    attachment_id = kwargs.get("attachmentId")
    output_path = kwargs.get("outputPath")

    if not all([issue_key, attachment_id]):
        return json.dumps({"error": "issueKey and attachmentId are required"})

    try:
        issue = jira.issue(issue_key, fields='attachment')

        attachment = None
        for att in issue.fields.attachment:
            if att.id == attachment_id or att.filename == attachment_id:
                attachment = att
                break

        if not attachment:
            return json.dumps({"error": f"Attachment {attachment_id} not found"})

        content = jira._session.get(attachment.content).content

        if output_path:
            with open(output_path, 'wb') as f:
                f.write(content)
            return json.dumps({
                "filename": attachment.filename,
                "size": attachment.size,
                "saved_to": output_path
            })
        else:
            # Return base64 encoded content
            import base64
            return json.dumps({
                "filename": attachment.filename,
                "size": attachment.size,
                "content": base64.b64encode(content).decode('utf-8')
            })
    except Exception as e:
        return json.dumps({"error": f"Failed to get attachment: {str(e)}"})


async def add_comment_with_attachment(jira: JIRA, **kwargs) -> str:
    """Add a comment with an attachment to an issue"""
    issue_key = kwargs.get("issueKey")
    comment = kwargs.get("comment")
    file_path = kwargs.get("filePath")

    if not all([issue_key, comment, file_path]):
        return json.dumps({"error": "issueKey, comment, and filePath are required"})

    try:
        if not os.path.exists(file_path):
            return json.dumps({"error": f"File not found: {file_path}"})

        # Add comment
        jira.add_comment(issue_key, comment)

        # Add attachment
        with open(file_path, 'rb') as f:
            jira.add_attachment(issue_key, attachment=f, filename=os.path.basename(file_path))

        return json.dumps({
            "key": issue_key,
            "comment_added": True,
            "attachment_added": True,
            "filename": os.path.basename(file_path)
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to add comment with attachment: {str(e)}"})


# ============================================================================
# CLI INTERFACE
# ============================================================================

class JiraCLI:
    """Standalone CLI with all Jira functions embedded"""

    def __init__(self, jira_client: JIRA, verbose: bool = False):
        self.jira = jira_client
        self.verbose = verbose

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool function"""
        if arguments is None:
            arguments = {}

        if self.verbose:
            print(f"\n→ Calling: {tool_name}", file=sys.stderr)
            print(f"  Args: {json.dumps(arguments, indent=2)}", file=sys.stderr)

        try:
            # Map tool names to functions
            func = globals().get(tool_name)
            if not func or not callable(func):
                raise AttributeError(f"Tool '{tool_name}' not found")

            result = await func(self.jira, **arguments)

            if self.verbose:
                preview = result[:200] + "..." if len(result) > 200 else result
                print(f"✓ Result: {preview}", file=sys.stderr)

            return {
                "success": True,
                "tool": tool_name,
                "arguments": arguments,
                "result": result
            }

        except Exception as e:
            if self.verbose:
                print(f"✗ Error: {str(e)}", file=sys.stderr)
            return {
                "success": False,
                "tool": tool_name,
                "arguments": arguments,
                "error": str(e)
            }

    async def list_available_tools(self) -> List[str]:
        """List all available tool functions"""
        tools = [
            'create_jira_issue', 'get_issue', 'update_issue', 'delete_issue',
            'search_issues', 'add_comment', 'create_issue_link', 'get_user',
            'list_fields', 'list_issue_types', 'list_link_types', 'attach_file',
            'attach_content', 'get_issue_attachment', 'add_comment_with_attachment'
        ]
        return tools


async def interactive_mode(cli: JiraCLI):
    """Interactive REPL mode"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║           Jira CLI - Standalone (Self-Contained)             ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    print("Type 'help' for commands, 'quit' to exit")
    print()

    try:
        while True:
            try:
                user_input = input("jira> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break

                if user_input.lower() == 'help':
                    print("""
╔════════════════════════════════════════════════════════════════╗
║                      Available Commands                        ║
╚════════════════════════════════════════════════════════════════╝

  list                      List available tools
  call <tool> <json>        Call a tool with JSON arguments
  help                      Show this help
  quit                      Exit

Examples:
  call get_issue {"issueKey": "TEST-123"}
  call create_jira_issue {"projectKey": "TEST", "summary": "New issue", "issueType": "Task"}
  call search_issues {"projectKey": "TEST", "jql": "status = Open"}
                    """)
                    continue

                # Shortcut: list
                if user_input.lower() == 'list':
                    tools = await cli.list_available_tools()
                    print(f"\n📋 Available tools ({len(tools)}):\n")
                    for tool in tools:
                        print(f"     • {tool}")
                    print()
                    continue

                # Full call syntax
                if user_input.startswith('call '):
                    parts = user_input[5:].split(maxsplit=1)
                    if len(parts) < 1:
                        print("❌ Missing tool name")
                        continue

                    tool_name = parts[0]
                    args = {}

                    if len(parts) == 2:
                        try:
                            args = json.loads(parts[1])
                        except json.JSONDecodeError as e:
                            print(f"❌ Invalid JSON: {e}")
                            continue

                    result = await cli.call_tool(tool_name, args)

                    if result["success"]:
                        print(f"\n{result['result']}\n")
                    else:
                        print(f"\n❌ Error: {result['error']}\n")

                    continue

                print("❌ Unknown command. Type 'help' for available commands.")

            except KeyboardInterrupt:
                print("\n^C")
                continue
            except EOFError:
                print("\nGoodbye!")
                break

    finally:
        pass


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Jira CLI - Standalone (Self-Contained)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--jira-host', type=str, help='Jira host (or set JIRA_HOST env var)')
    parser.add_argument('--jira-email', type=str, help='Jira email (or set JIRA_EMAIL env var)')
    parser.add_argument('--jira-token', type=str, help='Jira API token (or set JIRA_API_TOKEN env var)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if not args.interactive:
        parser.error("Must specify --interactive mode")

    try:
        # Create JIRA client
        jira_client = create_jira_client(args.jira_host, args.jira_email, args.jira_token)
        cli = JiraCLI(jira_client, verbose=args.verbose)

        # Run interactive mode
        asyncio.run(interactive_mode(cli))

    except ValueError as e:
        print(f"\n❌ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
