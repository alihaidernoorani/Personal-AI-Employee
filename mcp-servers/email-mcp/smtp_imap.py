"""SMTP/IMAP helpers for email-mcp server.

All external calls are gated behind DRY_RUN env var.
DRY_RUN=true (default): logs the action, returns dry_run status.
DRY_RUN=false: makes real SMTP/IMAP calls.
"""

import imaplib
import json
import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() != "false"


def send_email(
    to: str,
    subject: str,
    body: str,
    reply_to_message_id: str | None = None,
) -> dict:
    """Send an email via Gmail SMTP.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
        reply_to_message_id: Optional IMAP UID to reply to

    Returns:
        {"status": "sent"|"dry_run", "message_id": str}
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

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        message_id = msg.get("Message-ID", "unknown")
        logger.info(f"Email sent to {to}: {message_id}")
        return {"status": "sent", "message_id": message_id}

    except Exception as e:
        logger.error(f"send_email failed: {e}")
        return {"status": "error", "error": str(e)}


def draft_reply(message_id: str, draft_body: str) -> dict:
    """Save a draft reply to Gmail Drafts folder.

    Args:
        message_id: IMAP UID of the message to reply to
        draft_body: Draft body text

    Returns:
        {"status": "drafted"|"dry_run", "draft_id": str}
    """
    if DRY_RUN:
        logger.info(f"[DRY_RUN] draft_reply message_id={message_id}")
        return {"status": "dry_run", "draft_id": f"dry_run_draft_{message_id}"}

    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        imap.select("[Gmail]/Drafts")

        msg = MIMEText(draft_body, "plain")
        msg["From"] = GMAIL_EMAIL
        msg["Subject"] = "Re: (draft)"
        msg["In-Reply-To"] = message_id

        imap.append(
            "[Gmail]/Drafts",
            "",
            imaplib.Time2Internaldate(datetime.now().timetuple()),
            msg.as_bytes(),
        )
        imap.logout()

        return {"status": "drafted", "draft_id": f"draft_{message_id}"}

    except Exception as e:
        logger.error(f"draft_reply failed: {e}")
        return {"status": "error", "error": str(e)}


def search_inbox(query: str, max_results: int = 10) -> list:
    """Search Gmail INBOX using IMAP search.

    Args:
        query: IMAP search string (e.g. "FROM alice@example.com")
        max_results: Maximum number of results to return

    Returns:
        List of {"uid": str, "from": str, "subject": str, "snippet": str}
    """
    if DRY_RUN:
        logger.info(f"[DRY_RUN] search_inbox query={query!r}")
        return [{"uid": "dry_run", "from": "dry@run.com", "subject": "Dry run result", "snippet": "DRY_RUN=true"}]

    results = []
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        imap.select("INBOX")

        _, uid_data = imap.uid("search", None, query)
        uids = uid_data[0].split()[-max_results:] if uid_data[0] else []

        for uid_bytes in uids:
            try:
                _, msg_data = imap.uid("fetch", uid_bytes, "(RFC822.HEADER)")
                import email as email_lib
                msg = email_lib.message_from_bytes(msg_data[0][1])
                results.append({
                    "uid": uid_bytes.decode(),
                    "from": msg.get("From", ""),
                    "subject": msg.get("Subject", ""),
                    "snippet": f"(header only — from {msg.get('From', '')})",
                })
            except Exception:
                continue

        imap.logout()

    except Exception as e:
        logger.error(f"search_inbox failed: {e}")

    return results
