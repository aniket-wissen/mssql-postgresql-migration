def get_error_fix_prompt(table_name: str, error: str, sql: str = "") -> str:
    return f"""
You are a database migration error recovery expert.
A migration step failed for table '{table_name}'.

Error:
{error}

{f"Failed SQL: {sql}" if sql else ""}

Your job:
1. Identify the root cause of the error
2. Suggest a specific technical fix
3. If possible, provide the corrected SQL

Be concise and technical. No lengthy explanations.
"""