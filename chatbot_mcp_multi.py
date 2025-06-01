from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List, Dict, TypedDict
from contextlib import AsyncExitStack
from loguru import logger
import json
import asyncio
import sys

# Configure loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add("mcp_chatbot.log", rotation="10 MB")

load_dotenv()

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

class MCPChatBot:  # Renamed to follow Python naming conventions
    def __init__(self):
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            
            await session.initialize()
            self.sessions.append(session)
            
            response = await session.list_tools()
            tools = response.tools
            logger.info(f"Connected to {server_name} with tools: {[t.name for t in tools]}")
            
            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
        except Exception as e:
            logger.error(f"Failed to connect to {server_name}: {e}")
            raise

    async def connect_to_servers(self) -> None:
        """Connect to all configured MCP servers."""
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            logger.info(f"Found {len(servers)} servers in configuration")
            
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            logger.error(f"Error loading server configuration: {e}")
            raise

    async def process_query(self, query: str) -> None:
        """Process a user query and handle tool interactions."""
        
        messages = [{'role': 'user', 'content': query}]
        process_query = True

        while process_query:
            response = await self._get_claude_response(messages)
            assistant_content = []

            for content in response.content:
                if content.type == 'text':
                    print("\nAssistant:", content.text)  # Clear output distinction
                    assistant_content.append(content)
                    if len(response.content) == 1:
                        process_query = False
                elif content.type == 'tool_use':
                    assistant_content.append(content)
                    messages.append({'role': 'assistant', 'content': assistant_content})
                    await self._handle_tool_call(content, messages)
                    if len(response.content) == 1 and response.content[0].type == "text":
                        print("\nAssistant:", response.content[0].text)
                        process_query = False

    async def _get_claude_response(self, messages):
        """Get response from Claude API."""
        return self.anthropic.messages.create(
            max_tokens=2024,
            model='claude-3-7-sonnet-20250219',
            tools=self.available_tools,
            messages=messages
        )

    async def _handle_tool_call(self, tool_content, messages):
        """Handle tool execution and response processing."""
        tool_name = tool_content.name
        tool_args = tool_content.input
        logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")

        session = self.tool_to_session[tool_name]
        result = await session.call_tool(tool_name, arguments=tool_args)
        
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_content.id,
                "content": result.content
            }]
        })

    async def chat_loop(self):
        """Run an interactive chat loop."""
        logger.info("MCP Chatbot Started!")
        print("\n=== MCP Chatbot Started! ===")
        print("Type your queries or 'quit' to exit.\n")
        
        while True:
            try:
                query = input("You: ").strip()
                if query.lower() == 'quit':
                    break
                logger.debug(f"Received query: {query}")
                await self.process_query(query)
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Cleanly close all resources."""
        logger.info("Cleaning up resources...")
        await self.exit_stack.aclose()

async def main():
    chatbot = MCPChatBot()
    try:
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())