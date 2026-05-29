def get_schema_conversion_prompt(table_name: str, schema_description: str) -> str:
    return f"""
You are an expert database schema migration engineer.
Your job is to convert SQL Server table definitions to PostgreSQL.

Table name: {table_name}
Columns:
{schema_description}

strict rules:
- Use PostgreSQL compatible data types only
- Use CREATE TABLE IF NOT EXISTS
- Map types correctly:
    INT -> INTEGER
    VARCHAR -> VARCHAR
    NVARCHAR -> VARCHAR
    DATETIME -> TIMESTAMP
    BIT -> BOOLEAN
    MONEY -> NUMERIC(19,4)
    FLOAT -> DOUBLE PRECISION
    TINYINT -> SMALLINT
    UNIQUEIDENTIFIER -> UUID
    VARBINARY -> BYTEA
    IMAGE -> BYTEA
- Return ONLY the raw SQL statement
- No markdown, no explanation, no code fences
"""