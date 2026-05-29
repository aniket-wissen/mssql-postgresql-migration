import os
from datetime import datetime


def save_report(content: str, filename: str = "migration_report.txt"):
    print(f"    [Skill: save_report] Saving report...")
    output_dir = os.path.join(os.path.dirname(__file__), "../../output")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"    [Skill: save_report] Saved to {filepath}")


def save_table_report(table_name: str, content: str):
    print(f"    [Skill: save_table_report] Saving report for '{table_name}'...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{table_name}_{timestamp}.txt"
    save_report(content, filename)


def format_separator(title: str = "") -> str:
    return f"\n{'='*50}\n  {title}\n{'='*50}" if title else f"\n{'='*50}"