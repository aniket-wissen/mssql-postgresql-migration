import pymssql

from config import MSSQL_CONFIG


def get_connection():

    return pymssql.connect(
        server=MSSQL_CONFIG["server"],
        port=MSSQL_CONFIG["port"],
        user=MSSQL_CONFIG["user"],
        password=MSSQL_CONFIG["password"],
        database=MSSQL_CONFIG["database"]
    )


def extract_tables():

    conn = get_connection()

    cursor = conn.cursor(as_dict=True)

    cursor.execute("""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE='BASE TABLE'
    """)

    tables = cursor.fetchall()

    conn.close()

    return tables


def extract_columns(table_name):

    conn = get_connection()

    cursor = conn.cursor(as_dict=True)

    cursor.execute(f"""
        SELECT
            COLUMN_NAME,
            DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
    """)

    columns = cursor.fetchall()

    conn.close()

    return columns


def extract_table_data(table_name):

    conn = get_connection()

    cursor = conn.cursor(as_dict=False)

    query = f"SELECT * FROM {table_name}"

    cursor.execute(query)

    rows = cursor.fetchall()

    conn.close()

    return rows