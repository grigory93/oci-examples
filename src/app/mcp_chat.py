"""
MCP Chat Logic - Refactored for Streamlit with streaming support

This module provides the chat functionality that connects OpenAI's streaming API
to the MCP server for database operations.
"""

import asyncio
import json
import os
from typing import Any, AsyncIterator, Optional

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI async client
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# System prompt for the database assistant
SYSTEM_PROMPT = """You are a helpful database assistant. You have access to tools to query an Oracle database. 

Use get_metadata to explore the schema and execute_sql to run queries. Always explain your results clearly and concisely."""


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


async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
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


async def chat_stream(
    messages: list[dict[str, Any]],
    model: str = "gpt-4o-mini",
    tools: Optional[list[dict[str, Any]]] = None,
    max_iterations: int = 5
) -> AsyncIterator[dict[str, Any]]:
    """
    Stream chat responses from OpenAI with MCP tool support.
    
    Yields:
        dict with keys:
            - type: "text" | "tool_call" | "tool_result" | "done" | "error"
            - content: the actual content
            - name: (for tool_call/tool_result) tool name
    """
    iteration = 0
    
    # Add system prompt if not present
    if not any(msg.get("role") == "system" for msg in messages):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    
    while iteration < max_iterations:
        iteration += 1
        
        # Prepare API call kwargs
        create_kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        
        if tools:
            create_kwargs["tools"] = tools
            create_kwargs["tool_choice"] = "auto"
        
        # Stream response from OpenAI
        stream = await openai_client.chat.completions.create(**create_kwargs)
        
        assistant_message_content = ""
        tool_calls_data = []
        current_tool_call = None
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            
            # Handle text content
            if delta.content:
                assistant_message_content += delta.content
                yield {
                    "type": "text",
                    "content": delta.content
                }
            
            # Handle tool calls
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    if tool_call_delta.index is not None:
                        # New tool call or existing one
                        while len(tool_calls_data) <= tool_call_delta.index:
                            tool_calls_data.append({
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            })
                        
                        current_tool_call = tool_calls_data[tool_call_delta.index]
                        
                        if tool_call_delta.id:
                            current_tool_call["id"] = tool_call_delta.id
                        
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                current_tool_call["function"]["name"] = tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                current_tool_call["function"]["arguments"] += tool_call_delta.function.arguments
        
        # Check if we have tool calls
        if tool_calls_data:
            # Construct assistant message with tool calls for history
            from openai.types.chat import ChatCompletionMessageToolCall
            from openai.types.chat.chat_completion_message_tool_call import Function
            
            tool_calls_objects = [
                ChatCompletionMessageToolCall(
                    id=tc["id"],
                    type="function",
                    function=Function(
                        name=tc["function"]["name"],
                        arguments=tc["function"]["arguments"]
                    )
                )
                for tc in tool_calls_data
            ]
            
            messages.append({
                "role": "assistant",
                "tool_calls": tool_calls_objects,
                "content": assistant_message_content or None
            })
            
            # Execute tool calls
            for tool_call in tool_calls_data:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])
                
                yield {
                    "type": "tool_call",
                    "name": function_name,
                    "arguments": function_args
                }
                
                # Call MCP tool
                tool_result = await call_mcp_tool(function_name, function_args)
                
                yield {
                    "type": "tool_result",
                    "name": function_name,
                    "content": tool_result[:500] + "..." if len(tool_result) > 500 else tool_result
                }
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": function_name,
                    "content": tool_result
                })
            
            # Continue loop to get final response
            continue
        else:
            # No tool calls, we're done
            if assistant_message_content:
                messages.append({
                    "role": "assistant",
                    "content": assistant_message_content
                })
            
            yield {"type": "done"}
            break
    
    if iteration >= max_iterations:
        yield {
            "type": "error",
            "content": "Maximum iterations reached"
        }

