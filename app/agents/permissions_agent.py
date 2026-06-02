from agents.ai_agent import ask_ai
from db.permissions_extractor import extract_all_permissions
from prompts.permissions_prompts import get_permissions_conversion_prompt
from skills.sql_skills import clean_sql, validate_sql
from skills.report_skills import save_table_report
from mcps.postgres_client import mcp_postgres


def run_permissions_agent() -> dict:
    """
    Subagent: permissions_agent
    Uses MCP server for all PostgreSQL permission operations.
    """
    print("\n[Permissions Agent] Starting permissions migration...")

    result = {
        "status": "failed",
        "statements_applied": 0,
        "statements": [],
        "error": None
    }

    # Step 1 — Extract all permissions from MSSQL
    permissions_data = extract_all_permissions()

    if not permissions_data["users"] and not permissions_data["roles"]:
        print("[Permissions Agent] No users or roles found — skipping")
        result["status"] = "skipped"
        return result

    # Step 2 — AI converts to PostgreSQL syntax
    prompt = get_permissions_conversion_prompt(permissions_data)
    raw_sql = ask_ai(prompt, skill_name="permissions_conversion")
    clean_result = clean_sql(raw_sql)
    pg_sql = clean_result["cleaned_sql"]

    print(f"\n[Permissions Agent] AI Generated SQL:\n{pg_sql}")
    
    # Step 3 — AI self-reviews its own output to catch mistakes
    review_prompt = f"""
    Review these PostgreSQL SQL statements for syntax errors.
    Fix any issues you find — especially spacing in GRANT statements.
    Return ONLY the corrected SQL statements, no explanation.

    {pg_sql}
    """
    reviewed = ask_ai(review_prompt, skill_name="permissions_self_review")
    clean_reviewed = clean_sql(reviewed)
    pg_sql = clean_reviewed["cleaned_sql"]

    print(f"\n[Permissions Agent] AI Self-Reviewed SQL:\n{pg_sql}")

    statements = [s.strip() for s in pg_sql.split(";") if s.strip()]

    applied = 0
    failed = []

    for statement in statements:
        validation = validate_sql(statement)
        if not validation["is_valid"]:
            print(f"[Permissions Agent] Skipping invalid: {statement[:50]}")
            continue

        # Use MCP server for all permission operations
        result_msg = mcp_postgres.execute_sql(statement)

        if "ERROR" in str(result_msg):
            error_lower = result_msg.lower()
            if "already exists" in error_lower or "already a member" in error_lower:
                print(f"[Permissions Agent] Skipped (already exists): {statement[:60]}...")
                applied += 1
            else:
                print(f"[Permissions Agent] Failed: {result_msg}")
                failed.append({"statement": statement, "error": result_msg})
        else:
            print(f"[Permissions Agent] Applied: {statement[:60]}...")
            applied += 1

    result["status"] = "success" if applied > 0 else "failed"
    result["statements_applied"] = applied
    result["statements"] = statements
    result["failed"] = failed

    # Step 4 — Save report
    report = f"""
Permissions Migration Report
============================
Statements Applied: {applied}
Statements Failed: {len(failed)}
Status: {"PASS" if applied > 0 else "FAIL"}

Applied Statements:
{pg_sql}

Failed:
{failed}
"""
    save_table_report("permissions", report)

    print(f"\n[Permissions Agent] Done — {applied} statements applied, {len(failed)} failed")
    return result