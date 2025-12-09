"""
Test client for MCP Server - calls tools and displays results.

Run with: uv run python -m src.test_mcp_client
"""

import asyncio
import json

from mcp import ClientSession
from mcp.client.sse import sse_client


async def test_mcp_server():
    """Connect to the MCP server and test the tools."""
    server_url = "http://localhost:8000/sse"

    print(f"Connecting to MCP server at {server_url}...")
    print("=" * 60)

    async with sse_client(server_url) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # List available tools
            print("\n📦 Available Tools:")
            print("-" * 40)
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  • {tool.name}: {tool.description[:60]}...")

            # Test get_metadata
            print("\n" + "=" * 60)
            print("🔍 Testing: get_metadata")
            print("-" * 40)

            result = await session.call_tool("get_metadata", {"database_name": "default"})
            if result.content:
                data = json.loads(result.content[0].text)
                if "error" in data:
                    print(f"❌ Error: {data['error']}")
                else:
                    print(f"Schema: {data.get('schema')}")
                    tables = data.get("tables", [])
                    print(f"Tables found: {len(tables)}")
                    for table in tables[:3]:  # Show first 3 tables
                        print(f"\n  📋 {table['name']}")
                        if table.get("comment"):
                            print(f"     Comment: {table['comment']}")
                        for col in table.get("columns", [])[:3]:  # Show first 3 columns
                            nullable = "NULL" if col.get("nullable") else "NOT NULL"
                            comment = f" -- {col['comment']}" if col.get("comment") else ""
                            print(f"       • {col['name']}: {col['type']} {nullable}{comment}")
                        if len(table.get("columns", [])) > 3:
                            print(f"       ... and {len(table['columns']) - 3} more columns")
                    if len(tables) > 3:
                        print(f"\n  ... and {len(tables) - 3} more tables")

            # Test execute_sql
            print("\n" + "=" * 60)
            print("🔍 Testing: execute_sql (SELECT query)")
            print("-" * 40)

            result = await session.call_tool(
                "execute_sql",
                {"query": "SELECT SYSDATE as current_time, USER as db_user FROM DUAL"},
            )
            if result.content:
                data = json.loads(result.content[0].text)
                if data.get("success"):
                    print(f"✅ Success! Rows returned: {data.get('row_count')}")
                    print(f"Columns: {data.get('columns')}")
                    for row in data.get("rows", []):
                        print(f"  → {row}")
                else:
                    print(f"❌ Error: {data.get('error')}")

            # Test execute_sql with EMPLOYEES table
            print("\n" + "=" * 60)
            print("🔍 Testing: execute_sql (EMPLOYEES query)")
            print("-" * 40)

            result = await session.call_tool(
                "execute_sql",
                {"query": "SELECT EMPNO, ENAME, JOB, SAL FROM EMPLOYEES WHERE ROWNUM <= 5 ORDER BY SAL DESC"},
            )
            if result.content:
                data = json.loads(result.content[0].text)
                if data.get("success"):
                    print(f"✅ Success! Rows returned: {data.get('row_count')}")
                    print(f"Columns: {data.get('columns')}")
                    for row in data.get("rows", []):
                        print(f"  → {row}")
                else:
                    print(f"❌ Error: {data.get('error')}")

            print("\n" + "=" * 60)
            print("✅ All tests completed!")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mcp_server())

