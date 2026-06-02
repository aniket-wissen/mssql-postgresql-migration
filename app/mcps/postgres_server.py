import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastmcp import FastMCP
from db.target_writer import get_connection
from config import POSTGRES_CONFIG

# Initialize FastMCP server
mcp = FastMCP("PostgreSQL Migration Server")


@mcp.tool()
def execute_sql(sql: str) -> str:
    """
    Execute a SQL statement on PostgreSQL.
    Used for CREATE, DROP, INSERT, GRANT operations.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        return f"SUCCESS: {sql[:80]}"
    except Exception as e:
        return f"ERROR: {str(e)}"


@mcp.tool()
def query_sql(sql: str) -> str:
    """
    Run a SELECT query and return results from PostgreSQL.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        conn.close()
        return str({"columns": cols, "rows": rows, "count": len(rows)})
    except Exception as e:
        return f"ERROR: {str(e)}"


@mcp.tool()
def get_tables() -> str:
    """
    List all tables in the PostgreSQL database.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return str(tables)
    except Exception as e:
        return f"ERROR: {str(e)}"


@mcp.tool()
def get_table_schema(table_name: str) -> str:
    """
    Get column definitions for a specific table.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        columns = [{"column": row[0], "type": row[1]} for row in cursor.fetchall()]
        conn.close()
        return str(columns)
    except Exception as e:
        return f"ERROR: {str(e)}"


@mcp.tool()
def get_row_count(table_name: str) -> str:
    """
    Get the number of rows in a table.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        conn.close()
        return str(count)
    except Exception as e:
        return f"ERROR: {str(e)}"


@mcp.tool()
def get_roles() -> str:
    """
    List all roles and their memberships in PostgreSQL.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.rolname, r.rolcanlogin,
                   ARRAY(
                       SELECT m.rolname FROM pg_auth_members am
                       JOIN pg_roles m ON am.member = m.oid
                       WHERE am.roleid = r.oid
                   ) AS members
            FROM pg_roles r
            WHERE r.rolname NOT LIKE 'pg_%'
            AND r.rolname != 'postgres'
        """)
        roles = [{"role": row[0], "can_login": row[1], "members": list(row[2])} for row in cursor.fetchall()]
        conn.close()
        return str(roles)
    except Exception as e:
        return f"ERROR: {str(e)}"


# currently, mcp server will run on local
if __name__ == "__main__":
    print("Starting PostgreSQL MCP Server on http://127.0.0.1:8000")
    mcp.run(transport="http", host="127.0.0.1", port=8000)