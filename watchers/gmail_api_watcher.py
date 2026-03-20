"""Gmail API watcher — polls Gmail for UNSEEN IMPORTANT messages using Google API.

Uses credentials.json (OAuth 2.0) for authentication. Fetches unread messages
marked with the IMPORTANT label and creates .md files in Needs_Action/.

Validation steps:
  1. Ensure credentials.json exists in the project root (OAuth credentials from Google Cloud Console)
  2. python -c "from watchers.gmail_api_watcher import GmailApiWatcher; print('import ok')"
  3. Run: VAULT_PATH="$PWD/AI_Employee_Vault" python orchestrator.py --watcher gmail_api
  4. On first run, browser will open to authorize access
  5. Send a test email and mark it as IMPORTANT
  6. Within 2 minutes, Needs_Action/GMAIL_*.md should appear with YAML frontmatter
  7. Restart the watcher; confirm no duplicate for the same message ID (idempotency)

Extends BaseWatcher. Creates GMAIL_*.md task files in Needs_Action/.
Tracks processed Gmail message IDs in scripts/processed_gmail_api.json.
"""

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from watchers.base_watcher import BaseWatcher

try:
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    import google.auth
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    raise ImportError(
        "google-auth and google-api-python-client not installed. "
        "Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
    ) from e

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _slugify(text: str, max_len: int = 40) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:max_len] or "no-subject"


