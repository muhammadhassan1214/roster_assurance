import csv
import os
from datetime import datetime, UTC
from typing import List, Dict, Tuple, Callable, Optional

from .helper import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ACTIVE_LOG = os.path.join(DATA_DIR, "email_log.csv")
ARCHIVE_LOG = os.path.join(DATA_DIR, "email_archive.csv")

ACTIVE_FIELDS = [
    "eCard Code",
    "Course",
    "Course Date",
    "Instructor",
    "Student Name",
    "Student Email",
    "days_left",
    "email_send_to",
    "last_updated",
]
ARCHIVE_FIELDS = ACTIVE_FIELDS + ["archived_at"]


def ensure_log_files() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(ACTIVE_LOG):
        with open(ACTIVE_LOG, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=ACTIVE_FIELDS)
            writer.writeheader()
    if not os.path.exists(ARCHIVE_LOG):
        with open(ARCHIVE_LOG, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=ARCHIVE_FIELDS)
            writer.writeheader()


def _serialize_email_list(email_list: List[str]) -> str:
    cleaned = [e.strip() for e in (email_list or []) if e and e.strip()]
    return ";".join(cleaned)


def _deserialize_email_list(serialized: str) -> List[str]:
    return [e for e in (serialized or "").split(";") if e]


def _row_from_record(record: Dict, days_left: int, email_send_to: List[str]) -> Dict:
    return {
        "eCard Code": record.get("eCard Code", ""),
        "Course": record.get("Course", ""),
        "Course Date": record.get("Course Date", ""),
        "Instructor": record.get("Instructor", ""),
        "Student Name": record.get("Student Name", ""),
        "Student Email": record.get("Student Email", ""),
        "days_left": str(max(days_left, 0)),
        "email_send_to": _serialize_email_list(email_send_to),
        "last_updated": datetime.now(UTC).isoformat(),
    }


def _read_rows(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _write_rows(path: str, fieldnames: List[str], rows: List[Dict]) -> None:
    sanitized = [
        {key: row.get(key, "") for key in fieldnames}
        for row in (rows or [])
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sanitized)


def _append_rows(path: str, fieldnames: List[str], rows: List[Dict]) -> None:
    sanitized = [
        {key: row.get(key, "") for key in fieldnames}
        for row in (rows or [])
    ]
    if not sanitized:
        return
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(sanitized)


def add_entry_if_new(record: Dict, days_left: int, email_send_to: List[str]) -> bool:
    ensure_log_files()
    ecard_code = (record or {}).get("eCard Code")
    if not ecard_code:
        logger.warning("Cannot log email entry without 'eCard Code'")
        return False

    active_rows = _read_rows(ACTIVE_LOG)
    if any(row.get("eCard Code") == ecard_code for row in active_rows):
        logger.info("Entry for eCard Code %s already exists in log; skipping", ecard_code)
        return False

    row = _row_from_record(record, days_left, email_send_to)
    _append_rows(ACTIVE_LOG, ACTIVE_FIELDS, [row])
    logger.info("Logged email entry for eCard Code %s with days_left=%s", ecard_code, row["days_left"])
    return True


def load_active_entries() -> List[Dict]:
    ensure_log_files()
    rows = _read_rows(ACTIVE_LOG)
    for row in rows:
        try:
            row["days_left"] = int(row.get("days_left", 0))
        except ValueError:
            row["days_left"] = 0
        row["email_send_to_list"] = _deserialize_email_list(row.get("email_send_to", ""))
    return rows


def _archive_rows(rows: List[Dict]) -> None:
    if not rows:
        return
    timestamp = datetime.now(UTC).isoformat()
    archive_ready = []
    for row in rows:
        archived_row = row.copy()
        archived_row["archived_at"] = timestamp
        archive_ready.append(archived_row)
    _append_rows(ARCHIVE_LOG, ARCHIVE_FIELDS, archive_ready)


def decrement_days_and_archive(
    send_callback: Optional[Callable[[Dict, int], None]] = None,
) -> Tuple[List[Dict], List[Dict]]:
    """Decrement days_left for all active rows, archive rows at 0. Returns (updated_rows, expired_rows).

    If send_callback is provided, it will be invoked once per row before decrementing,
    with the row dict and the current days_left value.
    """
    ensure_log_files()
    rows = load_active_entries()
    updated_rows: List[Dict] = []
    expired_rows: List[Dict] = []

    for row in rows:
        days_left = row.get("days_left", 0)
        if not isinstance(days_left, int):
            try:
                days_left = int(days_left)
            except (TypeError, ValueError):
                days_left = 0

        if send_callback:
            send_callback(row, days_left)

        days_left -= 1
        row["days_left"] = max(days_left, 0)
        row["last_updated"] = datetime.now(UTC).isoformat()
        if days_left <= 0:
            expired_rows.append(row)
        else:
            updated_rows.append(row)

    _write_rows(ACTIVE_LOG, ACTIVE_FIELDS, updated_rows)
    _archive_rows(expired_rows)
    logger.info("Decremented days_left for %s entries; %s expired", len(rows), len(expired_rows))
    return updated_rows, expired_rows


def row_to_record(row: Dict) -> Dict:
    return {
        "Course": row.get("Course", ""),
        "Course Date": row.get("Course Date", ""),
        "eCard Code": row.get("eCard Code", ""),
        "Instructor": row.get("Instructor", ""),
        "Student Name": row.get("Student Name", ""),
        "Student Email": row.get("Student Email", ""),
    }


def active_log_path() -> str:
    ensure_log_files()
    return ACTIVE_LOG


def archive_log_path() -> str:
    ensure_log_files()
    return ARCHIVE_LOG
