import os

from dotenv import load_dotenv

load_dotenv()

MSSQL_CONFIG = {
    "server": os.getenv("MSSQL_HOST"),
    "port": int(os.getenv("MSSQL_PORT")),
    "user": os.getenv("MSSQL_USER"),
    "password": os.getenv("MSSQL_PASSWORD"),
    "database": os.getenv("MSSQL_DATABASE")
}

POSTGRES_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "port": int(os.getenv("PG_PORT")),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "dbname": os.getenv("PG_DATABASE")
}