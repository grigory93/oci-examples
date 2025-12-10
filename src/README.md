# MCP Server for Oracle Autonomous Database

This directory contains a complete MCP (Model Context Protocol) server implementation that exposes Oracle Autonomous Database operations to AI models like OpenAI's GPT-4o.

---

## 📦 Files Overview

| File | Purpose | Usage |
|------|---------|-------|
| **`mcp_server.py`** | FastMCP server with database tools | `uv run python -m src.mcp_server` |
| **`test_mcp_client.py`** | Direct MCP protocol test client | `uv run python -m src.test_mcp_client` |
| **`test_openai_mcp_bridge.py`** | OpenAI + MCP integration bridge | `uv run python -m src.test_openai_mcp_bridge "query"` |
| **`main.py`** | Original database CLI tool | `uv run python -m src.main --help` |
| **`test_python_access.py`** | Legacy database tests | - |

---

## 🚀 Quick Start

### 1. Start the MCP Server

```bash
# Make sure .env file has database credentials
uv run python -m src.mcp_server
```

Server runs on `http://0.0.0.0:8000/sse`

### 2. Query Your Database via OpenAI

```bash
# Set OPENAI_API_KEY in .env first
uv run python -m src.test_openai_mcp_bridge "What tables are in the database?"
uv run python -m src.test_openai_mcp_bridge "Show me employees with salary > 3000"
uv run python -m src.test_openai_mcp_bridge "Which employees earn more than average?"
```

### 3. Test MCP Server Directly (without OpenAI)

```bash
uv run python -m src.test_mcp_client
```

---

## 🛠️ MCP Server Features

### Tools Exposed

1. **`get_metadata(database_name)`**
   - Returns database schema: tables, columns, data types, Oracle comments
   - Automatically filters out system tables (CLOUD_INGEST_LOG$, DBTOOLS$EXECUTION_HISTORY, etc.)
   - Returns only user-created tables

2. **`execute_sql(query, database_name)`**
   - Executes SQL queries (SELECT, INSERT, UPDATE, DELETE)
   - Returns results as JSON
   - Handles Oracle-specific data types

### Configuration

Environment variables (set in `.env` file):

```bash
# Required for MCP server
ORACLE_DB_DSN="your_connection_string"
ORACLE_DB_PASSWORD="your_password"
ORACLE_DB_USER="ADMIN"  # optional, defaults to ADMIN

# Optional for wallet-based connections
ORACLE_WALLET_LOCATION="/path/to/wallet"
ORACLE_WALLET_PASSWORD="wallet_password"

# Required for OpenAI bridge
OPENAI_API_KEY="sk-..."

# Optional MCP server settings
MCP_HOST="0.0.0.0"  # defaults to 0.0.0.0
MCP_PORT="8000"     # defaults to 8000
MCP_SERVER_URL="http://localhost:8000/sse"  # for clients
```

---

## 🏗️ Architecture

```
User Query
    ↓
OpenAI API (gpt-4o)
    ↓ (Function Calling)
test_openai_mcp_bridge.py
    ↓ (MCP Protocol - HTTP/SSE)
mcp_server.py
    ↓ (oracledb - TLS/mTLS)
Oracle Autonomous Database
```

---

## ✅ What Works

### Database Tables Exposed
- **EMPLOYEES** (8 columns: EMPNO, ENAME, JOB, MGR, HIREDATE, SAL, COMM, DEPTNO)
- **GLOBALSUPERSTOREORDERS** (24 columns: order, customer, product, sales data)

### System Tables Filtered
- ❌ CLOUD_INGEST_LOG$
- ❌ DBTOOLS$EXECUTION_HISTORY
- ❌ All tables with `$`, `SYS_`, `ORDS_`, `APEX_` patterns

### OpenAI Capabilities
✅ Discovers MCP tools automatically  
✅ Generates valid Oracle SQL (including subqueries, aggregations, joins)  
✅ Multi-turn conversations (explores schema → writes SQL → formats results)  
✅ Natural language responses  

---

## 📊 Example Interactions

