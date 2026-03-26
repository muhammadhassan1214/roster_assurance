"""SQLite persistence for email follow-up scheduler.

Stores eCard/email records with follow-up state so the worker can resume
safely after restarts.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "email_scheduler.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS email_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT UNIQUE,
    recipients TEXT NOT NULL,
    data_payload TEXT,
    followup_stage INTEGER NOT NULL DEFAULT 0,
    next_send_time TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_email_records_status_due
    ON email_records(status, next_send_time);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    with _connect() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def insert_record(
    *,
    source_id: Optional[str],
    recipients: Iterable[str],
    data_payload: Dict[str, Any],
    next_send_time: Optional[datetime] = None,
) -> bool:
    """Insert a new record with followup_stage=0.

    Returns True if inserted, False if skipped because source_id already exists.
    """
    init_db()
    now_iso = _now_iso()
    next_send = next_send_time.isoformat() if next_send_time else now_iso
    recips_json = json.dumps(list(recipients))
    payload_json = json.dumps(data_payload or {})
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO email_records (
                source_id, recipients, data_payload,
                followup_stage, next_send_time, status,
                retry_count, created_at, updated_at
            ) VALUES (?, ?, ?, 0, ?, 'pending', 0, ?, ?)
            """,
            (source_id, recips_json, payload_json, next_send, now_iso, now_iso),
        )
        conn.commit()
        return cur.rowcount > 0


def fetch_due(now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Return pending records whose next_send_time is due."""
    init_db()
    now_iso = (now or datetime.now(timezone.utc)).isoformat()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM email_records
            WHERE status='pending' AND datetime(next_send_time) <= datetime(?)
            ORDER BY next_send_time ASC
            """,
            (now_iso,),
        ).fetchall()
    return [dict(r) for r in rows]


def update_record(record_id: int, **fields: Any) -> None:
    """Partial update for a record."""
    if not fields:
        return
    fields["updated_at"] = _now_iso()
    assignments = ", ".join(f"{k}=?" for k in fields.keys())
    values = list(fields.values()) + [record_id]
    with _connect() as conn:
        conn.execute(f"UPDATE email_records SET {assignments} WHERE id=?", values)
        conn.commit()


def mark_completed(record_ids: Iterable[int]) -> None:
    ids = list(record_ids)
    if not ids:
        return
    now_iso = _now_iso()
    placeholders = ",".join(["?"] * len(ids))
    with _connect() as conn:
        conn.execute(
            f"UPDATE email_records SET status='completed', updated_at=? WHERE id IN ({placeholders})",
            [now_iso, *ids],
        )
        conn.commit()

