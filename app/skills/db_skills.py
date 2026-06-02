from db.target_writer import get_connection
from mcps.postgres_client import mcp_postgres


def drop_table(table_name: str):
    """
    WHY MCP: Delegates DROP TABLE to MCP server.
    Single point of control for all DDL operations.
    """
    print(f"    [Skill: drop_table] Dropping '{table_name}' if exists...")
    result = mcp_postgres.execute_sql(f"DROP TABLE IF EXISTS {table_name} CASCADE")
    print(f"    [Skill: drop_table] {result}")


def create_table(create_sql: str):
    """
    WHY MCP: Delegates CREATE TABLE to MCP server.
    """
    print(f"    [Skill: create_table] Executing CREATE TABLE...")
    result = mcp_postgres.execute_sql(create_sql)
    print(f"    [Skill: create_table] {result}")


def insert_rows(insert_sql: str, rows: list):
    """
    WHY DIRECT: Bulk inserts use psycopg2 directly for performance.
    MCP HTTP overhead per row would be too slow for 1M rows.
    """
    print(f"    [Skill: insert_rows] Inserting {len(rows)} rows...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {insert_sql.split()[2]}")
    cursor.executemany(insert_sql, rows)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"    [Skill: insert_rows] Done")


def get_row_count(table_name: str, connection_fn=None) -> int:
    """
    WHY MCP: Simple read operation — perfect for MCP.
    No need for raw DB connection just to count rows.
    """
    print(f"    [Skill: get_row_count] Counting rows in '{table_name}'...")
    count = mcp_postgres.get_row_count(table_name)
    print(f"    [Skill: get_row_count] Count: {count}")
    return count