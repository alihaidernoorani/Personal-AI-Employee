"""base_watcher.py — Abstract base class for all AI Employee watchers."""

import time
import logging
import json
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.logs_dir = self.vault_path / "Logs"
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def check_for_updates(self) -> list:
        """Return list of new items to process."""
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create a .md file in Needs_Action folder and return its path."""
        pass

    def log_action(self, action_type: str, target: str, result: str, parameters: dict = None):
        """Append a structured audit log entry to today's log file."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action_type": action_type,
            "actor": self.__class__.__name__,
            "target": target,
            "parameters": parameters or {},
            "approval_status": "auto",
            "approved_by": "system",
            "result": result,
        }
        log_file = self.logs_dir / f"{datetime.utcnow().strftime('%Y-%m-%d')}.json"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def run(self):
        self.logger.info(f"Starting {self.__class__.__name__} (interval={self.check_interval}s)")
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    path = self.create_action_file(item)
                    self.logger.info(f"Created action file: {path.name}")
                    self.log_action("action_file_created", str(path.name), "success")
            except Exception as e:
                self.logger.error(f"Error in watch loop: {e}")
                self.log_action("watch_loop_error", "", "failure", {"error": str(e)})
            time.sleep(self.check_interval)
