"""Software-only local order_ticket runtime for the prototype machine."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from .events import LocalOrderOutbox, EventUploadError

class TicketNotFound(RuntimeError): pass
class TicketNotClaimable(RuntimeError): pass

class LocalOrderRuntime:
    """Local source of truth; Hub sync is explicitly outside ticket mutations."""
    def __init__(self, database: Path, outbox: LocalOrderOutbox):
        self.database = Path(database); self.outbox = outbox
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS order_ticket (serial TEXT PRIMARY KEY, drink_id TEXT NOT NULL, price_cents INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, claimed_at TEXT, completed_at TEXT)")

    def _connect(self):
        db = sqlite3.connect(self.database, isolation_level=None)
        db.execute("PRAGMA journal_mode=WAL"); return db

    def create_ticket(self, serial: str, drink_id: str, price_cents: int) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._connect() as db:
                db.execute("INSERT INTO order_ticket(serial,drink_id,price_cents,status,created_at) VALUES(?,?,?,?,?)", (serial, drink_id, price_cents, "unused", now))
        except sqlite3.IntegrityError as exc: raise ValueError("duplicate ticket serial") from exc
        self.outbox.append_order_ticket(serial=serial, status="unused", drink_id=drink_id, price_cents=price_cents, occurred_at=now)
        return self.get_ticket(serial)

    def claim_ticket(self, serial: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT drink_id,price_cents,status,created_at FROM order_ticket WHERE serial=?", (serial,)).fetchone()
            if row is None: db.rollback(); raise TicketNotFound(serial)
            changed = db.execute("UPDATE order_ticket SET status='in_progress',claimed_at=? WHERE serial=? AND status='unused'", (now, serial)).rowcount
            if changed != 1: db.rollback(); raise TicketNotClaimable(serial)
            db.commit()
        self.outbox.append_order_ticket(serial=serial, status="in_progress", drink_id=row[0], price_cents=row[1], occurred_at=now)
        return self.get_ticket(serial)

    def complete_ticket(self, serial: str) -> dict[str, Any]:
        return self._transition(serial, "used", "completed_at")

    def _transition(self, serial: str, status: str, column: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            row = db.execute("SELECT drink_id,price_cents,status FROM order_ticket WHERE serial=?", (serial,)).fetchone()
            if row is None: raise TicketNotFound(serial)
            if row[2] == status: return self.get_ticket(serial)
            if row[2] != "in_progress": raise TicketNotClaimable(serial)
            db.execute(f"UPDATE order_ticket SET status=?, {column}=? WHERE serial=?", (status, now, serial)); db.commit()
        self.outbox.append_order_ticket(serial=serial, status=status, drink_id=row[0], price_cents=row[1], occurred_at=now)
        return self.get_ticket(serial)

    def get_ticket(self, serial: str) -> dict[str, Any]:
        with self._connect() as db:
            row = db.execute("SELECT serial,drink_id,price_cents,status,created_at,claimed_at,completed_at FROM order_ticket WHERE serial=?", (serial,)).fetchone()
        if row is None: raise TicketNotFound(serial)
        return dict(zip(("serial","drink_id","price_cents","status","created_at","claimed_at","completed_at"), row))

    def sync(self, send: Callable[[dict[str, Any]], dict[str, Any]]) -> int:
        """Best-effort reconnect sync; failures leave the outbox untouched."""
        return self.outbox.upload(send)
