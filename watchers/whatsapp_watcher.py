"""
WhatsApp Watcher — persistent session, unread detection, no duplicates.

Design:
- ONE browser launch via launch_persistent_context (session saved to whatsapp_session/)
- QR scan only on first run; subsequent runs auto-authenticate from saved session
- Polls every 30s using time.sleep (non-blocking for Playwright event loop)
- Deduplication via SHA-256(sender + text) — timestamps never included in hash
- Chat grid uses role="grid" + role="row" (NOT role="listitem")
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from watchers.base_watcher import BaseWatcher

logger = logging.getLogger(__name__)

SESSION_DIR = Path(__file__).parent.parent / "whatsapp_session"

PRIORITY_KEYWORDS = {
    "urgent": "urgent",
    "asap": "high",
    "invoice": "high",
    "payment": "high",
}


def detect_priority(text: str) -> str:
    text_lower = text.lower()
    for keyword, level in PRIORITY_KEYWORDS.items():
        if keyword in text_lower:
            return level
    return "normal"


class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path: str, check_interval: int = 30, headless: bool = False):
        super().__init__(vault_path, check_interval=check_interval)
        self._registry_path = (
            Path(__file__).parent.parent / "scripts" / "processed_whatsapp.json"
        )
        self._processed = self._load_registry()
        self._headless = headless

    # ------------------------------------------------------------------ registry

    def _load_registry(self) -> set:
        try:
            return set(json.loads(self._registry_path.read_text())["processed"])
        except Exception:
            return set()

    def _save_registry(self):
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._registry_path.write_text(
            json.dumps({"processed": list(self._processed)}, indent=2)
        )

    def _hash_message(self, sender: str, text: str) -> str:
        """Stable dedup key: sender + message text only. No timestamps."""
        return hashlib.sha256(f"{sender}:{text}".encode()).hexdigest()[:16]

    # ------------------------------------------------------------------ output

    def check_for_updates(self) -> List[Path]:
        """Not used — this watcher drives itself via run()."""
        return []

    def create_action_file(self, msg: Dict) -> Path:
        sender = msg["sender"]
        text = msg["text"]
        priority = msg["priority"]

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"WA_{ts}_{sender[:20].replace(' ', '_')}.md"
        path = self.needs_action / filename

        content = (
            f"---\n"
            f"type: whatsapp\n"
            f'sender: "{sender}"\n'
            f"priority: {priority}\n"
            f'received: "{datetime.now(timezone.utc).isoformat()}"\n'
            f"status: pending\n"
            f"---\n\n"
            f"## Message from {sender}\n\n"
            f"{text}\n"
        )
        path.write_text(content, encoding="utf-8")
        logger.info(f"Created action file: {path.name}")
        return path

    # ------------------------------------------------------------------ browser

    def run(self):
        from playwright.sync_api import sync_playwright

        SESSION_DIR.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            logger.info("Launching browser (persistent session, single launch)...")

            # --enable-unsafe-swiftshader + --no-sandbox together cause exit-code-21
            # on Windows when launched from certain parent environments (WSL, CI).
            # Ignoring both flags fixes the crash; Windows Chrome doesn't need them.
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(SESSION_DIR),
                headless=self._headless,
                ignore_default_args=[
                    "--enable-unsafe-swiftshader",
                    "--no-sandbox",
                ],
                args=[
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            # ONE page for the entire session — never create a second one
            page = context.new_page()
            page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

            logger.info("Waiting for WhatsApp login (scan QR code if prompted)...")
            try:
                # [data-testid="search"] only appears when authenticated
                # Allow 5 minutes for QR scan
                page.wait_for_selector('[data-testid="search"]', timeout=300000)
                logger.info("WhatsApp authenticated. Watcher starting...")
            except Exception:
                logger.warning("Login wait timed out — continuing anyway.")

            # Continuous poll loop — browser is NEVER relaunched inside here
            while True:
                try:
                    self._poll(page)
                except KeyboardInterrupt:
                    logger.info("Stopped by user.")
                    break
                except Exception as e:
                    logger.error(f"Poll error: {e}")

                # time.sleep instead of page.wait_for_timeout to avoid
                # blocking Playwright's internal event loop
                time.sleep(self.check_interval)

    # ------------------------------------------------------------------ polling

    def _poll(self, page):
        """Single poll cycle: find unread chats, extract last message, write task file."""

        # WhatsApp Web sidebar: role="grid" (the list) + role="row" (each chat)
        # Confirmed via DOM inspection — role="listitem" does NOT exist here
        unread = page.evaluate("""
            () => {
                const grid = document.querySelector('[aria-label="Chat list"][role="grid"]');
                if (!grid) return [];

                const results = [];
                grid.querySelectorAll('[role="row"]').forEach(row => {
                    // Only process rows that have the unread count badge
                    if (!row.querySelector('[data-testid="icon-unread-count"]')) return;

                    // Use span[title] for the contact name — most reliable in WhatsApp Web
                    // Fallback: filter out "X unread message(s)" lines from innerText
                    let sender = '';
                    const titleEl = row.querySelector('span[title]');
                    if (titleEl && titleEl.title.trim()) {
                        sender = titleEl.title.trim();
                    } else {
                        const lines = (row.innerText || '').trim().split('\\n').filter(Boolean);
                        // Skip lines that look like unread count notifications
                        const nonBadge = lines.filter(l => !/^\\d+ unread/i.test(l));
                        sender = nonBadge[0] || lines[0] || '';
                    }

                    if (sender.length > 1) {
                        // Get message preview: last text line that isn't timestamp or badge
                        const lines = (row.innerText || '').trim().split('\\n').filter(Boolean);
                        const preview = lines.filter(l =>
                            !/^\\d+ unread/i.test(l) && !/^\\d{1,2}:\\d{2}/.test(l) && l !== sender
                        ).join(' ');

                        results.push({ sender, preview });
                    }
                });
                return results;
            }
        """)

        if not unread:
            logger.info("[POLL] No unread chats.")
            return

        logger.info(f"[POLL] {len(unread)} unread chat(s) found.")

        for chat in unread:
            sender = chat.get("sender", "").strip()
            preview = chat.get("preview", "")
            if not sender:
                continue

            # Skip if preview already processed (fast path before clicking)
            preview_hash = self._hash_message(sender, preview)
            if preview_hash in self._processed:
                continue

            try:
                # Open the chat to read the full last message
                page.locator(
                    f'[aria-label="Chat list"] [role="row"]:has-text("{sender}")'
                ).first.click(timeout=5000)
                page.wait_for_timeout(1200)

                # Extract last message from the conversation panel
                last_msg = page.evaluate("""
                    () => {
                        const msgs = document.querySelectorAll('[data-testid="msg-container"]');
                        if (!msgs.length) return '';
                        return (msgs[msgs.length - 1].innerText || '').trim();
                    }
                """) or preview

                msg_hash = self._hash_message(sender, last_msg)
                if msg_hash in self._processed:
                    continue

                priority = detect_priority(last_msg)
                self.create_action_file({"sender": sender, "text": last_msg, "priority": priority})
                self._processed.add(msg_hash)
                self._save_registry()
                logger.info(f"[NEW] {sender} | priority={priority}")

            except Exception as e:
                logger.warning(f"Could not open chat '{sender}': {e}")
                # Fallback: save with preview text rather than silently dropping
                if preview and preview_hash not in self._processed:
                    priority = detect_priority(preview)
                    self.create_action_file({"sender": sender, "text": preview, "priority": priority})
                    self._processed.add(preview_hash)
                    self._save_registry()
                    logger.info(f"[NEW/preview] {sender} | priority={priority}")
