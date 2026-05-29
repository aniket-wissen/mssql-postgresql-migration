import psycopg2

from config import POSTGRES_CONFIG


def get_connection():

    return psycopg2.connect(
        host=POSTGRES_CONFIG["host"],
        port=POSTGRES_CONFIG["port"],
        user=POSTGRES_CONFIG["user"],
        password=POSTGRES_CONFIG["password"],
        dbname=POSTGRES_CONFIG["dbname"]
    )


def execute_sql(sql):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(sql)

    conn.commit()

    cursor.close()

    conn.close()