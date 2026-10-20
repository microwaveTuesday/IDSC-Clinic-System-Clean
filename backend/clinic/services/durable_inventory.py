"""Separate simulated Inventory ledger. No Clinic ORM or real-provider contract.

SQLite transactions serialize this optional classroom provider across processes.
The database must be backed up independently with Clinic writes quiesced.
"""

import json
import sqlite3
from contextlib import contextmanager, closing
from pathlib import Path
from threading import RLock


class DurableInventoryMixin:
    durable = True

    def __init__(self, path):
        super().__init__()
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ledger_lock = RLock()
        self._depth = 0
        self.restocks = {}
        self.notifications = []
        self.read_notifications = {}
        self._operation_keys = {}
        with closing(sqlite3.connect(self.path, timeout=30)) as db, db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS requests (scope TEXT, key TEXT, fingerprint TEXT NOT NULL, status TEXT NOT NULL, PRIMARY KEY(scope,key))"
            )
            db.execute("INSERT OR IGNORE INTO state VALUES (1,?)", (self._encode(),))

    def _encode(self):
        return json.dumps(
            {
                "medicines": self._medicines,
                "transactions": self._transactions,
                "restocks": self.restocks,
                "notifications": self.notifications,
                "reads": {str(k): list(v) for k, v in self.read_notifications.items()},
                "operations": self._operation_keys,
            }
        )

    def _load(self, body):
        state = json.loads(body)
        self._medicines = state["medicines"]
        self._transactions = state["transactions"]
        # Keep collection identity stable for the mock workspace compatibility API.
        self.restocks.clear()
        self.restocks.update(state["restocks"])
        self.notifications[:] = state["notifications"]
        self.read_notifications.clear()
        self.read_notifications.update(
            {int(k): set(v) for k, v in state["reads"].items()}
        )
        self._operation_keys = state["operations"]

    @contextmanager
    def workspace(self):
        with self._ledger_lock:
            if self._depth:
                yield
                return
            with closing(sqlite3.connect(self.path, timeout=30)) as db, db:
                db.execute("BEGIN IMMEDIATE")
                self._load(
                    db.execute("SELECT body FROM state WHERE id=1").fetchone()[0]
                )
                self._depth += 1
                try:
                    yield
                    db.execute("UPDATE state SET body=? WHERE id=1", (self._encode(),))
                finally:
                    self._depth -= 1

    def list_medicines(self, *args, **kwargs):
        with self.workspace():
            return super().list_medicines(*args, **kwargs)

    def get_medicine(self, medicine_id):
        with self.workspace():
            return super().get_medicine(medicine_id)

    def deduct_stock(self, medicine_id, quantity, operation_key=None):
        with self.workspace():
            signature = [str(medicine_id), quantity]
            if operation_key in self._operation_keys:
                previous = self._operation_keys[operation_key]
                if previous["signature"] != signature:
                    raise ValueError(
                        "Inventory operation key reused with different values."
                    )
                return previous["transaction_id"]
            result = super().deduct_stock(medicine_id, quantity)
            if operation_key:
                self._operation_keys[operation_key] = {
                    "signature": signature,
                    "transaction_id": result,
                }
            return result

    def restore_stock(self, transaction_id):
        with self.workspace():
            source = self._transactions.get(transaction_id)
            if source and source.get("type") != "DEDUCTION":
                raise ValueError("Only a deduction transaction can be restored.")
            for ref, row in self._transactions.items():
                if row.get("source_transaction_id") == transaction_id:
                    return ref
            return super().restore_stock(transaction_id)

    def claim_request(self, scope, key, fingerprint):
        """Durable ambiguity fence, independent of the Clinic transaction.

        An interrupted request remains pending. Never blindly repeat external
        side effects even if its Clinic transaction was rolled back.
        """
        with closing(sqlite3.connect(self.path, timeout=30)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT fingerprint,status FROM requests WHERE scope=? AND key=?",
                (scope, key),
            ).fetchone()
            if row:
                if row[0] != fingerprint:
                    raise ValueError("Idempotency key reused with a different request.")
                return row[1]
            db.execute(
                "INSERT INTO requests VALUES (?,?,?,?)",
                (scope, key, fingerprint, "pending"),
            )
            return "new"

    def finish_request(self, scope, key):
        with closing(sqlite3.connect(self.path, timeout=30)) as db, db:
            db.execute(
                "UPDATE requests SET status=? WHERE scope=? AND key=?",
                ("complete", scope, key),
            )
