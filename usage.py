import sqlite3
from datetime import datetime, timezone

DB_PATH = "usage.db"
MONTHLY_LIMIT = 4

conn = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA busy_timeout=5000;")

conn.execute(
    """
    CREATE TABLE IF NOT EXISTS usage (
        user_id TEXT NOT NULL,
        month TEXT NOT NULL,
        used_count INTEGER NOT NULL DEFAULT 0,
        reserved_count INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id, month)
    )
    """
)


def _month_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _ensure_row(user_id: str, month: str) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO usage (user_id, month, used_count, reserved_count)
        VALUES (?, ?, 0, 0)
        """,
        (user_id, month),
    )


def reserve_quota(user_id: str, limit: int = MONTHLY_LIMIT) -> bool:
    month = _month_key()
    conn.execute("BEGIN IMMEDIATE")
    try:
        _ensure_row(user_id, month)
        used, reserved = conn.execute(
            "SELECT used_count, reserved_count FROM usage WHERE user_id=? AND month=?",
            (user_id, month),
        ).fetchone()

        if used + reserved >= limit:
            conn.execute("ROLLBACK")
            return False

        conn.execute(
            "UPDATE usage SET reserved_count = reserved_count + 1 WHERE user_id=? AND month=?",
            (user_id, month),
        )
        conn.execute("COMMIT")
        return True
    except Exception:
        conn.execute("ROLLBACK")
        raise


def commit_quota(user_id: str) -> None:
    month = _month_key()
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            """
            UPDATE usage
            SET reserved_count = CASE
                                    WHEN reserved_count > 0 THEN reserved_count - 1
                                    ELSE 0
                                 END,
                used_count = used_count + 1
            WHERE user_id=? AND month=?
            """,
            (user_id, month),
        )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def release_quota(user_id: str) -> None:
    month = _month_key()
    conn.execute(
        """
        UPDATE usage
        SET reserved_count = CASE
                                WHEN reserved_count > 0 THEN reserved_count - 1
                                ELSE 0
                             END
        WHERE user_id=? AND month=?
        """,
        (user_id, month),
    )


def remaining_quota(user_id: str, limit: int = MONTHLY_LIMIT) -> int:
    month = _month_key()
    row = conn.execute(
        "SELECT used_count FROM usage WHERE user_id=? AND month=?",
        (user_id, month),
    ).fetchone()
    used = row[0] if row else 0
    return max(0, limit - used)
