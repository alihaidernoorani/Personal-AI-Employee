"""Gmail API helpers for email-mcp server.

Uses OAuth 2.0 via credentials.json instead of App Password.

First-time setup (run once):
  python scripts/setup_gmail_mcp.py

After that, .gmail_mcp_token.json auto-refreshes silently.

DRY_RUN=true (default) — no real emails sent during development.
"""

import base64
import logging
import os
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent
CREDENTIALS_FILE = Path(os.getenv("GMAIL_CREDENTIALS", str(BASE_DIR / "credentials.json")))
TOKEN_FILE = BASE_DIR / ".gmail_mcp_token.json"
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() != "false"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def _get_service():
    """Return an authenticated Gmail API service object.

    Uses .gmail_mcp_token.json if valid; auto-refreshes if expired.
    Raises RuntimeError if no token exists (run setup_gmail_mcp.py first).
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())
            logger.info("Gmail token refreshed.")
        else:
            raise RuntimeError(
                f"No valid Gmail OAuth token found at {TOKEN_FILE}. "
                "Run: python scripts/setup_gmail_mcp.py"
            )

    return build("gmail", "v1", credentials=creds)


def send_email(
    to: str,
    subject: str,
    body: str,
    reply_to_message_id: str | None = None,
) -> dict:
    """Send an email via Gmail API.

    Returns:
        {"status": "sent"|"dry_run"|"error", "message_id": str}
    """
    if DRY_RUN:
        logger.info(f"[DRY_RUN] send_email to={to} subject={subject!r}")
        return {
            "status": "dry_run",
            "message_id": f"dry_run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        }

    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_EMAIL
        msg["To"] = to
        msg["Subject"] = subject
        if reply_to_message_id:
            msg["In-Reply-To"] = reply_to_message_id
            msg["References"] = reply_to_message_id
        msg.attach(MIMEText(body, "plain"))

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service = _get_service()
        sent = service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()

        message_id = sent.get("id", "unknown")
        logger.info(f"Email sent to {to}: {message_id}")
        return {"status": "sent", "message_id": message_id}

    except Exception as e:
        logger.error(f"send_email failed: {e}")
        return {"status": "error", "error": str(e)}


def draft_reply(message_id: str, draft_body: str) -> dict:
    """Save a draft reply via Gmail API Drafts.

    Returns:
        {"status": "drafted"|"dry_run"|"error", "draft_id": str}
    """
    if DRY_RUN:
        logger.info(f"[DRY_RUN] draft_reply message_id={message_id}")
        return {"status": "dry_run", "draft_id": f"dry_run_draft_{message_id}"}

    try:
        msg = MIMEText(draft_body, "plain")
        msg["From"] = GMAIL_EMAIL
        msg["Subject"] = "Re: (draft)"
        msg["In-Reply-To"] = message_id

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service = _get_service()
        draft = service.users().drafts().create(
            userId="me",
            body={"message": {"raw": raw, "threadId": message_id}},
        ).execute()

        draft_id = draft.get("id", "unknown")
        logger.info(f"Draft created: {draft_id}")
        return {"status": "drafted", "draft_id": draft_id}

    except Exception as e:
        logger.error(f"draft_reply failed: {e}")
        return {"status": "error", "error": str(e)}


def search_inbox(query: str, max_results: int = 10) -> list:
    """Search Gmail using the Gmail API.

    Args:
        query: Gmail search query (same syntax as Gmail search box)
        max_results: Maximum number of results to return

    Returns:
        List of {"uid": str, "from": str, "subject": str, "snippet": str}
    """
    if DRY_RUN:
        logger.info(f"[DRY_RUN] search_inbox query={query!r}")
        return [{"uid": "dry_run", "from": "dry@run.com", "subject": "Dry run result", "snippet": "DRY_RUN=true"}]

    results = []
    try:
        service = _get_service()
        resp = service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()

        for m in resp.get("messages", []):
            try:
                msg = service.users().messages().get(
                    userId="me",
                    id=m["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                ).execute()
                headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                results.append({
                    "uid": msg["id"],
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", ""),
                    "snippet": msg.get("snippet", ""),
                    "date": headers.get("Date", ""),
                })
            except Exception:
                continue

    except Exception as e:
        logger.error(f"search_inbox failed: {e}")

    return results
