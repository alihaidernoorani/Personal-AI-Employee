"""finance_watcher.py — Gold tier: reads bank transactions from CSV → Needs_Action/FINANCE_*.md.

Extends BaseWatcher. Polls a CSV file (BANK_CSV_PATH) every 300 seconds.
New transactions are written to:
  - Needs_Action/FINANCE_<txn_id>.md
  - AI_Employee_Vault/Bank_Transactions.md  (append)
  - AI_Employee_Vault/Accounting/Current_Month.md  (append)

CSV format (header required):
  id,date,payee,amount,reference,category

Processed IDs are persisted to scripts/processed_finance.json for idempotency.
"""

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

try:
    from watchers.base_watcher import BaseWatcher
except ImportError:
    from base_watcher import BaseWatcher  # noqa: E402 — when run from watchers/ dir


SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
STATE_FILE = SCRIPTS_DIR / "processed_finance.json"

_ROW_TEMPLATE = "| {date} | {payee} | {amount} | {reference} | {category} |\n"
_BANK_HEADER = (
    "# Bank Transactions\n\n"
    "| Date | Payee | Amount | Reference | Category |\n"
    "|------|-------|--------|-----------|----------|\n"
)
_ACCOUNTING_HEADER = (
    "# Accounting — Current Month\n\n"
    "| Date | Payee | Amount | Reference | Category |\n"
    "|------|-------|--------|-----------|----------|\n"
)


class FinanceWatcher(BaseWatcher):
    """Watches a bank CSV file for new transactions."""

    def __init__(self, vault_path: str, check_interval: int = 300):
        super().__init__(vault_path, check_interval)
        self.bank_csv_path = Path(os.environ.get("BANK_CSV_PATH", ""))
        self.bank_transactions = self.vault_path / "Bank_Transactions.md"
        self.accounting_current = self.vault_path / "Accounting" / "Current_Month.md"
        self._ensure_output_files()
        self._state = self._load_state()

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def _load_state(self) -> dict:
        """Load processed IDs from scripts/processed_finance.json."""
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                self.logger.warning(f"Could not read state file: {e}")
        return {"source_type": "finance", "processed_ids": [], "last_poll": None}

    def _save_state(self) -> None:
        """Persist processed IDs to disk."""
        SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self._state, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Output file initialisation
    # ------------------------------------------------------------------

    def _ensure_output_files(self) -> None:
        """Create Bank_Transactions.md and Accounting/Current_Month.md if missing."""
        if not self.bank_transactions.exists():
            self.bank_transactions.write_text(_BANK_HEADER, encoding="utf-8")
            self.logger.info("Created Bank_Transactions.md")

        self.accounting_current.parent.mkdir(parents=True, exist_ok=True)
        if not self.accounting_current.exists():
            self.accounting_current.write_text(_ACCOUNTING_HEADER, encoding="utf-8")
            self.logger.info("Created Accounting/Current_Month.md")

    # ------------------------------------------------------------------
    # BaseWatcher interface
    # ------------------------------------------------------------------

    def check_for_updates(self) -> list:
        """Read CSV and return new (unprocessed) transaction rows."""
        self._state["last_poll"] = datetime.now(timezone.utc).isoformat() + "Z"

        if not self.bank_csv_path or not self.bank_csv_path.exists():
            if self.bank_csv_path:
                self.logger.warning(f"Bank CSV not found: {self.bank_csv_path}")
            return []

        processed = set(self._state.get("processed_ids", []))
        new_transactions = []

        try:
            with self.bank_csv_path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    txn_id = row.get("id", "").strip()
                    if not txn_id:
                        continue
                    if txn_id not in processed:
                        new_transactions.append({
                            "id": txn_id,
                            "date": row.get("date", "").strip(),
                            "payee": row.get("payee", "").strip(),
                            "amount": row.get("amount", "").strip(),
                            "reference": row.get("reference", "").strip(),
                            "category": row.get("category", "").strip(),
                        })
        except Exception as e:
            self.logger.error(f"Failed to read CSV {self.bank_csv_path}: {e}")

        return new_transactions

    def create_action_file(self, item: dict) -> Path:
        """Create FINANCE_<id>.md in Needs_Action/ and append row to both MD files."""
        txn_id = item["id"]
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        fname = f"FINANCE_{txn_id}_{ts}.md"
        target = self.needs_action / fname

        frontmatter = (
            "---\n"
            f"type: finance\n"
            f"source: csv\n"
            f"source_id: {txn_id}\n"
            f"amount: {item['amount']}\n"
            f"payee: {item['payee']}\n"
            f"reference: {item['reference']}\n"
            f"date: {item['date']}\n"
            f"category: {item['category']}\n"
            f"received: {datetime.now(timezone.utc).isoformat()}Z\n"
            "---\n\n"
            f"# Finance Transaction: {txn_id}\n\n"
            f"**Date**: {item['date']}  \n"
            f"**Payee**: {item['payee']}  \n"
            f"**Amount**: {item['amount']}  \n"
            f"**Reference**: {item['reference']}  \n"
            f"**Category**: {item['category']}  \n"
        )
        target.write_text(frontmatter, encoding="utf-8")

        # Append row to both output files
        row = _ROW_TEMPLATE.format(**item)
        with self.bank_transactions.open("a", encoding="utf-8") as f:
            f.write(row)
        with self.accounting_current.open("a", encoding="utf-8") as f:
            f.write(row)

        # Mark processed
        self._state["processed_ids"].append(txn_id)
        self._save_state()

        self.logger.info(f"Finance transaction processed: {txn_id}")
        return target