class GmailApiWatcher(BaseWatcher):
    """Polls Gmail API for UNSEEN IMPORTANT messages and creates task files."""

    def __init__(self, vault_path: str, check_interval: int = 120):
        super().__init__(vault_path, check_interval=check_interval)
        self._registry_path = (
            Path(__file__).parent.parent / "scripts" / "processed_gmail_api.json"
        )
        self._processed: set = self._load_registry()
        self._credentials_path = Path(__file__).parent.parent / "credentials.json"
        self._token_path = Path(__file__).parent.parent / ".gmail_token.json"
        self._service = None
        self._user_email = None

    # ------------------------------------------------------------------
    # Registry helpers
    # ------------------------------------------------------------------

    def _load_registry(self) -> set:
        """Load processed message IDs from registry."""
        try:
            data = json.loads(self._registry_path.read_text(encoding="utf-8"))
            return set(data.get("processed", []))
        except (FileNotFoundError, json.JSONDecodeError):
            return set()

    def _save_registry(self) -> None:
        """Save processed message IDs to registry."""
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._registry_path.write_text(
            json.dumps({"processed": sorted(self._processed)}, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Google OAuth helpers
    # ------------------------------------------------------------------

    def _authenticate(self) -> bool:
        """Authenticate with Google API using OAuth 2.0. Returns True if successful."""
        try:
            creds = None

            # Load existing token if available
            if self._token_path.exists():
                creds = google.auth.load_credentials_from_file(str(self._token_path))[0]

            # If no valid token, perform OAuth flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired token...")
                    req = Request()
                    creds.refresh(req)
                else:
                    if not self._credentials_path.exists():
                        logger.error(
                            f"credentials.json not found at {self._credentials_path}. "
                            "Download from Google Cloud Console."
                        )
                        return False

                    logger.info("Starting OAuth flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self._credentials_path), SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save token for next run
                self._token_path.write_text(creds.to_json(), encoding="utf-8")

            self._service = build("gmail", "v1", credentials=creds)
            logger.info("Gmail API authenticated successfully")
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            self._write_error_file("gmail_api_auth", str(e))
            return False

    def _get_user_email(self) -> Optional[str]:
        """Get authenticated user's email address."""
        if not self._service:
            return None
        try:
            profile = self._service.users().getProfile(userId="me").execute()
            return profile.get("emailAddress")
        except Exception as e:
            logger.error(f"Failed to get user email: {e}")
            return None

    # ------------------------------------------------------------------
    # BaseWatcher interface
    # ------------------------------------------------------------------

    def check_for_updates(self) -> list:
        """Poll Gmail API for UNSEEN IMPORTANT messages. Returns list of new messages."""
        if not self._service:
            if not self._authenticate():
                return []

        if not self._user_email:
            self._user_email = self._get_user_email()

        new_tasks = []
        try:
            # Query for unread messages with IMPORTANT label (marked by user or Gmail's Smart Compose)
            query = 'is:unread label:IMPORTANT'

            results = (
                self._service.users()
                .messages()
                .list(userId="me", q=query, maxResults=10)
                .execute()
            )
            messages = results.get("messages", [])

            for msg_metadata in messages:
                msg_id = msg_metadata["id"]

                # Skip if already processed
                if msg_id in self._processed:
                    continue

                try:
                    # Fetch full message details
                    message = (
                        self._service.users()
                        .messages()
                        .get(userId="me", id=msg_id, format="full")
                        .execute()
                    )

                    headers = message["payload"]["headers"]
                    subject = next(
                        (h["value"] for h in headers if h["name"] == "Subject"),
                        "(no subject)",
                    )
                    sender = next(
                        (h["value"] for h in headers if h["name"] == "From"),
                        "unknown@example.com",
                    )
                    date_str = next(
                        (h["value"] for h in headers if h["name"] == "Date"),
                        "",
                    )

                    # Extract snippet
                    snippet = message.get("snippet", "")

                    # Determine priority from labels
                    labels = message.get("labelIds", [])
                    priority = "high" if "IMPORTANT" in labels else "normal"

                    task_path = self.create_action_file(
                        {
                            "msg_id": msg_id,
                            "sender": sender,
                            "subject": subject,
                            "date": date_str,
                            "snippet": snippet,
                            "priority": priority,
                        }
                    )

                    if task_path:
                        self._processed.add(msg_id)
                        self._save_registry()
                        new_tasks.append(task_path)
                        logger.info(f"Created Gmail task: {task_path.name}")
                        self.log_action(
                            "gmail_email_detected",
                            sender,
                            "success",
                            {"subject": subject, "priority": priority},
                        )

                except Exception as e:
                    logger.error(f"Error processing message {msg_id}: {e}")
                    self._write_error_file("gmail_api_watcher", str(e))

        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            self._write_error_file("gmail_api_http_error", str(e))
        except Exception as e:
            logger.error(f"GmailApiWatcher error: {e}")
            self._write_error_file("gmail_api_watcher", str(e))

        return new_tasks

    def create_action_file(self, item: dict) -> Path:
        """Write GMAIL_*.md task file to Needs_Action/ with metadata."""
        msg_id = item["msg_id"]
        subject = item["subject"]
        sender = item["sender"]
        snippet = item["snippet"]
        priority = item.get("priority", "normal")

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        slug = _slugify(subject)
        filename = f"GMAIL_{ts}_{slug}.md"
        task_path = self.needs_action / filename

        received = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        content = f"""---
type: email
source: gmail_api
msg_id: "{msg_id}"
sender: "{sender}"
subject: "{subject}"
snippet: "{snippet[:200]}"
priority: {priority}
received: "{received}"
status: pending
---

## Email from {sender}

**Subject:** {subject}

**Snippet:** {snippet}

## Actions

- [ ] Read full email in Gmail
- [ ] Draft reply
- [ ] Archive
- [ ] Add to task list
"""
        task_path.write_text(content, encoding="utf-8")
        return task_path

    def _write_error_file(self, watcher_name: str, error_msg: str) -> None:
        """Write ERROR_*.md to Needs_Action/ on errors."""
        try:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            error_path = self.needs_action / f"ERROR_{ts}_{watcher_name}.md"
            error_path.write_text(
                f"""---
type: error
source: {watcher_name}
received: "{datetime.now(timezone.utc).isoformat()}Z"
priority: urgent
status: pending
---

## Error

{error_msg}
""",
                encoding="utf-8",
            )
            logger.info(f"Wrote error file: {error_path.name}")
        except Exception as write_err:
            logger.error(f"Failed to write error file: {write_err}")

    def run(self) -> None:
        """Run Gmail API watcher — polls every check_interval seconds (default 120s)."""
        logger.info(
            f"GmailApiWatcher started (check_interval={self.check_interval}s)"
        )
        while True:
            try:
                self.check_for_updates()
            except Exception as e:
                logger.error(f"Unexpected error in watch loop: {e}")
                self.log_action("watch_loop_error", "", "failure", {"error": str(e)})
            time.sleep(self.check_interval)
