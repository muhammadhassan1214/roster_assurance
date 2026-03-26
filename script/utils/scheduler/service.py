"""Scheduler service: state machine for first email + follow-ups.

Key rules:
- First email sends immediately when followup_stage == 0.
- Follow-ups (stages 1..5) are gated by check_roster_status before sending.
- Each send schedules the next attempt 24h later until stage > 5 or status completed.
- Failures back off by 1 hour and bump retry_count.
- No long sleeps; run run_once() from a short polling loop or external scheduler.
"""
from __future__ import annotations
from ..mail_sender.email_sender import send_email as brevo_send_email
from ..mail_sender.email_generator import generate_email
from ..automation import login_to_enrollware, search_student_using_email, no_match_found
from ..helper import get_undetected_driver, safe_navigate_to_url
from ..elements_locators import EnrollwareLocators as Els

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Sequence, Tuple

from .db import fetch_due, insert_record, mark_completed, update_record

logger = logging.getLogger(__name__)

# --- Integration hooks ----------------------------------------------------


def check_roster_status(email_list: Sequence[str]) -> Tuple[List[str], List[str]]:  # pragma: no cover - replace in prod
    emails = [e.strip() for e in (email_list or []) if e and e.strip()]
    if not emails:
        return [], []

    driver = get_undetected_driver(headless=True)
    if not driver:
        logger.error("Unable to init driver for roster status; treating all as pending")
        return emails, []

    pending: List[str] = []
    completed: List[str] = []
    try:
        if not login_to_enrollware(driver):
            logger.error("Enrollware login failed during roster check; treating all as pending")
            return emails, []

        safe_navigate_to_url(driver, Els.STUDENT_SEARCH_URL)
        for idx, email in enumerate(emails):
            search_student_using_email(driver, email, idx)
            if no_match_found(driver):
                pending.append(email)
            else:
                completed.append(email)
        return pending, completed
    except Exception:
        logger.exception("Roster status check failed; falling back to pending")
        return emails, []
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def send_email(to_addresses: Sequence[str], subject: str, body_html: str) -> None:
    brevo_send_email(to_addresses, body_html, subject)
    logger.info("Send triggered via Brevo to=%s | Subject=%s", to_addresses, subject)


# --- Public API -----------------------------------------------------------


def add_new_record(*, source_id: str | None, recipients: Iterable[str], data_payload: Dict) -> bool:
    """Insert a record with followup_stage=0 and next_send_time=now."""
    return insert_record(source_id=source_id, recipients=recipients, data_payload=data_payload)


def run_once(now: datetime | None = None) -> None:
    """Process all due records once.

    Intended to be called from a short-interval loop (e.g., every 5-10 minutes).
    """
    now = now or datetime.now(timezone.utc)
    due = fetch_due(now)
    if not due:
        logger.debug("No due records at %s", now.isoformat())
        return

    first_sends = [r for r in due if r["followup_stage"] == 0]
    followups = [r for r in due if r["followup_stage"] >= 1]

    for record in first_sends:
        _process_first_email(record, now)

    if followups:
        _process_followups(followups, now)


def run_forever(poll_interval_seconds: int = 300) -> None:
    """Simple polling loop with short sleep to avoid long blocking waits."""
    logger.info("Scheduler worker started with %s second interval", poll_interval_seconds)
    while True:
        run_once()
        time.sleep(poll_interval_seconds)


# --- Helpers --------------------------------------------------------------


def _parse_recipients(record: Dict) -> List[str]:
    raw = record.get("recipients") or "[]"
    try:
        return list(json.loads(raw))
    except Exception:
        logger.exception("Unable to parse recipients; defaulting to empty list")
        return []


def _process_first_email(record: Dict, now: datetime) -> None:
    recips = _parse_recipients(record)
    subject = "Roster Assurance - Initial Notification"
    body = _render_email(record, followup_stage=0)
    try:
        send_email(recips, subject, body)
    except Exception as exc:  # retry with backoff
        logger.exception("First email failed for record %s", record.get("id"))
        update_record(
            record["id"],
            retry_count=record.get("retry_count", 0) + 1,
            next_send_time=(now + timedelta(hours=1)).isoformat(),
        )
        return

    update_record(
        record["id"],
        followup_stage=1,
        next_send_time=(now + timedelta(hours=24)).isoformat(),
    )
    logger.info("First email sent for record %s", record.get("id"))


def _process_followups(records: Sequence[Dict], now: datetime) -> None:
    # Gather all emails for roster check
    all_emails = []
    for r in records:
        all_emails.extend(_parse_recipients(r))
    pending_emails, completed_emails = check_roster_status(all_emails)
    pending_set = set(pending_emails or [])
    completed_set = set(completed_emails or [])

    # Mark completed records whose recipients are fully completed
    completed_ids = []
    for r in records:
        recips = _parse_recipients(r)
        if recips and set(recips).issubset(completed_set):
            completed_ids.append(r["id"])
    if completed_ids:
        mark_completed(completed_ids)
        logger.info("Marked %d records completed via roster check", len(completed_ids))

    # Send follow-ups for remaining records
    for r in records:
        if r["status"] != "pending":
            continue
        recips = _parse_recipients(r)
        send_to = [e for e in recips if e in pending_set] or recips
        if not send_to:
            mark_completed([r["id"]])
            continue

        followup_number = min(int(r.get("followup_stage", 1)), 5)
        subject = f"Roster Assurance - Follow-up {followup_number} of 5"
        body = _render_email(r, followup_stage=followup_number)

        try:
            send_email(send_to, subject, body)
        except Exception:
            logger.exception("Follow-up send failed for record %s", r.get("id"))
            update_record(
                r["id"],
                retry_count=r.get("retry_count", 0) + 1,
                next_send_time=(now + timedelta(hours=1)).isoformat(),
            )
            continue

        if followup_number >= 5:
            mark_completed([r["id"]])
            logger.info("Record %s completed after final follow-up", r.get("id"))
        else:
            update_record(
                r["id"],
                followup_stage=followup_number + 1,
                next_send_time=(now + timedelta(hours=24)).isoformat(),
            )
            logger.info(
                "Follow-up %s sent for record %s; next at %s",
                followup_number,
                r.get("id"),
                (now + timedelta(hours=24)).isoformat(),
            )


def _render_email(record: Dict, followup_stage: int) -> str:
    payload = record.get("data_payload") or "{}"
    try:
        data = json.loads(payload)
    except Exception:
        data = {}
    # Map stages to days_left: initial=5, then decrement each follow-up until 0
    days_left = max(5 - max(followup_stage - 0, 0), 0)
    return generate_email(data, days_left)
