def get_migration_order_prompt(table_names: list) -> str:
    return f"""
You are a database migration expert.
Given these tables: {table_names}

Decide the best order to migrate them to avoid foreign key dependency issues.
Consider common patterns:
- Parent tables before child tables
- Lookup/reference tables first
- Tables with no dependencies first

Return ONLY a JSON array of table names in order.
Example: ["table1", "table2"]
Return nothing else. No explanation, no markdown.
"""