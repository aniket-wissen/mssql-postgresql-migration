from db.target_writer import get_connection, execute_sql


def drop_table(table_name: str):
    print(f"    [Skill: drop_table] Dropping '{table_name}' if exists...")
    execute_sql(f"DROP TABLE IF EXISTS {table_name} CASCADE")
    print(f"    [Skill: drop_table] Done")


def create_table(create_sql: str):
    print(f"    [Skill: create_table] Executing CREATE TABLE...")
    execute_sql(create_sql)
    print(f"    [Skill: create_table] Done")


def insert_rows(insert_sql: str, rows: list):
    print(f"    [Skill: insert_rows] Inserting {len(rows)} rows...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {insert_sql.split()[2]}")
    cursor.executemany(insert_sql, rows)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"    [Skill: insert_rows] Done")


def get_row_count(table_name: str, connection_fn) -> int:
    print(f"    [Skill: get_row_count] Counting rows in '{table_name}'...")
    conn = connection_fn()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    conn.close()
    print(f"    [Skill: get_row_count] Count: {count}")
    return count