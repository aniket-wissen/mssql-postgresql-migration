def get_insert_prompt(table_name: str, column_names: list) -> str:
    return f"""
You are a PostgreSQL data migration expert.
Write a single PostgreSQL INSERT statement for the following table.

Table: {table_name}
Columns: {column_names}

Strict rules:
- Use %s as value placeholders
- Include ALL columns listed above
- Return ONLY the INSERT SQL, nothing else
- No markdown, no explanation, no code fences
- Example format: INSERT INTO my_table (col1, col2) VALUES (%s, %s)
"""