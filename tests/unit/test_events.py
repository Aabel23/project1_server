from pathlib import Path

import pytest

from flexmix_machine.events import EventUploadError, LocalOrderOutbox


def test_outbox_ack_retry_and_note_redaction(tmp_path: Path):
    outbox = LocalOrderOutbox(tmp_path / "events.json", machine_mid=7)
    event = outbox.append_order_ticket(
        serial="S-1", status="used", drink_id="latte", price_cents=350,
        occurred_at="2026-09-17T10:00:00Z", note="private customer note",
    )
    assert "note" not in event
    sent = []
    with pytest.raises(EventUploadError):
        outbox.upload(lambda batch: (_ for _ in ()).throw(OSError("offline")))
    assert outbox.acked_cursor == 0

    def acknowledge(batch):
        sent.append(batch)
        return {"ack": "ok", "cursor_to": batch["cursor_to"]}

    assert outbox.upload(acknowledge) == 1
    assert outbox.acked_cursor == 1
    assert outbox.pending_batch() is None
    assert "private customer note" not in (tmp_path / "events.json").read_text()
    assert outbox.upload(acknowledge) == 1
    assert len(sent) == 1


def test_invalid_ack_does_not_advance(tmp_path: Path):
    outbox = LocalOrderOutbox(tmp_path / "events.json", machine_mid=7)
    outbox.append_order_ticket(
        serial="S-1", status="unused", drink_id="latte", price_cents=350,
        occurred_at="2026-09-17T10:00:00Z",
    )
    with pytest.raises(EventUploadError):
        outbox.upload(lambda _: {"ack": "ok", "cursor_to": 999})
    assert outbox.acked_cursor == 0
