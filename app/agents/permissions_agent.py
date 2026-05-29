from agents.ai_agent import ask_ai
from db.permissions_extractor import extract_all_permissions
from prompts.permissions_prompts import get_permissions_conversion_prompt
from skills.sql_skills import clean_sql, validate_sql
from db.target_writer import execute_sql
from skills.report_skills import save_table_report


def run_permissions_agent() -> dict:
    """
    Subagent: permissions_agent
    Responsibility: Extract MSSQL users/roles/permissions and recreate in PostgreSQL
    Input: none — reads directly from source DB
    Output: {status, statements_applied, error}

    WHY WE NEED THIS:
    Schema and data migration alone is not enough for a production system.
    Without users, roles and permissions, no application or developer
    can access the migrated database with the correct access level.
    This agent ensures the entire access control structure is preserved.
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

    # Step 3 — Split into individual statements and apply
    statements = [s.strip() for s in pg_sql.split(";") if s.strip()]

    applied = 0
    failed = []

    for statement in statements:
        validation = validate_sql(statement)
        if not validation["is_valid"]:
            print(f"[Permissions Agent] Skipping invalid statement: {statement[:50]}")
            continue
        try:
            execute_sql(statement)
            print(f"[Permissions Agent] Applied: {statement[:60]}...")
            applied += 1
        except Exception as e:
            error_msg = str(e).lower()
            # Role already exists — not a real failure, safe to skip
            if "already exists" in error_msg:
                print(f"[Permissions Agent] Skipped (already exists): {statement[:60]}...")
                applied += 1
            # Permission already granted — safe to skip
            elif "already a member" in error_msg or "duplicate" in error_msg:
                print(f"[Permissions Agent] Skipped (already granted): {statement[:60]}...")
                applied += 1
            else:
                print(f"[Permissions Agent] Failed: {statement[:60]}... Error: {e}")
                failed.append({"statement": statement, "error": str(e)})

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