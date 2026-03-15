"""Gmail watcher — polls Gmail INBOX for UNSEEN messages every 5 minutes.

Validation steps:
  1. python -c "from watchers.gmail_watcher import GmailWatcher; print('import ok')"
  2. Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env (Gmail App Password required, not account password)
  3. Run: VAULT_PATH="$PWD/AI_Employee_Vault" python orchestrator.py --watcher gmail
  4. Send a test email to the monitored inbox
  5. Within 5 minutes, Needs_Action/EMAIL_*.md should appear with valid YAML frontmatter
  6. Restart the watcher; confirm no duplicate task file is created for the same email (idempotency)

Extends BaseWatcher. Creates EMAIL_*.md task files in Needs_Action/.
Tracks processed IMAP UIDs in scripts/processed_gmail.json.
"""

import imaplib
import email
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from watchers.base_watcher import BaseWatcher

load_dotenv()

logger = logging.getLogger(__name__)


def _slugify(text: str, max_len: int = 40) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:max_len] or "no-subject"


class GmailWatcher(BaseWatcher):
    """Polls Gmail INBOX for UNSEEN messages and creates task files."""

    def __init__(self, vault_path: str):
        super().__init__(vault_path)
        self._registry_path = (
            Path(__file__).parent.parent / "scripts" / "processed_gmail.json"
        )
        self._processed: set = self._load_registry()
        self._gmail_email = os.getenv("GMAIL_EMAIL", "")
        self._gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")

    # ------------------------------------------------------------------
    # Registry helpers
    # ------------------------------------------------------------------

    def _load_registry(self) -> set:
        try:
            data = json.loads(self._registry_path.read_text(encoding="utf-8"))
            return set(data.get("processed", []))
        except (FileNotFoundError, json.JSONDecodeError):
            return set()

    def _save_registry(self) -> None:
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._registry_path.write_text(
            json.dumps({"processed": sorted(self._processed)}, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # BaseWatcher interface
    # ------------------------------------------------------------------

    def check_for_updates(self) -> list:
        """Poll Gmail for UNSEEN messages. Returns list of new task file paths."""
        if not self._gmail_email or not self._gmail_password:
            logger.warning("GMAIL_EMAIL or GMAIL_APP_PASSWORD not set — skipping poll")
            return []

        new_tasks = []
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(self._gmail_email, self._gmail_password)
            imap.select("INBOX")

            _, uid_data = imap.uid("search", None, "UNSEEN")
            uids = uid_data[0].split() if uid_data[0] else []

            for uid_bytes in uids:
                uid = uid_bytes.decode()
                if uid in self._processed:
                    continue

                try:
                    _, msg_data = imap.uid("fetch", uid_bytes, "(RFC822.HEADER)")
                    raw_header = msg_data[0][1]
                    msg = email.message_from_bytes(raw_header)

                    sender = msg.get("From", "unknown@example.com")
                    subject = msg.get("Subject", "(no subject)")
                    date_str = msg.get("Date", "")

                    task_path = self.create_action_file(
                        {
                            "uid": uid,
                            "sender": sender,
                            "subject": subject,
                            "date": date_str,
                        }
                    )

                    if task_path:
                        # Mark as read
                        imap.uid("store", uid_bytes, "+FLAGS", "\\Seen")
                        self._processed.add(uid)
                        self._save_registry()
                        new_tasks.append(task_path)
                        logger.info(f"Created email task: {task_path.name}")

                except Exception as e:
                    logger.error(f"Error processing UID {uid}: {e}")
                    self._write_error_file("gmail_watcher", str(e))

            imap.logout()

        except Exception as e:
            logger.error(f"GmailWatcher non-fatal error: {e}")
            self._write_error_file("gmail_watcher", str(e))

        return new_tasks

    def create_action_file(self, item: dict) -> Path:
        """Write EMAIL_*.md task file to Needs_Action/."""
        uid = item["uid"]
        subject = item["subject"]
        sender = item["sender"]

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        slug = _slugify(subject)
        filename = f"EMAIL_{ts}_{slug}.md"
        task_path = Path(self.vault_path) / "Needs_Action" / filename

        received = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        content = f"""---
type: email
source: gmail
sender: "{sender}"
subject: "{subject}"
body_snippet: "(header only — body fetched on demand)"
imap_uid: "{uid}"
received: "{received}"
priority: normal
status: pending
---

## Email Summary

New email from {sender} with subject: {subject}

## Suggested Actions

- [ ] Draft a reply
- [ ] File the email
"""
        task_path.write_text(content, encoding="utf-8")
        return task_path

    def _write_error_file(self, watcher_name: str, error_msg: str) -> None:
        """Write ERROR_*.md to Needs_Action/ on non-fatal errors (FR-005)."""
        try:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            error_path = (
                Path(self.vault_path)
                / "Needs_Action"
                / f"ERROR_{ts}_{watcher_name}.md"
            )
            error_path.write_text(
                f"---\ntype: error\nsource: {watcher_name}\nreceived: \"{datetime.now(timezone.utc).isoformat()}Z\"\npriority: urgent\nstatus: pending\n---\n\n## Error\n\n{error_msg}\n",
                encoding="utf-8",
            )
            logger.info(f"Wrote error file: {error_path.name}")
        except Exception as write_err:
            logger.error(f"Failed to write error file: {write_err}")

    def run(self) -> None:
        """Run Gmail watcher — polls every 5 minutes (300s)."""
        logger.info("GmailWatcher started (5-min poll)")
        while True:
            self.check_for_updates()
            time.sleep(300)
