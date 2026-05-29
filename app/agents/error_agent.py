from agents.ai_agent import ask_ai
from prompts.error_prompts import get_error_fix_prompt


def run_error_agent(table_name: str, error: str, sql: str = "") -> dict:
    """
    Subagent: error_agent
    Responsibility: Analyse errors and suggest fixes
    Input: table_name, error, sql (optional)
    Output: {status, table, suggestion, skill_used}
    """
    print(f"\n[Error Agent] Analysing error for '{table_name}'...")
    prompt = get_error_fix_prompt(table_name, error, sql)
    suggestion = ask_ai(prompt, skill_name="error_recovery")
    return {
        "status": "analysed",
        "table": table_name,
        "suggestion": suggestion,
        "skill_used": "error_recovery"
    }