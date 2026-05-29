from db.target_writer import get_connection, execute_sql


def get_indexes(table_name: str) -> list:
    """
    Skill: get_indexes

    WHY WE USE THIS:
    Before dropping indexes, we need to know what indexes exist on the table.
    We store them so we can recreate the exact same indexes after migration.
    Without this, we would lose all index definitions permanently.
    """
    print(f"    [Skill: get_indexes] Fetching indexes for '{table_name}'...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = '{table_name}'
        AND indexname NOT LIKE '%_pkey'
    """)
    indexes = [{"name": row[0], "definition": row[1]} for row in cursor.fetchall()]
    conn.close()
    print(f"    [Skill: get_indexes] Found {len(indexes)} indexes on '{table_name}'")
    return indexes


def drop_indexes(table_name: str) -> list:
    """
    Skill: drop_indexes

    WHY WE USE THIS:
    Indexes slow down INSERT operations significantly.
    For every row inserted, PostgreSQL updates all indexes on that table.
    With 1 million rows and 3 indexes, that's 3 million extra index operations.
    Dropping indexes before migration and recreating after can make
    bulk inserts 3-5x faster. We return the index definitions so
    recreate_indexes() can restore them exactly as they were.
    """
    print(f"    [Skill: drop_indexes] Dropping indexes on '{table_name}'...")
    indexes = get_indexes(table_name)
    for index in indexes:
        try:
            execute_sql(f"DROP INDEX IF EXISTS {index['name']}")
            print(f"    [Skill: drop_indexes] Dropped index '{index['name']}'")
        except Exception as e:
            print(f"    [Skill: drop_indexes] Could not drop '{index['name']}': {e}")
    print(f"    [Skill: drop_indexes] Done — {len(indexes)} indexes dropped")
    return indexes


def recreate_indexes(indexes: list):
    """
    Skill: recreate_indexes

    WHY WE USE THIS:
    After all data is migrated, we restore the indexes that were dropped.
    This is done at the end — not during migration — so inserts stay fast.
    We use the exact index definitions we saved before dropping them,
    ensuring the recreated indexes are identical to the originals.
    Running this after migration also means the index is built once
    across all data rather than updated row by row during inserts.
    """
    if not indexes:
        print(f"    [Skill: recreate_indexes] No indexes to recreate")
        return
    print(f"    [Skill: recreate_indexes] Recreating {len(indexes)} indexes...")
    for index in indexes:
        try:
            execute_sql(index["definition"])
            print(f"    [Skill: recreate_indexes] Recreated '{index['name']}'")
        except Exception as e:
            print(f"    [Skill: recreate_indexes] Could not recreate '{index['name']}': {e}")
    print(f"    [Skill: recreate_indexes] Done")


def disable_triggers(table_name: str):
    """
    Skill: disable_triggers

    WHY WE USE THIS:
    Triggers fire on every INSERT and can significantly slow down
    bulk migrations. For example an audit trigger logging every
    insert would create 1 million audit records during migration.
    We disable triggers during migration and re-enable them after
    so the migrated data doesn't generate false audit entries.
    """
    print(f"    [Skill: disable_triggers] Disabling triggers on '{table_name}'...")
    try:
        execute_sql(f"ALTER TABLE {table_name} DISABLE TRIGGER ALL")
        print(f"    [Skill: disable_triggers] Triggers disabled on '{table_name}'")
    except Exception as e:
        print(f"    [Skill: disable_triggers] Could not disable triggers: {e}")


def enable_triggers(table_name: str):
    """
    Skill: enable_triggers

    WHY WE USE THIS:
    After migration is complete, triggers must be re-enabled so the
    table behaves normally in production. Leaving triggers disabled
    would mean future inserts are not audited or processed correctly.
    """
    print(f"    [Skill: enable_triggers] Re-enabling triggers on '{table_name}'...")
    try:
        execute_sql(f"ALTER TABLE {table_name} ENABLE TRIGGER ALL")
        print(f"    [Skill: enable_triggers] Triggers re-enabled on '{table_name}'")
    except Exception as e:
        print(f"    [Skill: enable_triggers] Could not enable triggers: {e}")