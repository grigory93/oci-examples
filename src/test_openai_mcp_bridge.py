"""
OpenAI + MCP Bridge: Use OpenAI models with your MCP server

This script connects OpenAI's function calling to your MCP server.

Requirements:
- OpenAI API key in environment: OPENAI_API_KEY
- MCP server running at http://localhost:8000/sse

Usage:
    uv run python -m src.test_openai_mcp_bridge "Show me the database schema"
"""

import asyncio
import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# MCP Server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def get_mcp_tools_as_openai_functions() -> list[dict[str, Any]]:
    """Connect to MCP server and convert its tools to OpenAI function format."""
    async with sse_client(MCP_SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Get available tools from MCP server
            tools_response = await session.list_tools()
            
            # Convert MCP tools to OpenAI function format
            openai_functions: list[dict[str, Any]] = []
            for tool in tools_response.tools:
                function_def: dict[str, Any] = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or f"Call {tool.name}",
                        "parameters": tool.inputSchema if tool.inputSchema else {
                            "type": "object",
                            "properties": {},
                        }
                    }
                }
                openai_functions.append(function_def)
            
            return openai_functions


async def call_mcp_tool(tool_name: str, arguments: dict):
    """Call a tool on the MCP server."""
    async with sse_client(MCP_SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(tool_name, arguments)
            
            if result.content:
                # Extract text from result
                if isinstance(result.content, list) and len(result.content) > 0:
                    return getattr(result.content[0], 'text', str(result.content[0]))
                return str(result.content)
            return json.dumps({"error": "No content returned"})


async def chat_with_openai_and_mcp(user_message: str, model: str = "gpt-4o"):
    """
    Send a message to OpenAI, handle tool calls via MCP server, and return final response.
    """
    print(f"🤖 Using model: {model}")
    print(f"🔗 MCP Server: {MCP_SERVER_URL}")
    print("=" * 60)
    
    # Get MCP tools as OpenAI functions
    print("📦 Loading tools from MCP server...")
    tools: list[dict[str, Any]] = await get_mcp_tools_as_openai_functions()
    print(f"✅ Loaded {len(tools)} tools: {[t['function']['name'] for t in tools]}")
    print("=" * 60)
    
    # Initialize conversation
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are a helpful database assistant. You have access to tools to query "
                "an Oracle database. Use get_metadata to explore the schema and execute_sql "
                "to run queries. Always explain your results clearly."
            )
        },
        {"role": "user", "content": user_message}
    ]
    
    # Track iterations to prevent infinite loops
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n🔄 Iteration {iteration}")
        
        # Call OpenAI - only include tools parameter if tools are available
        create_kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if tools:
            create_kwargs["tools"] = tools
            create_kwargs["tool_choice"] = "auto"
        
        response = openai_client.chat.completions.create(**create_kwargs)
        
        assistant_message = response.choices[0].message
        messages.append(assistant_message)
        
        # Check if OpenAI wants to call a tool
        if assistant_message.tool_calls:
            print(f"🔧 OpenAI requested {len(assistant_message.tool_calls)} tool call(s)")
            
            # Execute each tool call via MCP
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"   → Calling {function_name}({function_args})")
                
                # Call MCP server
                tool_result = await call_mcp_tool(function_name, function_args)
                
                print(f"   ✅ Got result ({len(tool_result)} chars)")
                
                # Add tool result to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": tool_result,
                })
        else:
            # No more tool calls, return final response
            final_response = assistant_message.content
            print("\n" + "=" * 60)
            print("💬 Final Response:")
            print("=" * 60)
            print(final_response)
            print("=" * 60)
            return final_response
    
    return "⚠️ Maximum iterations reached"


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExample queries:")
        print('  "What tables are in the database?"')
        print('  "Show me employees with salary > 3000"')
        print('  "Get the schema for the EMPLOYEES table"')
        sys.exit(1)
    
    user_query = " ".join(sys.argv[1:])
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY=sk-...")
        sys.exit(1)
    
    print(f"\n💭 User Query: {user_query}\n")
    
    try:
        await chat_with_openai_and_mcp(user_query)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

