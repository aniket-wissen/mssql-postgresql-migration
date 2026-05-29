from agents.ai_agent import ask_ai
from prompts.schema_prompts import get_schema_conversion_prompt
from skills.sql_skills import clean_sql, build_schema_description, validate_sql
from skills.db_skills import drop_table, create_table


def run_schema_agent(table_name: str, columns: list) -> dict:
    """
    Subagent: schema_agent
    Responsibility: Convert and create table schema in PostgreSQL
    Input: table_name, columns
    Output: {status, table, sql_generated, skill_used, error}
    """
    print(f"\n[Schema Agent] Starting for '{table_name}'...")
    result = {
        "status": "failed",
        "table": table_name,
        "sql_generated": None,
        "skill_used": "schema_conversion",
        "error": None
    }

    # Skill: build schema description
    schema_result = build_schema_description(columns)

    # Prompt: get schema conversion prompt
    prompt = get_schema_conversion_prompt(
        table_name,
        schema_result["description"]
    )

    # AI: generate DDL
    raw_sql = ask_ai(prompt, skill_name="schema_conversion")

    # Skill: clean SQL
    clean_result = clean_sql(raw_sql)
    create_sql = clean_result["cleaned_sql"]

    # Skill: validate SQL
    validation = validate_sql(create_sql)
    if not validation["is_valid"]:
        result["error"] = f"AI returned invalid SQL: {validation['reason']}"
        print(f"[Schema Agent] FAILED — {result['error']}")
        return result

    print(f"\n[Schema Agent] AI Generated DDL:\n{create_sql}")
    result["sql_generated"] = create_sql

    # Skill: drop and create table
    try:
        drop_table(table_name)
        create_table(create_sql)
        result["status"] = "success"
        print(f"[Schema Agent] SUCCESS — '{table_name}' created")
    except Exception as e:
        result["error"] = str(e)
        print(f"[Schema Agent] FAILED — {e}")

    return result