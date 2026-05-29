import re


def clean_sql(sql: str) -> dict:
    """
    Skill: clean_sql
    Input: Raw AI generated SQL string
    Output: {cleaned_sql, was_dirty}
    """
    print(f"    [Skill: clean_sql] Running...")
    was_dirty = "```" in sql
    sql = re.sub(r"```sql|```", "", sql).strip()
    print(f"    [Skill: clean_sql] Cleaned: {was_dirty}")
    return {"cleaned_sql": sql, "was_dirty": was_dirty}


def build_schema_description(columns: list) -> dict:
    """
    Skill: build_schema_description
    Input: List of column dicts
    Output: {description, column_count}
    """
    print(f"    [Skill: build_schema_description] Running...")
    description = "\n".join([
        f"- {col['COLUMN_NAME']}: {col['DATA_TYPE']}"
        for col in columns
    ])
    print(f"    [Skill: build_schema_description] {len(columns)} columns processed")
    return {"description": description, "column_count": len(columns)}


def extract_column_names(columns: list) -> dict:
    """
    Skill: extract_column_names
    Input: List of column dicts
    Output: {column_names, count}
    """
    print(f"    [Skill: extract_column_names] Running...")
    names = [col["COLUMN_NAME"] for col in columns]
    print(f"    [Skill: extract_column_names] Found: {names}")
    return {"column_names": names, "count": len(names)}


def validate_sql(sql: str) -> dict:
    """
    Skill: validate_sql
    Input: SQL string
    Output: {is_valid, reason}
    """
    print(f"    [Skill: validate_sql] Running...")
    sql_upper = sql.upper().strip()
    valid_starts = ["CREATE", "INSERT", "SELECT", "DROP", "ALTER"]
    is_valid = any(sql_upper.startswith(kw) for kw in valid_starts)
    reason = "Valid SQL keyword found" if is_valid else "No valid SQL keyword at start"
    print(f"    [Skill: validate_sql] {reason}")
    return {"is_valid": is_valid, "reason": reason}