import os
import time
from datetime import datetime, UTC
from dotenv import load_dotenv

from utils.email_log import decrement_days_and_archive, row_to_record
from utils.mail_sender.email_generator import generate_email
from utils.mail_sender.email_sender import send_email
from utils.helper import logger

CHECK_INTERVAL_SECONDS = 24 * 60 * 60


def _send_daily_notice(row: dict, days_left: int) -> None:
    recipients = row.get("email_send_to_list", []) or []
    if not recipients:
        logger.warning("No recipients for eCard %s; skipping send", row.get("eCard Code"))
        return
    record = row_to_record(row)
    try:
        email_html = generate_email(record, days_left)
    except Exception as exc:
        logger.error("Failed to build daily email for eCard %s: %s", record.get("eCard Code"), exc)
        return
    try:
        send_email(recipients, email_html)
        logger.info(
            "Sent daily reminder for eCard %s (days_left=%s) to %s",
            record.get("eCard Code"),
            days_left,
            ", ".join(recipients),
        )
    except Exception as exc:
        logger.error("Failed to send daily email for eCard %s: %s", record.get("eCard Code"), exc)


def process_once() -> None:
    updated_rows, expired_rows = decrement_days_and_archive(send_callback=_send_daily_notice)

    if expired_rows:
        logger.info("%s entries expired and were archived", len(expired_rows))
        for row in expired_rows:
            record = row_to_record(row)
            try:
                email_html = generate_email(record, 0)
            except Exception as exc:  # Defensive guard for incomplete records
                logger.error("Failed to build expiration email for eCard %s: %s", record.get("eCard Code"), exc)
                continue
            send_email([os.getenv("NATHAN_EMAIL")], email_html)
    else:
        logger.info("No expired entries this cycle; %s active rows remain", len(updated_rows))


def run_forever() -> None:
    load_dotenv()
    logger.info("Starting daily email maintenance loop (%s second interval)", CHECK_INTERVAL_SECONDS)
    while True:
        start = datetime.now(UTC).isoformat()
        logger.info("Maintenance cycle started at %s", start)
        process_once()
        logger.info("Cycle complete; sleeping for %s seconds", CHECK_INTERVAL_SECONDS)
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_forever()
