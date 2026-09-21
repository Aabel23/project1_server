"""Local order-ticket outbox and retry cursor for the prototype machine."""

import json
import os
from pathlib import Path
from typing import Any, Callable
from uuid import UUID, uuid4


class EventUploadError(RuntimeError):
    pass


class LocalOrderOutbox:
    def __init__(self, path: Path, *, machine_mid: int):
        self.path = path
        self.machine_mid = machine_mid

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"next_cursor": 1, "acked_cursor": 0, "events": []}
        return json.loads(self.path.read_text())

    def _write(self, state: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(state, sort_keys=True, separators=(",", ":")))
        os.replace(tmp, self.path)

    def append_order_ticket(
        self, *, serial: str, status: str, drink_id: str, price_cents: int, occurred_at: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        state = self._read()
        event = {
            "event_id": str(uuid4()), "cursor": state["next_cursor"],
            "serial": serial, "status": status, "drink_id": drink_id,
            "price_cents": price_cents, "occurred_at": occurred_at,
        }
        # note is intentionally accepted for local ticket use but never serialized.
        state["next_cursor"] += 1
        state["events"].append(event)
        self._write(state)
        return event

    def pending_batch(self, limit: int = 100) -> dict[str, Any] | None:
        state = self._read()
        pending = [e for e in state["events"] if e["cursor"] > state["acked_cursor"]][:limit]
        if not pending:
            return None
        return {"cursor_from": state["acked_cursor"], "cursor_to": pending[-1]["cursor"], "rows": pending}

    def acknowledge(self, cursor_to: int) -> None:
        state = self._read()
        pending = self.pending_batch()
        if pending is None or cursor_to != pending["cursor_to"]:
            raise EventUploadError("Invalid event acknowledgement")
        state["acked_cursor"] = cursor_to
        state["events"] = [e for e in state["events"] if e["cursor"] > cursor_to]
        self._write(state)

    def upload(self, send: Callable[[dict[str, Any]], dict[str, Any]]) -> int:
        batch = self.pending_batch()
        if batch is None:
            return self._read()["acked_cursor"]
        try:
            acknowledgement = send(batch)
        except Exception as error:
            raise EventUploadError("Event upload failed") from error
        if acknowledgement.get("ack") != "ok" or acknowledgement.get("cursor_to") != batch["cursor_to"]:
            raise EventUploadError("Invalid event acknowledgement")
        self.acknowledge(batch["cursor_to"])
        return batch["cursor_to"]

    @property
    def acked_cursor(self) -> int:
        return self._read()["acked_cursor"]
