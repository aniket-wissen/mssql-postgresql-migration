import json
from agents.ai_agent import ask_ai
from db.source_reader import extract_tables, extract_columns
from agents.schema_agent import run_schema_agent
from agents.data_agent import run_data_agent
from agents.error_agent import run_error_agent
from validator import validate_table
from prompts.validation_prompts import get_final_summary_prompt
from prompts.orchestrator_prompts import get_migration_order_prompt
from skills.report_skills import save_report, format_separator


def decide_migration_order(tables: list) -> list:
    table_names = [t["TABLE_NAME"] for t in tables]
    prompt = get_migration_order_prompt(table_names)
    response = ask_ai(prompt, skill_name="migration_order_planning")
    start = response.find("[")
    end = response.rfind("]") + 1
    ordered = json.loads(response[start:end])
    print(f"\n[Orchestrator] AI decided migration order: {ordered}")
    return ordered


def run_migration():
    print(format_separator("AI-POWERED MIGRATION PIPELINE STARTING"))
    print("\n[Orchestrator] Fetching tables from source...")

    tables = extract_tables()
    ordered_tables = decide_migration_order(tables)
    migration_summary = []

    for table_name in ordered_tables:
        print(format_separator(f"Processing: {table_name}"))

        result = {
            "table": table_name,
            "schema": None,
            "data": None,
            "validation": None,
            "error": None
        }

        # Step 1 — Schema Agent
        schema_result = run_schema_agent(table_name, extract_columns(table_name))
        result["schema"] = schema_result

        if schema_result["status"] != "success":
            error_result = run_error_agent(table_name, schema_result["error"])
            result["error"] = error_result
            print(f"\n[Error Agent] Suggestion: {error_result['suggestion']}")
            migration_summary.append(result)
            continue

        # Step 2 — Data Agent
        data_result = run_data_agent(table_name, extract_columns(table_name))
        result["data"] = data_result

        if data_result["status"] != "success":
            error_result = run_error_agent(table_name, data_result["error"])
            result["error"] = error_result
            print(f"\n[Error Agent] Suggestion: {error_result['suggestion']}")

        # Step 3 — Validator
        validation_result = validate_table(table_name)
        result["validation"] = validation_result

        migration_summary.append(result)

    # Final AI Summary
    print(format_separator("MIGRATION COMPLETE — AI SUMMARY"))
    final_report = ask_ai(
        get_final_summary_prompt(migration_summary),
        skill_name="final_summary"
    )
    print(final_report)
    save_report(final_report)


if __name__ == "__main__":
    run_migration()