"""At-least-once order event ingestion; no Hub order arbitration."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from flexmix_hub.api.machine import authenticated_machine
from flexmix_hub.infrastructure.database.session import get_session
from flexmix_hub.modules.events.models import MachineOrderEvent
from flexmix_hub.modules.fleet.models import MachineRegistry

router = APIRouter(tags=["events"])


class OrderEvent(BaseModel):
    event_id: UUID
    cursor: int = Field(ge=1)
    serial: str = Field(min_length=1, max_length=128)
    status: str = Field(min_length=1, max_length=32)
    drink_id: str = Field(min_length=1, max_length=64)
    price_cents: int = Field(ge=0)
    occurred_at: datetime


class EventBatch(BaseModel):
    cursor_from: int = Field(ge=0)
    cursor_to: int = Field(ge=1)
    rows: list[OrderEvent] = Field(min_length=1, max_length=500)


@router.post("/v1/events")
def receive_events(
    batch: EventBatch,
    request: Request,
    machine: MachineRegistry = Depends(authenticated_machine),
    session: Session = Depends(get_session),
) -> dict[str, int | str]:
    if batch.cursor_to < batch.cursor_from or any(row.cursor > batch.cursor_to for row in batch.rows):
        raise HTTPException(status_code=400, detail="Invalid event cursor range")
    # Prototype requires contiguous batch bounds; retries use the same IDs safely.
    cursors = sorted({row.cursor for row in batch.rows})
    if cursors[0] <= batch.cursor_from or cursors[-1] != batch.cursor_to:
        raise HTTPException(status_code=400, detail="Invalid event cursor range")
    for row in batch.rows:
        existing = session.scalar(select(MachineOrderEvent).where(
            MachineOrderEvent.machine_mid == machine.mid,
            MachineOrderEvent.event_id == str(row.event_id),
        ))
        if existing is not None:
            continue
        session.add(MachineOrderEvent(
                machine_mid=machine.mid,
                event_id=str(row.event_id),
                cursor=row.cursor,
                serial=row.serial,
                status=row.status,
                drink_id=row.drink_id,
                price_cents=row.price_cents,
                occurred_at=row.occurred_at,
            ))
    session.commit()
    return {"ack": "ok", "cursor_to": batch.cursor_to}
