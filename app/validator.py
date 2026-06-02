from agents.ai_agent import ask_ai
from prompts.validation_prompts import get_validation_prompt
from skills.report_skills import save_table_report
from db.source_reader import get_connection as source_connection
from mcps.postgres_client import mcp_postgres


def get_source_count(table_name: str) -> int:
    """
    WHY DIRECT: Source is MSSQL — MCP server only covers PostgreSQL.
    """
    conn = source_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def validate_table(table_name: str) -> dict:
    """
    Subagent: validator
    Source count — direct pymssql
    Target count — via MCP PostgreSQL server
    """
    print(f"\n[Validator] Validating '{table_name}'...")

    # Source — direct pymssql connection
    source_count = get_source_count(table_name)
    print(f"    [Validator] Source count: {source_count}")

    # Target — via MCP server
    target_count = mcp_postgres.get_row_count(table_name)
    print(f"    [Validator] Target count: {target_count}")

    match = source_count == target_count

    report = {
        "table": table_name,
        "source_count": source_count,
        "target_count": target_count,
        "match": match
    }

    # Prompt: get validation prompt
    prompt = get_validation_prompt(report)

    # AI: generate validation summary
    ai_summary = ask_ai(prompt, skill_name="validation_report")

    print(f"\n--- AI Validation Report for {table_name} ---")
    print(ai_summary)
    print("----------------------------------------------")

    # Skill: save report
    save_table_report(table_name, ai_summary)

    return {
        "status": "pass" if match else "fail",
        "table": table_name,
        "source_count": source_count,
        "target_count": target_count,
        "match": match,
        "ai_summary": ai_summary,
        "skill_used": "validation_report"
    }