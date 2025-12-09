# MCP Inspector Guide

## Overview

The MCP Inspector is a browser-based tool for testing and debugging MCP servers. It provides an interactive interface to test tools, resources, prompts, and monitor server communications.

## Installation

✅ Already installed! Node.js, npm, and npx are set up on your Mac.

## Running the Inspector

### Basic Usage (Opens Browser Interface)

```bash
npx @modelcontextprotocol/inspector
```

This will:
- Start a local web server
- Automatically open your default browser
- Display the Inspector interface

### Connecting to Local MCP Servers

#### Option 1: SSE Transport (HTTP-based servers)

If your MCP server runs with SSE transport (like your FastMCP server):

```bash
# Terminal 1: Start your MCP server
python -m src.mcp_server

# Terminal 2: Connect Inspector to your server
npx @modelcontextprotocol/inspector --transport sse --server-url http://localhost:8000/sse
```

#### Option 2: HTTP Transport

For HTTP-based MCP servers:

```bash
npx @modelcontextprotocol/inspector --transport http --server-url http://localhost:8000
```

#### Option 3: stdio Transport (for local development)

For servers that use standard input/output:

```bash
npx @modelcontextprotocol/inspector python src/mcp_server.py
```

### Connecting to Remote MCP Servers

#### SSE Transport (over internet)

```bash
npx @modelcontextprotocol/inspector \
  --transport sse \
  --server-url https://your-server.com:8000/sse
```

#### HTTP Transport (over internet)

```bash
npx @modelcontextprotocol/inspector \
  --transport http \
  --server-url https://your-server.com:8000
```

#### With Authentication Headers

If your server requires authentication:

```bash
npx @modelcontextprotocol/inspector \
  --transport sse \
  --server-url https://your-server.com:8000/sse \
  --header "Authorization: Bearer your-token-here" \
  --header "X-API-Key: your-api-key"
```

## Inspector Features

Once connected, the Inspector provides:

### 1. **Server Connection Pane**
- Select transport type
- Configure connection settings
- Customize command-line arguments and environment variables

### 2. **Resources Tab**
- List all available resources
- View resource metadata (MIME types, descriptions)
- Inspect resource content
- Test resource subscriptions

### 3. **Prompts Tab**
- View available prompt templates
- See prompt arguments and descriptions
- Test prompts with custom arguments
- Preview generated messages

### 4. **Tools Tab**
- List all available tools
- View tool schemas and descriptions
- Test tools with custom inputs
- View tool execution results

### 5. **Notifications Pane**
- View all server logs
- Monitor notifications from the server
- Debug communication issues

## Example: Testing Your Oracle Database MCP Server

### Step 1: Start your MCP server

```bash
# Make sure your .env file has the required variables:
# ORACLE_DB_DSN=...
# ORACLE_DB_PASSWORD=...
# ORACLE_DB_USER=ADMIN

python -m src.mcp_server
```

The server will start on `http://localhost:8000` (or the port specified in `MCP_PORT` env var).

### Step 2: Connect Inspector

```bash
npx @modelcontextprotocol/inspector \
  --transport sse \
  --server-url http://localhost:8000/sse
```

### Step 3: Test in Browser

1. The Inspector will open in your browser
2. Navigate to the **Tools** tab
3. Test `get_metadata` tool to see your database schema
4. Test `execute_sql` tool with queries like:
   - `SELECT * FROM EMPLOYEES`
   - `SELECT table_name FROM user_tables`

## Troubleshooting

### Inspector doesn't open browser automatically

The Inspector typically runs on `http://localhost:3000` or similar. Check the terminal output for the exact URL, or try:
- `http://localhost:3000`
- `http://localhost:8080`
- `http://localhost:6274` (check with `lsof -i -P | grep node`)

### Connection refused

- Ensure your MCP server is running
- Check the server URL and port
- Verify firewall settings for remote servers
- For SSE transport, ensure the path includes `/sse`

### CORS Issues (remote servers)

If connecting to a remote server, ensure:
- The server allows CORS from your origin
- Proper authentication headers are included
- The server is accessible from your network

## Advanced Usage

### Using Config Files

Create a config file for easier server management:

```json
{
  "servers": {
    "local-oracle": {
      "transport": "sse",
      "url": "http://localhost:8000/sse"
    },
    "remote-server": {
      "transport": "http",
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer token"
      }
    }
  }
}
```

Then use:
```bash
npx @modelcontextprotocol/inspector --config mcp-config.json --server local-oracle
```

### Environment Variables

Pass environment variables to stdio-based servers:

```bash
npx @modelcontextprotocol/inspector \
  -e "ORACLE_DB_DSN=your-dsn" \
  -e "ORACLE_DB_PASSWORD=your-password" \
  python src/mcp_server.py
```

## Resources

- [MCP Inspector Documentation](https://modelcontextprotocol.io/docs/tools/inspector)
- [MCP Inspector Repository](https://github.com/modelcontextprotocol/inspector)
- [MCP Debugging Guide](https://modelcontextprotocol.io/docs/debugging)

