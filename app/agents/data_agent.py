from agents.ai_agent import ask_ai
from db.source_reader import extract_table_data
from prompts.data_prompts import get_insert_prompt
from skills.sql_skills import clean_sql, extract_column_names, validate_sql
from skills.db_skills import insert_rows


def run_data_agent(table_name: str, columns: list) -> dict:
    """
    Subagent: data_agent
    Responsibility: Migrate data from MSSQL to PostgreSQL
    Input: table_name, columns
    Output: {status, table, rows_migrated, sql_generated, skill_used, error}
    """
    print(f"\n[Data Agent] Starting for '{table_name}'...")
    result = {
        "status": "failed",
        "table": table_name,
        "rows_migrated": 0,
        "sql_generated": None,
        "skill_used": "data_insert_generation",
        "error": None
    }

    # Skill: extract data from source
    rows = extract_table_data(table_name)
    if not rows:
        print(f"[Data Agent] No data found for '{table_name}'")
        result["status"] = "success"
        result["rows_migrated"] = 0
        return result

    # Skill: extract column names
    col_result = extract_column_names(columns)
    column_names = col_result["column_names"]

    # Prompt: get insert prompt
    prompt = get_insert_prompt(table_name, column_names)

    # AI: generate INSERT statement
    raw_sql = ask_ai(prompt, skill_name="data_insert_generation")

    # Skill: clean SQL
    clean_result = clean_sql(raw_sql)
    insert_sql = clean_result["cleaned_sql"]

    # Skill: validate SQL
    validation = validate_sql(insert_sql)
    if not validation["is_valid"]:
        result["error"] = f"AI returned invalid SQL: {validation['reason']}"
        print(f"[Data Agent] FAILED — {result['error']}")
        return result

    print(f"[Data Agent] AI Generated INSERT:\n{insert_sql}")
    result["sql_generated"] = insert_sql

    # Skill: insert rows
    try:
        insert_rows(insert_sql, rows)
        result["status"] = "success"
        result["rows_migrated"] = len(rows)
        print(f"[Data Agent] SUCCESS — {len(rows)} rows migrated")
    except Exception as e:
        result["error"] = str(e)
        print(f"[Data Agent] FAILED — {e}")

    return result