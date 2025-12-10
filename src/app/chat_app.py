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

import altair as alt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Add parent directory to path to enable imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.app.mcp_chat import (
    analyze_data_for_visualization,
    chat_stream,
    get_mcp_tools_as_openai_functions,
)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Data Platform Chat",
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
    
    if "last_sql_result" not in st.session_state:
        st.session_state.last_sql_result = None
    
    if "show_chart" not in st.session_state:
        st.session_state.show_chart = False


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
    """Render minimal application header."""
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown("### Oracle Database Chat")
    
    with col2:
        if st.session_state.mcp_connected:
            st.caption("✅ MCP")
        else:
            st.caption("⚠️ MCP")


def render_controls():
    """Render controls near the chat input."""
    col1, col2, col3 = st.columns([3, 1, 1])
    
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
        if st.button("Clear", use_container_width=True, type="secondary"):
            st.session_state.messages = []
            st.session_state.last_sql_result = None
            st.session_state.show_chart = False
            st.rerun()
    
    with col3:
        st.caption(f"{len(st.session_state.messages)} msgs")


def create_chart(data: dict, viz_spec: dict) -> alt.Chart:
    """Create an Altair chart from data and visualization spec."""
    rows = data.get("rows", [])
    df = pd.DataFrame(rows)
    
    chart_type = viz_spec.get("type", "bar")
    x_field = viz_spec.get("x", {}).get("field")
    y_field = viz_spec.get("y", {}).get("field")
    x_label = viz_spec.get("x", {}).get("label", x_field)
    y_label = viz_spec.get("y", {}).get("label", y_field)
    title = viz_spec.get("title", "")
    
    # Ensure x_field is treated as nominal if it's not purely numeric
    x_type = "nominal"
    if df[x_field].dtype in ['int64', 'float64']:
        # Check if it looks like a category (few unique values)
        if df[x_field].nunique() > 10:
            x_type = "quantitative"
    
    if chart_type == "bar":
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(f"{x_field}:{x_type[0].upper()}", title=x_label, sort=None),
            y=alt.Y(f"{y_field}:Q", title=y_label),
            tooltip=[x_field, y_field]
        )
    elif chart_type == "line":
        chart = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X(f"{x_field}:Q", title=x_label),
            y=alt.Y(f"{y_field}:Q", title=y_label),
            tooltip=[x_field, y_field]
        )
    else:
        # Default to bar
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(f"{x_field}:N", title=x_label, sort=None),
            y=alt.Y(f"{y_field}:Q", title=y_label),
            tooltip=[x_field, y_field]
        )
    
    return chart.properties(
        title=title,
        width="container",
        height=300
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16
    )


def render_chat_history():
    """Render chat message history."""
    for i, message in enumerate(st.session_state.messages):
        role = message["role"]
        content = message.get("content", "")
        
        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)
        
        elif role == "assistant":
            with st.chat_message("assistant"):
                st.markdown(content)
                
                # Check if this message has associated data for visualization
                msg_data = message.get("sql_result")
                if msg_data and msg_data.get("rows"):
                    render_data_section(msg_data, key_suffix=f"history_{i}")


def render_data_section(data: dict, key_suffix: str = ""):
    """Render data table and optional visualization button."""
    rows = data.get("rows", [])
    
    if not rows:
        return
    
    # Show data as table
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Check if data is chartable
    viz_spec = analyze_data_for_visualization(data)
    
    if viz_spec:
        # Show visualize button
        button_key = f"viz_btn_{key_suffix}"
        chart_key = f"show_chart_{key_suffix}"
        
        # Initialize chart state for this specific message
        if chart_key not in st.session_state:
            st.session_state[chart_key] = False
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("📊 Visualize", key=button_key, use_container_width=True):
                st.session_state[chart_key] = not st.session_state[chart_key]
                st.rerun()
        
        # Show chart if toggled
        if st.session_state.get(chart_key, False):
            try:
                chart = create_chart(data, viz_spec)
                st.altair_chart(chart, use_container_width=True)
            except Exception as e:
                st.error(f"Could not create chart: {e}")


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
        data_container = st.container()
        
        full_response = ""
        last_sql_result = None
        
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
                        with st.expander(f"🔧 {tool_name}", expanded=False):
                            st.json(event["arguments"])
                
                elif event_type == "tool_result":
                    # Track SQL results
                    if event.get("data") and event["data"].get("success"):
                        last_sql_result = event["data"]
                
                elif event_type == "done":
                    # Finished streaming
                    response_placeholder.markdown(full_response)
                    
                    # Get SQL result from done event if available
                    if event.get("sql_result"):
                        last_sql_result = event["sql_result"]
                    
                    break
                
                elif event_type == "error":
                    st.error(event["content"])
                    return
            
            # Store the result and show data section
            if last_sql_result and last_sql_result.get("rows"):
                st.session_state.last_sql_result = last_sql_result
                with data_container:
                    render_data_section(last_sql_result, key_suffix="current")
            
            # Add assistant response to history with data
            if full_response:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "sql_result": last_sql_result
                })
        
        except Exception as e:
            st.error(f"Error: {e}")
            return


def main():
    """Main application entry point."""
    initialize_session_state()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OPENAI_API_KEY not found. Please set it in your .env file.")
        st.stop()
    
    # Load MCP tools if not already loaded
    if st.session_state.tools is None:
        with st.spinner("Connecting to MCP server..."):
            success = asyncio.run(load_mcp_tools())
            if not success:
                st.warning("Running without MCP tools. Check if the MCP server is running.")
    
    # Render UI - header at top
    render_header()
    
    # Chat history in the middle
    render_chat_history()
    
    # Controls and chat input at bottom
    # Use a container to keep controls close to input
    with st.container():
        render_controls()
        
        # Chat input
        user_input = st.chat_input("Ask about your database...")
        
        if user_input:
            asyncio.run(handle_user_message(user_input))
            st.rerun()


if __name__ == "__main__":
    main()
