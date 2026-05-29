import time


# How many rows per batch — tunable based on your system
BATCH_SIZE = 10_000

# Delay between batches in seconds — prevents overwhelming the DB
THROTTLE_DELAY = 0.1


def chunk_rows(rows: list, batch_size: int = BATCH_SIZE) -> list:
    """
    Skill: chunk_rows
    Splits a large list of rows into smaller batches.
    Input: full list of rows, batch size
    Output: list of batches
    """
    print(f"    [Skill: chunk_rows] Splitting {len(rows)} rows into batches of {batch_size}...")
    batches = [rows[i:i + batch_size] for i in range(0, len(rows), batch_size)]
    print(f"    [Skill: chunk_rows] Created {len(batches)} batches")
    return batches


def throttle(batch_number: int, total_batches: int):
    """
    Skill: throttle
    Adds a small delay between batches to reduce DB strain.
    Input: current batch number, total batches
    """
    print(f"    [Skill: throttle] Batch {batch_number}/{total_batches} complete. Waiting {THROTTLE_DELAY}s...")
    time.sleep(THROTTLE_DELAY)


def log_batch_progress(batch_number: int, total_batches: int, rows_migrated: int, total_rows: int):
    """
    Skill: log_batch_progress
    Prints a progress update for the current batch.
    """
    percent = round((rows_migrated / total_rows) * 100, 1)
    print(f"    [Skill: log_batch_progress] Progress: {percent}% ({rows_migrated}/{total_rows} rows) — Batch {batch_number}/{total_batches}")


def calculate_batch_stats(total_rows: int, batch_size: int = BATCH_SIZE) -> dict:
    """
    Skill: calculate_batch_stats
    Returns stats about the batch run before it starts.
    Input: total rows, batch size
    Output: {total_batches, batch_size, estimated_time_seconds}
    """
    import math
    total_batches = math.ceil(total_rows / batch_size)
    estimated_time = round(total_batches * THROTTLE_DELAY, 1)
    stats = {
        "total_rows": total_rows,
        "batch_size": batch_size,
        "total_batches": total_batches,
        "estimated_time_seconds": estimated_time
    }
    print(f"    [Skill: calculate_batch_stats] {stats}")
    return stats