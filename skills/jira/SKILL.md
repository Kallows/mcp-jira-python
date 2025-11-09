---
name: "jira"
description: "Interactive CLI for managing Jira issues, comments, attachments, and workflows."
---

# Jira Skill

Standalone CLI for managing Jira issues, search, comments, attachments, and links.

## Quick Start

```bash
# Set environment variables
export JIRA_HOST="your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"

# Install dependencies
pip install jira

# Interactive mode
python /mnt/skills/user/jira/scripts/jira_cli.py --interactive
```

## Available Tools (15 total)

### Issue Management
- **create_jira_issue** - `projectKey`, `summary`, `issueType`, `description` (opt), `priority` (opt), `assignee` (opt)
- **get_issue** - `issueKey`
- **update_issue** - `issueKey`, `summary` (opt), `description` (opt), `priority` (opt), `assignee` (opt)
- **delete_issue** - `issueKey`
- **search_issues** - `projectKey`, `jql`

### Comments & Collaboration
- **add_comment** - `issueKey`, `comment`
- **add_comment_with_attachment** - `issueKey`, `comment`, `filePath`
- **create_issue_link** - `inwardIssue`, `outwardIssue`, `linkType`

### Attachments
- **attach_file** - `issueKey`, `filePath`
- **attach_content** - `issueKey`, `filename`, `content`
- **get_issue_attachment** - `issueKey`, `attachmentId`, `outputPath` (opt)

### Metadata & Discovery
- **get_user** - `email`
- **list_fields** - (no args)
- **list_issue_types** - (no args)
- **list_link_types** - (no args)

## Tested Working Examples

### Example 1: Get Issue Details

```bash
jira> call get_issue {"issueKey": "TEST-123"}
# Returns full issue with comments and attachments
```

### Example 2: Create New Issue

```bash
jira> call create_jira_issue {
  "projectKey": "TEST",
  "summary": "Bug in login",
  "issueType": "Bug",
  "description": "Users cannot log in",
  "priority": "High"
}
# Returns: {"key": "TEST-456", "id": "12345", ...}
```

### Example 3: Search Issues

```bash
jira> call search_issues {
  "projectKey": "TEST",
  "jql": "status = Open AND priority = High"
}
# Returns array of matching issues
```

### Example 4: Add Comment

```bash
jira> call add_comment {
  "issueKey": "TEST-123",
  "comment": "Fixed in latest release"
}
```

### Example 5: Update Issue

```bash
jira> call update_issue {
  "issueKey": "TEST-123",
  "summary": "Updated summary",
  "priority": "Medium",
  "assignee": "user@example.com"
}
```

## Common Workflows

### Workflow 1: Create Issue with Attachment

```bash
# Create issue
call create_jira_issue {"projectKey": "TEST", "summary": "New feature", "issueType": "Story"}

# Attach file
call attach_file {"issueKey": "TEST-789", "filePath": "/path/to/spec.pdf"}

# Add comment
call add_comment {"issueKey": "TEST-789", "comment": "Specification attached"}
```

### Workflow 2: Search and Update Issues

```bash
# Search for open bugs
call search_issues {"projectKey": "TEST", "jql": "type = Bug AND status = Open"}

# Update priority
call update_issue {"issueKey": "TEST-456", "priority": "Critical"}

# Assign to user
call update_issue {"issueKey": "TEST-456", "assignee": "dev@example.com"}
```

### Workflow 3: Link Related Issues

```bash
# Get link types available
call list_link_types {}

# Create link between issues
call create_issue_link {
  "inwardIssue": "TEST-123",
  "outwardIssue": "TEST-456",
  "linkType": "Blocks"
}
```

## Configuration

### Environment Variables (Required)

```bash
export JIRA_HOST="your-domain.atlassian.net"      # Without https://
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

### Get API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token and set as JIRA_API_TOKEN

### Command Line Options

```bash
python jira_cli.py --interactive \
  --jira-host your-domain.atlassian.net \
  --jira-email your@email.com \
  --jira-token your-token \
  --verbose
```

## Important Notes for AI Assistants

### JQL (Jira Query Language)
- Use JQL for advanced searches: `status = Open AND assignee = currentUser()`
- Common operators: `=`, `!=`, `>`, `<`, `IN`, `NOT IN`, `~` (contains)
- Common functions: `currentUser()`, `now()`, `startOfDay()`

### Issue Types
- Standard types: Bug, Task, Story, Epic
- Use `list_issue_types` to see available types for your instance

### Link Types
- Common types: Blocks, Clones, Duplicates, Relates
- Use `list_link_types` to see available types

### Field Names
- Use `list_fields` to discover custom fields
- Custom fields usually have IDs like `customfield_10001`

### Attachments
- `get_issue_attachment` returns base64 if no `outputPath` provided
- Use `attach_content` to attach text/code without creating a file
- `add_comment_with_attachment` combines both operations

### Error Handling
- All functions return JSON with `error` key on failure
- Check for `"error"` in response before processing
- Common errors: Authentication failed, Issue not found, Permission denied

## Jira Emoticons

Supported emoticons in descriptions/comments:
- Smileys: `:)` `:(`  `:P` `:D` `;)`
- Symbols: `(y)` (thumbs up), `(n)` (thumbs down), `(i)` (info), `(!)` (warning)
- Status: `(/)` (checkmark), `(x)` (cross), `(on)` `(off)`
- Stars: `(*)` `(*r)` (red) `(*g)` (green) `(*b)` (blue) `(*y)` (yellow)

**Note:** Unicode emojis will not display correctly - use Jira emoticons only.

## Troubleshooting

### Authentication Failed
```bash
# Check environment variables
echo $JIRA_HOST
echo $JIRA_EMAIL
# Don't echo JIRA_API_TOKEN for security

# Test connection
call get_user {"email": "your-email@example.com"}
```

### Issue Not Found
```bash
# Verify issue key format (PROJECT-###)
call get_issue {"issueKey": "TEST-123"}

# Search to find correct key
call search_issues {"projectKey": "TEST", "jql": "summary ~ 'search term'"}
```

### Permission Denied
```bash
# Check user permissions in Jira
call get_user {"email": "your-email@example.com"}

# Some operations require project admin or Jira admin rights
```

### Invalid JQL
```bash
# Test JQL in Jira web UI first
# Use simple queries initially
call search_issues {"projectKey": "TEST", "jql": "status = Open"}

# Build complexity gradually
call search_issues {"projectKey": "TEST", "jql": "status = Open AND priority IN (High, Critical)"}
```

## Dependencies

```python
# Required
import jira  # pip install jira

# Standard library only
import asyncio, os, sys, json, argparse, io, base64
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
```

## CLI Features

- ✓ Fully standalone (all functions embedded)
- ✓ No MCP server required
- ✓ Environment variable or CLI arg configuration
- ✓ Interactive REPL mode
- ✓ JSON input/output
- ✓ Verbose debugging mode
- ✓ Complete error handling

## Examples Output

**Get Issue:**
```json
{
  "key": "TEST-123",
  "summary": "Login bug",
  "description": "Users cannot log in",
  "status": "Open",
  "priority": "High",
  "assignee": "john.doe",
  "type": "Bug",
  "comments": [...],
  "attachments": [...]
}
```

**Search Results:**
```json
[
  {
    "key": "TEST-123",
    "summary": "Issue 1",
    "status": "Open",
    "priority": "High",
    "assignee": "user@example.com",
    "type": "Bug"
  },
  ...
]
```

**Create Issue:**
```json
{
  "key": "TEST-789",
  "id": "12345",
  "self": "https://your-domain.atlassian.net/rest/api/2/issue/12345"
}
```