### Query 1: Schema Exploration
```bash
$ uv run python -m src.test_openai_mcp_bridge "What tables are in the database?"

→ OpenAI calls: get_metadata()
→ Response: Lists EMPLOYEES and GLOBALSUPERSTOREORDERS with full schema
```

### Query 2: Simple SQL
```bash
$ uv run python -m src.test_openai_mcp_bridge "Show me all employees"

→ OpenAI calls: get_metadata() → execute_sql("SELECT * FROM EMPLOYEES")
→ Response: Formatted list of 11 employees with details
```

### Query 3: Complex Query
```bash
$ uv run python -m src.test_openai_mcp_bridge "Which employees earn more than average?"

→ OpenAI calls: get_metadata() → execute_sql("SELECT ... WHERE SAL > (SELECT AVG(SAL)...)")
→ Response: 5 employees with salaries above $2,073 average
```

---

## 🌐 Cloud Deployment

### Deploy to VM

```bash
# 1. Copy project to cloud VM
scp -r oci-demo user@vm-ip:~/

# 2. SSH and setup
ssh user@vm-ip
cd oci-demo
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 3. Configure environment
cp env_example.txt .env
# Edit .env with your Oracle credentials

# 4. Run MCP server
uv run python -m src.mcp_server
# Server available at http://VM_IP:8000/sse
```

### Firewall Configuration
```bash
# Open port 8000 for MCP server
sudo ufw allow 8000/tcp
```

---

## 🔑 Design Decisions

- **Simplicity**: Prototype-focused, no authentication/rate limiting (add later if needed)
- **System table filtering**: Clean schema view for AI models
- **OpenAI Function Calling**: Bridge between OpenAI and MCP (OpenAI has no native MCP support yet)
- **SSE Transport**: Enables remote access from any HTTP client
- **Connection per request**: Simple approach, no pooling complexity

---

## 🧪 Testing

### Test MCP Server Directly
```bash
# Test metadata tool
uv run python -c "
from src.mcp_server import get_metadata
import json
print(json.dumps(get_metadata('default'), indent=2))
"

# Test SQL execution
uv run python -c "
from src.mcp_server import execute_sql
import json
print(json.dumps(execute_sql('SELECT COUNT(*) FROM EMPLOYEES'), indent=2))
"
```

### Test with MCP Client
```bash
uv run python -m src.test_mcp_client
```

### Test with OpenAI
```bash
uv run python -m src.test_openai_mcp_bridge "What is the current date in the database?"
```

---

## 📝 Development Notes

### Adding New Tools

To add a new MCP tool, edit `mcp_server.py`:

```python
@mcp.tool
def your_new_tool(param: str) -> dict[str, Any]:
    """Tool description for AI models."""
    # Your implementation
    return {"result": "data"}
```

Tools are automatically discovered by OpenAI bridge.

### Modifying System Table Filter

Edit the `is_system_table()` function in `mcp_server.py` to add/remove patterns:

```python
system_patterns = [
    "$",        # Tables with $ 
    "YOUR_PATTERN",  # Add your pattern
]
```

---

## 🐛 Troubleshooting

### MCP Server Won't Start
- Check `ORACLE_DB_DSN` and `ORACLE_DB_PASSWORD` in `.env`
- Verify database connectivity: `uv run python -m src.main test-tls-connection`

### OpenAI Bridge Returns Errors
- Verify `OPENAI_API_KEY` is set in `.env`
- Check MCP server is running: `curl http://localhost:8000/sse`
- Check API quota/billing at https://platform.openai.com/

### Connection Errors
- TLS vs mTLS: Ensure database allows TLS connections or set `ORACLE_WALLET_LOCATION`
- Firewall: Check port 8000 is accessible
- Network: Verify VM's public IP and security groups

---

## 📚 Additional Resources

- **FastMCP Documentation**: https://gofastmcp.com
- **Model Context Protocol Spec**: https://spec.modelcontextprotocol.io/
- **OpenAI Function Calling**: https://platform.openai.com/docs/guides/function-calling
- **Oracle python-oracledb**: https://python-oracledb.readthedocs.io/

---

## 📄 License

Part of the oci-demo project.

