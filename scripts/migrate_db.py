#!/usr/bin/env python3
"""
Migrate data from an old SQLite database to a new one.

The old database lacks the `log_type` column in clan_logs.
This script parses each message to derive the type.

Prerequisites:
    uv run alembic upgrade head  # Create new DB schema first

Usage:
    uv run python scripts/migrate_db.py old_database.db new_database.db
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.models.clanlog import parse_log_type


def migrate_clan_logs(old_conn: sqlite3.Connection, new_conn: sqlite3.Connection) -> int:
    """Migrate clan_logs table, parsing log_type from message content."""
    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()

    # Check columns in old table
    old_cursor.execute("PRAGMA table_info(clan_logs)")
    old_columns = {row[1] for row in old_cursor.fetchall()}
    has_log_type = "log_type" in old_columns

    # Fetch all rows from old DB
    old_cursor.execute(
        "SELECT id, clan_name, member_username, message, timestamp, message_sent FROM clan_logs"
    )
    rows = old_cursor.fetchall()

    migrated = 0
    for row in rows:
        id_, clan_name, member_username, message, timestamp, message_sent = row
        log_type = parse_log_type(message)

        try:
            new_cursor.execute(
                """
                INSERT INTO clan_logs
                    (clan_name, member_username, message, timestamp, message_sent, log_type)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (clan_name, member_username, message, timestamp, message_sent, str(log_type)),
            )
            migrated += 1
        except sqlite3.IntegrityError:
            # Duplicate entry, skip
            pass

    new_conn.commit()
    return migrated


def migrate_scheduled_messages(old_conn: sqlite3.Connection, new_conn: sqlite3.Connection) -> int:
    """Migrate scheduled_messages table (direct copy)."""
    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()

    # Check if table exists in old DB
    old_cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='scheduled_messages'"
    )
    if not old_cursor.fetchone():
        return 0

    old_cursor.execute("SELECT type, channel_id, message_id, created_at FROM scheduled_messages")
    rows = old_cursor.fetchall()

    migrated = 0
    for row in rows:
        try:
            new_cursor.execute(
                """
                INSERT INTO scheduled_messages (type, channel_id, message_id, created_at)
                VALUES (?, ?, ?, ?)
                """,
                row,
            )
            migrated += 1
        except sqlite3.IntegrityError:
            pass

    new_conn.commit()
    return migrated


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <old_db_path> <new_db_path>")
        sys.exit(1)

    old_db_path = Path(sys.argv[1])
    new_db_path = Path(sys.argv[2])

    if not old_db_path.exists():
        print(f"Error: Old database not found: {old_db_path}")
        sys.exit(1)

    if not new_db_path.exists():
        print(f"Error: New database not found: {new_db_path}")
        print("Run 'uv run alembic upgrade head' first to create the schema.")
        sys.exit(1)

    print(f"Migrating from: {old_db_path}")
    print(f"Migrating to:   {new_db_path}")
    print()

    old_conn = sqlite3.connect(old_db_path)
    new_conn = sqlite3.connect(new_db_path)

    try:
        clan_logs_count = migrate_clan_logs(old_conn, new_conn)
        print(f"Migrated {clan_logs_count} clan_logs entries")

        scheduled_count = migrate_scheduled_messages(old_conn, new_conn)
        print(f"Migrated {scheduled_count} scheduled_messages entries")

        print()
        print("Migration complete!")
    finally:
        old_conn.close()
        new_conn.close()


if __name__ == "__main__":
    main()
