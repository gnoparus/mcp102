# Model Context Protocol (MCP) Project

## Overview
This project implements Model Context Protocol (MCP) for enhanced chatbot interactions and tool calling capabilities.

## Getting Started

### Prerequisites
- Python environment (recommended: use `uv` for dependency management)
- Node.js and npm
- MCP Inspector tool (`@modelcontextprotocol/inspector`)

### Installation
1. Clone the repository
2. Install dependencies:
```bash
uv pip install -r requirements.txt
npm install @modelcontextprotocol/inspector
```

## Development Guide

### Components

1. **Chatbot Tools Integration** (`chatbot_tools_calling.ipynb`)
    - Reference implementation for standard tools calling
    - Base implementation before MCP refactoring

2. **MCP Server** (`research_mcp_server.py`)
    - MCP server implementation
    - Run with:
    ```bash
    npx @modelcontextprotocol/inspector uv run research_mcp_server.py
    ```

3. **MCP Tools** (`chatbot_mcp_tools.py`)
    - Tool integration with Research MCP Server from previous topic
    - Run with:
    ```bash
    uv run chatbot_mcp_tools.py
    ```

4. **MCP Multi-Server Tools** (`chatbot_mcp_multi.py`)
    - Multiple MCP server integration examples
    - Includes fetch and filesystem reference implementations
    - Run with:
    ```bash
    uv run chatbot_mcp_multi.py
    ```

5. **MCP Tools, Resources, and Prompts** (`chatbot_mcp_full.py`)
    - Complete implementation with integrated tools
    - Resource management and prompt handling
    - Enhanced context management
    - Run with:
    ```bash
    uv run chatbot_mcp_full.py
    ```

### Adding Resources
To extend the server with new resources and prompts:
1. Add resource files to appropriate directories
2. Update server configuration
3. Run server with:
```bash
npx @modelcontextprotocol/inspector uv run research_mcp_server.py
```

## Contributing
Please refer to our contribution guidelines before submitting PRs.
