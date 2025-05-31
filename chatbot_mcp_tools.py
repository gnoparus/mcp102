from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List
import asyncio
import nest_asyncio
from loguru import logger

# Configure loguru
logger.add("chatbot.log", rotation="500 MB", level="INFO")

nest_asyncio.apply()
load_dotenv()

class MCP_ChatBot:
    def __init__(self):
        self.session: ClientSession = None
        self.anthropic = Anthropic()
        self.available_tools: List[dict] = []
        logger.info("MCP_ChatBot initialized")

    async def process_query(self, query):
        """
        Process a user query using Claude and execute any requested tools.
        """
        print("\n=== Starting New Query Processing ===")
        print(f"User Query: {query}")
        logger.info(f"Processing new query: {query}")
        
        messages = [{'role': 'user', 'content': query}]
        max_iterations = 10
        iteration = 1

        try:
            while iteration <= max_iterations:
                logger.debug(f"Starting iteration {iteration}")
                print(f"\n--- Processing Iteration {iteration} ---")
                
                response = await self._get_claude_response(messages)
                should_continue = await self._process_content_blocks(response, messages)
                if not should_continue:
                    break
                    
                iteration += 1
                
            if iteration > max_iterations:
                logger.warning("Maximum iterations reached")
                print("\n⚠️ Maximum iterations reached - stopping processing")
                
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            print(f"\n❌ Error processing query: {str(e)}")
            raise

    async def _get_claude_response(self, messages):
        """Get response from Claude API with error handling."""
        try:
            logger.info("Sending request to Claude")
            print("\nSending request to Claude...")
            response = self.anthropic.messages.create(
                max_tokens=2024,
                model='claude-3-7-sonnet-20250219',
                tools=self.available_tools,
                messages=messages
            )
            logger.info(f"Claude response received: {response.id}")
            print(f"\n📨 Response received (ID: {response.id}, Blocks: {len(response.content)})")
            return response
        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            print(f"\n❌ Claude API error: {str(e)}")
            raise

    async def _process_content_blocks(self, response, messages):
        """Process content blocks from Claude's response. Returns True if processing should continue."""
        for content in response.content:
            if content.type == 'text':
                logger.info("Processing text response")
                print("\n🤖 Claude's Response:")
                print("-" * 50)
                print(content.text)
                print("-" * 50)
                
                if len(response.content) == 1:
                    logger.info("Query processing complete")
                    print("\n✅ Query processing complete")
                    return False
                    
            elif content.type == 'tool_use':
                logger.info(f"Executing tool: {content.name}")
                print("\n🛠️ Executing Tool:")
                print(f"Name: {content.name}")
                print(f"Arguments: {content.input}")
                
                try:
                    result = await self.session.call_tool(content.name, arguments=content.input)
                    
                    messages.extend([
                        {'role': 'assistant', 'content': [content]},
                        {'role': 'user', 'content': [{
                            'type': 'tool_result',
                            'tool_use_id': content.id,
                            'content': result.content
                        }]}
                    ])
                    
                    logger.info("Tool execution successful")
                    print(f"\n📊 Tool execution successful")
                    return True
                    
                except Exception as e:
                    logger.error(f"Tool execution failed: {str(e)}")
                    print(f"\n❌ Tool execution failed: {str(e)}")
                    raise
                    
        return False
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        logger.info("Starting chat loop")
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
        
                if query.lower() == 'quit':
                    logger.info("Chat loop terminated by user")
                    break
                    
                await self.process_query(query)
                print("\n")
                    
            except Exception as e:
                logger.error(f"Error in chat loop: {str(e)}")
                print(f"\nError: {str(e)}")
    
    async def connect_to_server_and_run(self):
        logger.info("Connecting to server")
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "research_mcp_server.py"],
            env=None,
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await session.initialize()
                
                response = await session.list_tools()
                tools = response.tools
                
                logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")
                print("\nConnected to server with tools:", [tool.name for tool in tools])
                
                self.available_tools = [{
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                } for tool in response.tools]
    
                await self.chat_loop()

async def main():
    logger.info("Starting MCP Chatbot")
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()

if __name__ == "__main__":
    asyncio.run(main())