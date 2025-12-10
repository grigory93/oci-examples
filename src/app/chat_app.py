"""
Oracle Database Chat - Streamlit Application

A minimal chat interface for querying Oracle databases via OpenAI and MCP.

Run with:
    streamlit run src/app/chat_app.py
"""

import asyncio
import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Add parent directory to path to enable imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.app.mcp_chat import chat_stream, get_mcp_tools_as_openai_functions

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Oracle Database Chat",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Available models
MODELS = [
    "gpt-4o-mini",
    "gpt-4.1",
    "gpt-4o",
    "gpt-4.1-mini",
    "gpt-5-mini",
    "gpt-5-nano",
    "gpt-4.1-nano"
]

DEFAULT_MODEL = "gpt-4.1-mini"


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "tools" not in st.session_state:
        st.session_state.tools = None
    
    if "model" not in st.session_state:
        st.session_state.model = DEFAULT_MODEL
    
    if "mcp_connected" not in st.session_state:
        st.session_state.mcp_connected = False


async def load_mcp_tools():
    """Load MCP tools asynchronously."""
    try:
        tools = await get_mcp_tools_as_openai_functions()
        st.session_state.tools = tools
        st.session_state.mcp_connected = True
        return True
    except Exception as e:
        st.error(f"Failed to connect to MCP server: {e}")
        st.session_state.mcp_connected = False
        return False


def render_header():
    """Render the application header."""
    st.title("💬 Oracle Database Chat")
    
    # Model selector in a compact row
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_model = st.selectbox(
            "Model",
            options=MODELS,
            index=MODELS.index(st.session_state.model) if st.session_state.model in MODELS else MODELS.index(DEFAULT_MODEL),
            label_visibility="collapsed",
            key="model_selector"
        )
        if selected_model != st.session_state.model:
            st.session_state.model = selected_model
    
    with col2:
        if st.session_state.mcp_connected:
            st.success("MCP Connected", icon="✅")
        else:
            st.warning("MCP Disconnected", icon="⚠️")
    
    with col3:
        if st.button("Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    st.divider()


def render_chat_history():
    """Render chat message history."""
    for message in st.session_state.messages:
        role = message["role"]
        content = message.get("content", "")
        
        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)
        
        elif role == "assistant":
            with st.chat_message("assistant"):
                st.markdown(content)
        
        elif role == "tool":
            # Show tool results in a compact expander
            tool_name = message.get("name", "tool")
            with st.chat_message("assistant"):
                with st.expander(f"🔧 {tool_name}", expanded=False):
                    st.code(content[:500] + "..." if len(content) > 500 else content, language="json")


async def handle_user_message(user_input: str):
    """Handle user message and stream response."""
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Prepare messages for API (excluding tool messages from display)
    api_messages = [
        msg for msg in st.session_state.messages
        if msg["role"] in ["user", "assistant", "system", "tool"]
    ]
    
    # Display assistant response with streaming
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        tool_calls_container = st.container()
        
        full_response = ""
        
        try:
            async for event in chat_stream(
                messages=api_messages,
                model=st.session_state.model,
                tools=st.session_state.tools
            ):
                event_type = event.get("type")
                
                if event_type == "text":
                    # Stream text content
                    full_response += event["content"]
                    response_placeholder.markdown(full_response + "▌")
                
                elif event_type == "tool_call":
                    # Show tool being called
                    tool_name = event["name"]
                    with tool_calls_container:
                        with st.expander(f"🔧 Calling {tool_name}...", expanded=False):
                            st.json(event["arguments"])
                
                elif event_type == "tool_result":
                    # Tool result already shown in expander
                    pass
                
                elif event_type == "done":
                    # Finished streaming
                    response_placeholder.markdown(full_response)
                    break
                
                elif event_type == "error":
                    st.error(event["content"])
                    return
            
            # Add assistant response to history
            if full_response:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response
                })
        
        except Exception as e:
            st.error(f"Error: {e}")
            return


def main():
    """Main application entry point."""
    initialize_session_state()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OPENAI_API_KEY not found in environment variables. Please set it in your .env file.")
        st.stop()
    
    # Load MCP tools if not already loaded
    if st.session_state.tools is None:
        with st.spinner("Connecting to MCP server..."):
            success = asyncio.run(load_mcp_tools())
            if not success:
                st.warning("Running without MCP tools. Check if the MCP server is running.")
    
    # Render UI
    render_header()
    render_chat_history()
    
    # Chat input
    user_input = st.chat_input("Ask about your database...")
    
    if user_input:
        asyncio.run(handle_user_message(user_input))
        st.rerun()


if __name__ == "__main__":
    main()

