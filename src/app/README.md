# AI Data Platform Chat - Streamlit App

A minimal, elegant chat interface for querying Oracle Autonomous Database using OpenAI models and MCP.

## Features

- 🤖 **Multiple OpenAI Models**: Choose from gpt-4o-mini, gpt-4.1, gpt-4o, gpt-5 variants
- 💬 **Streaming Responses**: Real-time response streaming for better UX
- 🔧 **MCP Tool Integration**: Automatically uses database tools (get_metadata, execute_sql)
- ✨ **Minimal Design**: Clean, distraction-free interface

## Quick Start

### 1. Ensure MCP Server is Running

```bash
# In one terminal
uv run python -m src.mcp_server
```

### 2. Launch the Chat App

```bash
# In another terminal
uv run streamlit run src/app/chat_app.py
```

The app will open in your browser at `http://localhost:8501`

On VM launch with 
```bash
uv run streamlit run src/app/chat_app.py --server.address 0.0.0.0 --server.port 8501
```
The app will open at `http://64.181.210.109:8501`

## Usage

1. **Select Model**: Choose your preferred OpenAI model from the dropdown
2. **Type Message**: Enter your question in the chat input
3. **View Response**: Watch the streaming response with tool calls displayed in expandable sections
4. **Clear History**: Use the "Clear" button to start fresh

## Example Queries

```
What tables are in the database?
Show me the top 5 highest paid employees
How many employees work in each department?
What is the schema of the EMPLOYEES table?
Find all orders from the last month
```

## Configuration

Set in your `.env` file:

```bash
# Required
OPENAI_API_KEY=sk-...
ORACLE_DB_DSN=...
ORACLE_DB_PASSWORD=...

# Optional
MCP_SERVER_URL=http://localhost:8000/sse  # default
```

## Architecture

```
User Input
    ↓
Streamlit UI
    ↓
chat_app.py
    ↓
mcp_chat.py (streaming logic)
    ↓
OpenAI Streaming API
    ↓
MCP Server (via SSE)
    ↓
Oracle Database
```

## Files

- **`chat_app.py`** - Main Streamlit application with UI
- **`mcp_chat.py`** - Chat logic with streaming and MCP integration
- **`__init__.py`** - Package initialization

## Troubleshooting

### "MCP Disconnected" Warning
- Check if MCP server is running: `ps aux | grep mcp_server`
- Verify MCP_SERVER_URL in .env
- Test connection: `curl http://localhost:8000/sse`

### OpenAI API Errors
- Verify OPENAI_API_KEY is set correctly
- Check API quota at https://platform.openai.com/
- Try a different model (some may not be available yet)

### Database Errors
- Ensure Oracle database credentials are correct
- Test with: `uv run python -m src.main test-tls-connection`

## Development

To modify the UI:
- Edit `chat_app.py` for layout and styling
- Edit `mcp_chat.py` for chat logic and streaming

The app automatically reloads when files change (Streamlit's hot reload).

