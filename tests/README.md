# MCP JIRA Python Tests

This directory contains the test suite for the MCP JIRA Python server. The tests are organized into several categories to ensure comprehensive coverage of functionality.

## Test Files Overview

### Core Integration Tests

**test_jira_connection.py**
- Tests basic connectivity to JIRA
- Verifies authentication and configuration
- Checks network-related error handling

**test_jira_endpoints.py**
- Tests all endpoints used by server.py
- Verifies correct request/response handling
- Ensures proper parameter validation

**test_jira_mcp_integration.py**
- Integration tests that make actual server requests
- Tests the MCP server's handling of JIRA operations
- Verifies proper tool registration and discovery
- Tests the full request-response cycle through the MCP protocol

**test_jira_mcp_system.py**
- System-level tests focusing on user patterns
- Tests heavy usage scenarios and load handling
- Verifies system stability under various conditions

### Modular Tool Tests

**endpoint_tests/**
- Individual tests for each endpoint function
- Tests specific to the old monolithic structure

**unit_tests/**
- Unit tests for individual tool classes in the refactored structure
- Tests each tool in isolation with mocks
- Covers the new tools/ directory structure

## Running the Tests

To run the full test suite:
```bash
python -m unittest discover tests
```

To run specific test categories:
```bash
# Run integration tests
python -m unittest tests/test_jira_mcp_integration.py

# Run unit tests for refactored tools
python -m unittest discover tests/unit_tests

# Run endpoint tests
python -m unittest discover tests/endpoint_tests
```

## Environment Setup

The integration and system tests require proper JIRA credentials. Set these environment variables before running the tests:

```bash
export JIRA_HOST="your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
export JIRA_PROJECT_KEY="TEST"  # Project key for test issues
```

## Test Configuration

**conftest.py** sets up the Python path to ensure tests can import from the src/ directory. This file is essential for proper test execution.

## Test Coverage

The test suite covers:
- All JIRA API operations
- MCP protocol integration
- Error handling and edge cases
- Authentication and connectivity
- Tool registration and discovery
- Complex workflows and attachments

Run tests with coverage reporting:
```bash
python -m coverage run -m unittest discover tests
python -m coverage report
```