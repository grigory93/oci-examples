"""
Minimal MCP Server for Oracle Database Operations

Run with: python -m src.mcp_server
"""

import os
from typing import Any

import oracledb
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Database configuration from environment
DEFAULT_DSN = os.getenv("ORACLE_DB_DSN", "")
DEFAULT_USER = os.getenv("ORACLE_DB_USER", "ADMIN")
DEFAULT_PASSWORD = os.getenv("ORACLE_DB_PASSWORD", "")
WALLET_LOCATION = os.getenv("ORACLE_WALLET_LOCATION", "")
WALLET_PASSWORD = os.getenv("ORACLE_WALLET_PASSWORD", "")

# Initialize FastMCP server
mcp = FastMCP(
    name="Oracle Database MCP",
    instructions="""
    This MCP server provides access to an Oracle Autonomous Database.
    Use get_metadata to explore database schema (tables, columns, comments).
    Use execute_sql to run SQL queries against the database.
    """,
)


def get_connection() -> oracledb.Connection:
    """Create a database connection using environment configuration."""
    if not DEFAULT_DSN:
        raise ValueError("ORACLE_DB_DSN environment variable is required")
    if not DEFAULT_PASSWORD:
        raise ValueError("ORACLE_DB_PASSWORD environment variable is required")

    if WALLET_LOCATION:
        # mTLS connection with wallet
        return oracledb.connect(
            user=DEFAULT_USER,
            password=DEFAULT_PASSWORD,
            dsn=DEFAULT_DSN,
            config_dir=WALLET_LOCATION,
            wallet_location=WALLET_LOCATION,
            wallet_password=WALLET_PASSWORD,
        )
    else:
        # TLS connection without wallet
        return oracledb.connect(
            user=DEFAULT_USER,
            password=DEFAULT_PASSWORD,
            dsn=DEFAULT_DSN,
        )


def is_system_table(table_name: str) -> bool:
    """
    Check if a table name is an Oracle system/internal table.
    
    Args:
        table_name: The table name to check
        
    Returns:
        True if it's a system table, False otherwise
    """
    # List of system table patterns to exclude
    system_patterns = [
        "$",  # Tables with $ in name (e.g., CLOUD_INGEST_LOG$)
        "DR$",  # Oracle Text indexes
        "MLOG$",  # Materialized view logs
        "RUPD$",  # Updatable materialized views
        "SYS_",  # System tables
        "DBTOOLS$",  # Database tools tables
        "ORDS_",  # Oracle REST Data Services tables
        "APEX_",  # Oracle APEX tables
    ]
    
    # Check if table name contains or starts with any system pattern
    table_upper = table_name.upper()
    for pattern in system_patterns:
        if pattern in table_upper:
            return True
    
    return False


@mcp.tool
def get_metadata(database_name: str = "default") -> dict[str, Any]:
    """
    Get database schema metadata including tables, columns, data types, and comments.

    Args:
        database_name: Name of the database/schema to query (currently uses the
                      connected user's schema; parameter reserved for future multi-db support)

    Returns:
        Dictionary containing tables with their columns, data types, and comments
    """
    connection = None
    try:
        connection = get_connection()

        # Query to get tables with their comments
        tables_query = """
            SELECT t.table_name, tc.comments as table_comment
            FROM user_tables t
            LEFT JOIN user_tab_comments tc ON t.table_name = tc.table_name
            ORDER BY t.table_name
        """

        # Query to get columns with their comments
        columns_query = """
            SELECT 
                c.table_name,
                c.column_name,
                c.data_type,
                c.data_length,
                c.data_precision,
                c.data_scale,
                c.nullable,
                cc.comments as column_comment
            FROM user_tab_columns c
            LEFT JOIN user_col_comments cc 
                ON c.table_name = cc.table_name 
                AND c.column_name = cc.column_name
            ORDER BY c.table_name, c.column_id
        """

        tables_dict = {}
        cursor = connection.cursor()
        
        try:
            # Fetch tables (exclude system tables)
            cursor.execute(tables_query)
            for row in cursor.fetchall():
                table_name, table_comment = row
                # Skip system tables
                if is_system_table(table_name):
                    continue
                tables_dict[table_name] = {
                    "name": table_name,
                    "comment": table_comment,
                    "columns": [],
                }

            # Fetch columns (only for non-system tables)
            cursor.execute(columns_query)
            for row in cursor.fetchall():
                (
                    table_name,
                    column_name,
                    data_type,
                    data_length,
                    data_precision,
                    data_scale,
                    nullable,
                    column_comment,
                ) = row

                # Format the data type nicely
                if data_type in ("VARCHAR2", "CHAR", "NVARCHAR2", "NCHAR"):
                    type_str = f"{data_type}({data_length})"
                elif data_type == "NUMBER" and data_precision:
                    if data_scale:
                        type_str = f"NUMBER({data_precision},{data_scale})"
                    else:
                        type_str = f"NUMBER({data_precision})"
                else:
                    type_str = data_type

                if table_name in tables_dict:
                    tables_dict[table_name]["columns"].append(
                        {
                            "name": column_name,
                            "type": type_str,
                            "nullable": nullable == "Y",
                            "comment": column_comment,
                        }
                    )
        finally:
            cursor.close()

        return {
            "schema": DEFAULT_USER,
            "database_name": database_name,
            "tables": list(tables_dict.values()),
        }

    except oracledb.Error as e:
        (error,) = e.args
        return {"error": error.message, "error_code": error.code}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if connection:
            try:
                connection.close()
            except Exception:
                pass


@mcp.tool
def execute_sql(query: str, database_name: str = "default") -> dict[str, Any]:
    """
    Execute a SQL query against the Oracle database.

    Args:
        query: The SQL query to execute
        database_name: Name of the database/schema (reserved for future multi-db support)

    Returns:
        Dictionary containing columns and rows, or error information
    """
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        
        try:
            cursor.execute(query)

            # Check if this is a SELECT query (has results)
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()

                # Convert rows to list of dicts for better readability
                results = []
                for row in rows:
                    row_dict: dict[str, Any] = {}
                    for i, value in enumerate(row):
                        # Handle special types
                        if value is None:
                            row_dict[columns[i]] = ""
                        elif isinstance(value, (int, float, str, bool)):
                            row_dict[columns[i]] = value
                        else:
                            row_dict[columns[i]] = str(value)
                    results.append(row_dict)

                return {
                    "success": True,
                    "columns": columns,
                    "row_count": len(results),
                    "rows": results,
                }
            else:
                # DML statement (INSERT, UPDATE, DELETE)
                rowcount = cursor.rowcount
                connection.commit()
                return {
                    "success": True,
                    "rows_affected": rowcount,
                    "message": f"Statement executed successfully. {rowcount} row(s) affected.",
                }
        finally:
            cursor.close()

    except oracledb.Error as e:
        (error,) = e.args
        return {"success": False, "error": error.message, "error_code": error.code}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        if connection:
            try:
                connection.close()
            except Exception:
                pass


if __name__ == "__main__":
    # Run the server with SSE transport for remote access
    # Host 0.0.0.0 allows connections from any IP (needed for cloud VM)
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    mcp.run(transport="sse", host=host, port=port)

