"""WhatsApp watcher — polls WhatsApp Web every 60 seconds using Playwright.

Validation steps:
  1. python -c "from watchers.whatsapp_watcher import WhatsAppWatcher; print('import ok')"
  2. Run: .venv/bin/playwright install chromium  (one-time setup)
  3. Run: VAULT_PATH="$PWD/AI_Employee_Vault" python orchestrator.py --watcher whatsapp
  4. Scan the QR code in the opened browser window (first run only)
  5. Send a WhatsApp message to the monitored account
  6. Within 60 seconds, Needs_Action/WA_*.md should appear with valid YAML frontmatter

Persistent long-running daemon. Creates WA_*.md task files in Needs_Action/.
Tracks processed message hashes in scripts/processed_whatsapp.json.

NOTE: Requires `playwright install chromium` and a QR scan on first run.
Session is saved in whatsapp_session/ (gitignored) — subsequent runs skip QR.
"""

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from watchers.base_watcher import BaseWatcher

logger = logging.getLogger(__name__)

SESSION_DIR = Path(__file__).parent.parent / "whatsapp_session"


def _slugify(text: str, max_len: int = 30) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:max_len] or "unknown"


class WhatsAppWatcher(BaseWatcher):
    """Polls WhatsApp Web for new messages using Playwright.

    Runs as a persistent daemon (60s internal loop) — NOT a cron job.
    This is required to satisfy SC-002 (≤60s detection).
    """

    def __init__(self, vault_path: str):
        super().__init__(vault_path)
        self._registry_path = (
            Path(__file__).parent.parent / "scripts" / "processed_whatsapp.json"
        )
        self._processed: set = self._load_registry()

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

    def check_for_updates(self) -> list:
        """Poll WhatsApp Web for unread messages. Returns list of new task file paths."""
        new_tasks = []
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    str(SESSION_DIR),
                    headless=False,  # Must be visible for QR code scan on first run
                    args=["--no-sandbox"],
                )
                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate to WhatsApp Web if not already there
                if "web.whatsapp.com" not in page.url:
                    page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
                    # Wait up to 60s for QR scan / login
                    try:
                        page.wait_for_selector('[data-icon="chat"]', timeout=60000)
                    except Exception:
                        logger.info("WhatsApp Web not ready yet — QR scan may be needed")
                        browser.close()
                        return []

                # Get accessibility snapshot to find unread chats
                try:
                    snapshot = page.accessibility.snapshot()
                    messages = self._extract_unread_messages(snapshot)
                except Exception as e:
                    logger.warning(f"Could not get accessibility snapshot: {e}")
                    messages = []

                for msg in messages:
                    msg_hash = hashlib.sha256(
                        f"{msg['sender']}{msg['text']}{msg['timestamp']}".encode()
                    ).hexdigest()[:16]

                    if msg_hash in self._processed:
                        continue

                    task_path = self.create_action_file({**msg, "hash": msg_hash})
                    if task_path:
                        self._processed.add(msg_hash)
                        self._save_registry()
                        new_tasks.append(task_path)
                        logger.info(f"Created WhatsApp task: {task_path.name}")

                browser.close()

        except Exception as e:
            logger.error(f"WhatsAppWatcher non-fatal error: {e}")
            self._write_error_file("whatsapp_watcher", str(e))

        return new_tasks

    def _extract_unread_messages(self, snapshot: dict) -> list:
        """Extract unread chat messages from accessibility snapshot."""
        messages = []
        if not snapshot:
            return messages

        def traverse(node):
            if not node:
                return
            # Look for unread badge indicators
            name = node.get("name", "") or ""
            role = node.get("role", "") or ""
            if role == "listitem" and "unread" in name.lower():
                # Attempt to extract sender + preview text
                children = node.get("children", [])
                sender = ""
                text = ""
                for child in children:
                    child_name = child.get("name", "") or ""
                    child_role = child.get("role", "") or ""
                    if child_role in ("heading", "text") and not sender:
                        sender = child_name
                    elif child_role == "text" and sender:
                        text = child_name
                if sender:
                    messages.append({
                        "sender": sender,
                        "text": text or "(no preview)",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
            for child in node.get("children", []) or []:
                traverse(child)

        traverse(snapshot)
        return messages

    def create_action_file(self, item: dict) -> Path:
        """Write WA_*.md task file to Needs_Action/."""
        sender = item.get("sender", "unknown")
        text = item.get("text", "")
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        slug = _slugify(sender)
        filename = f"WA_{ts}_{slug}.md"
        task_path = Path(self.vault_path) / "Needs_Action" / filename

        received = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        content = f"""---
type: whatsapp
source: whatsapp
sender: "{sender}"
message_text: "{text.replace('"', "'")}"
message_hash: "{item.get('hash', '')}"
received: "{received}"
priority: normal
status: pending
---

## Message

{text}

## Suggested Actions

- [ ] Review message
- [ ] Draft reply (requires approval)
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
        except Exception as write_err:
            logger.error(f"Failed to write error file: {write_err}")

    def run(self) -> None:
        """Run WhatsApp watcher as persistent daemon with 60s poll interval."""
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("WhatsAppWatcher started (60s persistent daemon)")
        while True:
            self.check_for_updates()
            time.sleep(60)
