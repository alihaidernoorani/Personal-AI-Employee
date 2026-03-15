"""Approval watcher — polls Approved/ and Rejected/ vault folders.

When an APPROVAL_*.md file appears in Approved/, writes an ACTION_*.md
trigger to Needs_Action/ for the execute-plan skill to process.
When a file appears in Rejected/, logs it and archives — no action trigger.

Tracks processed filenames in scripts/processed_approvals.json.
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from watchers.base_watcher import BaseWatcher

logger = logging.getLogger(__name__)


def _parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown content."""
    try:
        import yaml
        if not content.startswith("---"):
            return {}
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}
        return yaml.safe_load(parts[1]) or {}
    except Exception:
        return {}


class ApprovalWatcher(BaseWatcher):
    """Polls Approved/ every 5 seconds for new approval files."""

    def __init__(self, vault_path: str):
        super().__init__(vault_path)
        self._registry_path = (
            Path(__file__).parent.parent / "scripts" / "processed_approvals.json"
        )
        self._processed: set = self._load_registry()
        self._approved_dir = Path(vault_path) / "Approved"
        self._rejected_dir = Path(vault_path) / "Rejected"

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
        """Scan Approved/ and Rejected/ for new files."""
        new_triggers = []

        # Process approved files
        try:
            for approval_file in sorted(self._approved_dir.glob("APPROVAL_*.md")):
                if approval_file.name in self._processed:
                    continue

                try:
                    content = approval_file.read_text(encoding="utf-8")
                    frontmatter = _parse_frontmatter(content)

                    action_type = frontmatter.get("action", "unknown")
                    parameters = frontmatter.get("parameters", {})
                    plan_file = frontmatter.get("plan_file", "")

                    trigger_path = self._write_action_trigger(
                        approval_file.name, action_type, parameters, plan_file
                    )

                    self._processed.add(approval_file.name)
                    self._save_registry()
                    new_triggers.append(trigger_path)
                    logger.info(f"Approval detected: {approval_file.name} → {trigger_path.name}")

                except Exception as e:
                    logger.error(f"Error processing approval {approval_file.name}: {e}")

        except FileNotFoundError:
            self._approved_dir.mkdir(parents=True, exist_ok=True)

        # Log rejected files
        try:
            for rejected_file in sorted(self._rejected_dir.glob("APPROVAL_*.md")):
                if rejected_file.name in self._processed:
                    continue
                logger.info(f"Rejection noted (archived): {rejected_file.name}")
                self._processed.add(rejected_file.name)
                self._save_registry()
                self._log_rejection(rejected_file.name)

        except FileNotFoundError:
            self._rejected_dir.mkdir(parents=True, exist_ok=True)

        return new_triggers

    def _write_action_trigger(
        self, approval_filename: str, action_type: str, parameters: dict, plan_file: str
    ) -> Path:
        """Write ACTION_*.md trigger to Needs_Action/."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        slug = action_type.replace("_", "-")
        filename = f"ACTION_{ts}_{slug}.md"
        trigger_path = Path(self.vault_path) / "Needs_Action" / filename

        content = f"""---
type: action_trigger
source: system
action_type: {action_type}
approval_file: "{approval_filename}"
action_params: '{json.dumps(parameters)}'
received: "{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}"
priority: high
status: pending
---

## Action Details

Execute the approved action referenced in `{approval_filename}`.
"""
        trigger_path.write_text(content, encoding="utf-8")
        return trigger_path

    def _log_rejection(self, filename: str) -> None:
        """Log rejection to Logs/."""
        try:
            log_dir = Path(self.vault_path) / "Logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "action_type": "approval_rejected",
                "actor": "approval_watcher",
                "target": filename,
                "parameters": {},
                "approval_status": "rejected",
                "result": "archived",
            }
            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log rejection: {e}")

    def create_action_file(self, item) -> Path:
        """Required by BaseWatcher — not used directly (see _write_action_trigger)."""
        return None

    def run(self) -> None:
        """Run approval watcher — polls every 5 seconds."""
        logger.info("ApprovalWatcher started (5s poll)")
        while True:
            self.check_for_updates()
            time.sleep(5)
