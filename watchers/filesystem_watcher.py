"""filesystem_watcher.py — Watches an Inbox drop folder for new files.

Any file dropped into AI_Employee_Vault/Inbox/ is automatically copied to
Needs_Action/ with a structured .md metadata file for Claude to process.

Usage:
    python filesystem_watcher.py
    # or with explicit vault path:
    VAULT_PATH=/path/to/AI_Employee_Vault python filesystem_watcher.py
"""

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

# Add parent dir to path so base_watcher is importable when run directly
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher  # noqa: E402


class DropFolderHandler(FileSystemEventHandler):
    """Watchdog event handler: reacts to new files dropped in Inbox."""

    def __init__(self, watcher: "FilesystemWatcher"):
        self.watcher = watcher

    def on_created(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        # Ignore hidden/temp files (e.g. .DS_Store, Thumbs.db, ~lockfiles)
        if source.name.startswith(".") or source.name.startswith("~"):
            return
        self.watcher.logger.info(f"New file detected: {source.name}")
        self.watcher.create_action_file(source)


class FilesystemWatcher(BaseWatcher):
    """
    Monitors AI_Employee_Vault/Inbox/ for dropped files.

    When a file appears:
    1. Copies it to Needs_Action/ prefixed with FILE_
    2. Creates a companion .md metadata file with YAML frontmatter
    3. Logs the event to Logs/YYYY-MM-DD.json
    """

    def __init__(self, vault_path: str):
        super().__init__(vault_path, check_interval=5)
        self.inbox = self.vault_path / "Inbox"
        self.inbox.mkdir(parents=True, exist_ok=True)
        self._observer = None

    def check_for_updates(self) -> list:
        # Watchdog handles detection via events; this is a no-op for the base loop.
        return []

    def create_action_file(self, source: Path) -> Path:
        """Copy source file into Needs_Action and write a metadata .md file."""
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        safe_stem = source.stem.replace(" ", "_")
        dest_name = f"FILE_{timestamp}_{safe_stem}{source.suffix}"
        dest = self.needs_action / dest_name
        meta_path = self.needs_action / f"FILE_{timestamp}_{safe_stem}.md"

        # Copy the actual file
        shutil.copy2(source, dest)

        # Write structured metadata for Claude
        size_bytes = source.stat().st_size
        content = f"""---
type: file_drop
original_name: {source.name}
copied_to: {dest_name}
size_bytes: {size_bytes}
received: {datetime.utcnow().isoformat()}Z
priority: normal
status: pending
---

## File Dropped for Processing

A new file was detected in the Inbox and is ready for review.

| Field | Value |
|-------|-------|
| Original name | `{source.name}` |
| File size | {size_bytes:,} bytes |
| Received | {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} |
| Copied to | `{dest_name}` |

## Suggested Actions

- [ ] Review file contents
- [ ] Determine if action is required
- [ ] Move this file to `/Done/` when complete, or `/Rejected/` to discard
"""
        meta_path.write_text(content, encoding="utf-8")
        self.log_action("file_drop_detected", source.name, "success", {"dest": dest_name})
        return meta_path

    def run(self):
        """Start watchdog observer on Inbox directory."""
        self.logger.info(f"Watching inbox: {self.inbox}")
        self.logger.info(f"Action files will appear in: {self.needs_action}")

        handler = DropFolderHandler(self)
        self._observer = PollingObserver(timeout=3)
        self._observer.schedule(handler, str(self.inbox), recursive=False)
        self._observer.start()

        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Stopping watcher...")
            self._observer.stop()
        self._observer.join()
        self.logger.info("Watcher stopped.")


if __name__ == "__main__":
    vault_path = os.environ.get(
        "VAULT_PATH",
        str(Path(__file__).parent.parent / "AI_Employee_Vault"),
    )
    watcher = FilesystemWatcher(vault_path)
    watcher.run()
