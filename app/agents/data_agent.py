from agents.ai_agent import ask_ai
from db.source_reader import extract_table_data
from prompts.data_prompts import get_insert_prompt
from skills.sql_skills import clean_sql, extract_column_names, validate_sql
from skills.db_skills import insert_rows
from skills.batch_skills import chunk_rows, throttle, log_batch_progress, calculate_batch_stats
from skills.checkpoint_skills import save_checkpoint, load_checkpoint, complete_checkpoint, clear_checkpoint
from skills.index_skills import drop_indexes, recreate_indexes, disable_triggers, enable_triggers

# Tables with rows above this threshold use batch migration
# Tables below this threshold use direct single-shot migration
BATCH_THRESHOLD = 10_000


def run_data_agent(table_name: str, columns: list) -> dict:
    """
    Subagent: data_agent
    Responsibility: Migrate data from MSSQL to PostgreSQL
    - Small tables (<10k rows): migrate in one shot
    - Large tables (>10k rows): migrate in batches with checkpointing
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
        "error": None,
    }

    # Check if already completed in a previous run
    checkpoint = load_checkpoint(table_name)
    if checkpoint and checkpoint.get("status") == "completed":
        # If target table is empty despite completed checkpoint
        # it means schema agent recreated the table — checkpoint is stale
        from skills.db_skills import get_row_count
        from db.target_writer import get_connection as tgt_conn
        target_count = get_row_count(table_name, tgt_conn)
        if target_count == 0:
            print(f"[Data Agent] Stale checkpoint detected — table is empty, clearing and remigrating")
            clear_checkpoint(table_name)
        else:
            print(f"[Data Agent] '{table_name}' already fully migrated — skipping")
            result["status"] = "skipped"
            result["rows_migrated"] = target_count
            return result

    # Extract all rows from source
    rows = extract_table_data(table_name)
    if not rows:
        print(f"[Data Agent] No data found for '{table_name}'")
        result["status"] = "success"
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

    total_rows = len(rows)

    # Route to batch or direct migration based on row count
    if total_rows > BATCH_THRESHOLD:
        print(
            f"[Data Agent] Large table detected ({total_rows} rows) — using batch migration"
        )
        return _batch_migrate(table_name, rows, insert_sql, result)
    else:
        print(
            f"[Data Agent] Small table detected ({total_rows} rows) — using direct migration"
        )
        return _direct_migrate(table_name, rows, insert_sql, result)


def _direct_migrate(table_name: str, rows: list, insert_sql: str, result: dict) -> dict:
    """
    Direct migration for small tables — single INSERT operation.
    No batching needed, faster for small datasets.
    """
    try:
        insert_rows(insert_sql, rows)
        result["status"] = "success"
        result["rows_migrated"] = len(rows)
        print(f"[Data Agent] SUCCESS — {len(rows)} rows migrated directly")
    except Exception as e:
        result["error"] = str(e)
        print(f"[Data Agent] FAILED — {e}")
    return result


def _batch_migrate(table_name: str, rows: list, insert_sql: str, result: dict) -> dict:
    """
    Batch migration for large tables.
    - Splits rows into chunks
    - Saves checkpoint after each batch
    - Resumes from last checkpoint if a previous run failed
    - Throttles between batches to reduce DB strain
    """
    total_rows = len(rows)

    # Calculate and display batch stats upfront
    stats = calculate_batch_stats(total_rows)
    total_batches = stats["total_batches"]

    # Check if a previous run left a checkpoint — resume from there
    checkpoint = load_checkpoint(table_name)
    start_batch = 0
    rows_migrated = 0

    if checkpoint and checkpoint["status"] == "in_progress":
        start_batch = checkpoint["last_completed_batch"]
        rows_migrated = checkpoint["rows_migrated"]
        print(f"[Data Agent] Resuming from batch {start_batch}/{total_batches}")

    # Split all rows into batches
    batches = chunk_rows(rows)

    try:
        # Drop indexes before migration for faster inserts
        saved_indexes = drop_indexes(table_name)
        disable_triggers(table_name)

        from db.target_writer import get_connection
        conn = get_connection()
        cursor = conn.cursor()

        if start_batch == 0:
            cursor.execute(f"DELETE FROM {table_name}")
            conn.commit()

        for i, batch in enumerate(batches):
            batch_number = i + 1
            if batch_number <= start_batch:
                continue
            cursor.executemany(insert_sql, batch)
            conn.commit()
            rows_migrated += len(batch)
            save_checkpoint(table_name, batch_number, total_batches, rows_migrated)
            log_batch_progress(batch_number, total_batches, rows_migrated, total_rows)
            throttle(batch_number, total_batches)

        cursor.close()
        conn.close()

        # Recreate indexes and re-enable triggers after migration
        recreate_indexes(saved_indexes)
        enable_triggers(table_name)
        complete_checkpoint(table_name, total_rows)

        result["status"] = "success"
        result["rows_migrated"] = rows_migrated
        print(f"[Data Agent] SUCCESS — {rows_migrated} rows migrated in {total_batches} batches")

    except Exception as e:
        # Re-enable triggers even if migration fails
        enable_triggers(table_name)
        result["error"] = str(e)
        print(f"[Data Agent] FAILED at batch — {e}")
        print(f"[Data Agent] Checkpoint saved — resume by running again")

    return result