def get_validation_prompt(report: dict) -> str:
    return f"""
You are a database migration validation specialist.
Review this migration report and produce a structured summary.

Report:
{report}

Your response must include:
- Status: PASS or FAIL
- Table name
- Source row count vs target row count
- Whether counts match
- One line reason if FAIL

Keep it concise and structured.
"""


def get_final_summary_prompt(migration_summary: list) -> str:
    return f"""
You are a migration project analyst.
Here is the full migration summary across all tables:

{migration_summary}

Write a final migration report covering:
- Tables successfully migrated (schema + data + validation)
- Tables that failed and exact reason
- Overall status: PASS or FAIL
- Any recommendations

Be concise, professional, and structured.
"""