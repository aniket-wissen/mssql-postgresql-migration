import json
import os
from datetime import datetime

# Where checkpoint files are stored — one file per table
# This folder is created automatically if it doesn't exist
CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "../../output/checkpoints")


def _get_checkpoint_path(table_name: str) -> str:
    """Returns the file path for a table's checkpoint file."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    return os.path.join(CHECKPOINT_DIR, f"{table_name}_checkpoint.json")


def save_checkpoint(table_name: str, last_completed_batch: int, total_batches: int, rows_migrated: int):
    """
    Skill: save_checkpoint

    WHY WE USE THIS:
    When migrating 1 million rows in 100 batches, anything can go wrong
    mid-way — network drop, DB timeout, power cut, memory error.
    Without checkpointing, we would have to restart from batch 1 every time.
    With checkpointing, we save progress after every batch.
    If batch 47 fails, we resume from batch 47 — not from batch 1.
    This saves time, avoids duplicate data, and makes migration recoverable.
    """
    checkpoint = {
        "table_name": table_name,
        "last_completed_batch": last_completed_batch,
        "total_batches": total_batches,
        "rows_migrated": rows_migrated,
        "status": "in_progress",
        "saved_at": datetime.now().isoformat()
    }
    path = _get_checkpoint_path(table_name)
    with open(path, "w") as f:
        json.dump(checkpoint, f, indent=2)
    print(f"    [Skill: save_checkpoint] Saved checkpoint at batch {last_completed_batch}/{total_batches}")


def load_checkpoint(table_name: str) -> dict:
    """
    Skill: load_checkpoint

    WHY WE USE THIS:
    Before starting migration for a table, we check if a checkpoint
    file already exists from a previous failed run.
    If it does, we skip all already-completed batches and resume
    exactly where we left off — avoiding re-inserting duplicate data
    and wasting time re-processing rows that already made it through.
    If no checkpoint exists, we start fresh from batch 1.
    """
    path = _get_checkpoint_path(table_name)
    if not os.path.exists(path):
        print(f"    [Skill: load_checkpoint] No checkpoint found for '{table_name}' — starting fresh")
        return None
    with open(path, "r") as f:
        checkpoint = json.load(f)
    print(f"    [Skill: load_checkpoint] Resuming '{table_name}' from batch {checkpoint['last_completed_batch']}/{checkpoint['total_batches']}")
    return checkpoint


def complete_checkpoint(table_name: str, total_rows: int):
    """
    Skill: complete_checkpoint

    WHY WE USE THIS:
    Once all batches for a table finish successfully, we mark the
    checkpoint as 'completed' rather than deleting it immediately.
    This gives us a permanent record that this table was fully migrated,
    including when it finished and how many rows were transferred.
    It also prevents the orchestrator from accidentally re-migrating
    the same table if the pipeline is run again.
    """
    path = _get_checkpoint_path(table_name)
    if not os.path.exists(path):
        return
    with open(path, "r") as f:
        checkpoint = json.load(f)
    checkpoint["status"] = "completed"
    checkpoint["total_rows_migrated"] = total_rows
    checkpoint["completed_at"] = datetime.now().isoformat()
    with open(path, "w") as f:
        json.dump(checkpoint, f, indent=2)
    print(f"    [Skill: complete_checkpoint] '{table_name}' marked as complete")


def clear_checkpoint(table_name: str):
    """
    Skill: clear_checkpoint

    WHY WE USE THIS:
    Used when we intentionally want to re-migrate a table from scratch —
    for example during a full re-run or after fixing a data issue.
    Clearing the checkpoint file removes all saved progress,
    so the next run treats the table as if it was never migrated.
    This gives developers manual control to reset specific tables
    without touching the rest of the migration state.
    """
    path = _get_checkpoint_path(table_name)
    if os.path.exists(path):
        os.remove(path)
        print(f"    [Skill: clear_checkpoint] Checkpoint cleared for '{table_name}'")


def is_already_completed(table_name: str) -> bool:
    """
    Skill: is_already_completed

    WHY WE USE THIS:
    At the start of each table migration, we check this first.
    If a previous run already completed this table fully,
    there is no reason to migrate it again — doing so would
    cause duplicate data errors or waste time.
    This acts as a safety gate — only tables that are NOT yet
    complete will proceed through the migration pipeline.
    Think of it as an idempotency check — running the pipeline
    twice should be safe and produce the same result.
    """
    checkpoint = load_checkpoint(table_name)
    if checkpoint and checkpoint.get("status") == "completed":
        print(f"    [Skill: is_already_completed] '{table_name}' already fully migrated — skipping")
        return True
    return False