from agents.ai_agent import ask_ai
from prompts.validation_prompts import get_validation_prompt
from skills.db_skills import get_row_count
from skills.report_skills import save_table_report
from db.source_reader import get_connection as source_connection
from db.target_writer import get_connection as target_connection


def validate_table(table_name: str) -> dict:
    """
    Subagent: validator
    Responsibility: Validate data migration correctness
    Input: table_name
    Output: {status, table, source_count, target_count, match, ai_summary, skill_used}
    """
    print(f"\n[Validator] Validating '{table_name}'...")

    # Skill: get row counts
    source_count = get_row_count(table_name, source_connection)
    target_count = get_row_count(table_name, target_connection)
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