# Roster Assurance Scheduler (SQLite, restart-safe)

This adds a state-driven email follow-up system that replaces long sleeps and CSV files. It uses SQLite to track state so the worker can restart safely and avoids duplicate emails.

## Schema (SQLite)
Table `email_records` (file: `script/data/email_scheduler.db`):
- `id` INTEGER PK
- `source_id` TEXT UNIQUE (e.g., eCard Code or other upstream ID)
- `recipients` TEXT (JSON list of emails)
- `data_payload` TEXT (JSON payload for email rendering)
- `followup_stage` INT (0 first-send pending, 1-5 follow-ups)
- `next_send_time` TEXT (ISO UTC timestamp)
- `status` TEXT (`pending` | `completed`)
- `retry_count` INT
- `created_at`, `updated_at` TEXT (ISO UTC)

## Key behaviors
- Insert new records with `followup_stage=0`, `next_send_time=now`, `status=pending`.
- Worker polls due records (status pending & next_send_time <= now).
- First email sends immediately, then schedules `next_send_time = now + 24h`, `followup_stage = 1`.
- Before any follow-up (stage >=1), the worker calls `check_roster_status(email_list)`.
  - Emails returned in `completed_emails` stop receiving further mail; their records move to `status=completed`.
  - Emails in `pending_emails` continue receiving follow-ups.
- Up to 5 follow-ups are sent ("Follow-up N of 5"), spaced 24h. After 5, status becomes `completed`.
- Failures increment `retry_count` and back off `next_send_time` by 1 hour.
- No long sleeps; `run_forever` uses a short poll interval (default 300s).

## Files
- `script/utils/scheduler/db.py` – SQLite schema and CRUD.
- `script/utils/scheduler/service.py` – business logic, placeholders for `send_email` and `check_roster_status`.
- `script/email_worker.py` – CLI worker (loop or single run).

## How to use
1) Insert records from your scraping pipeline:
```python
from utils.scheduler.service import add_new_record
add_new_record(
    source_id="<ecard_code>",
    recipients=["user@example.com"],
    data_payload={"course": "BLS", "course_date": "2026-03-25"},
)
```

2) Implement `check_roster_status` and `send_email` in `utils/scheduler/service.py` to call your real systems.

3) Run the worker (polling loop):
```powershell
python -m script.email_worker --interval 300
```
Or a single pass (for cron/task scheduler):
```powershell
python -m script.email_worker --once
```

## Email template
Rendered in `_render_email`: includes an "Initial Notice" or "Follow-up N of 5" banner and echoes the stored payload as key/value pairs.

