from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from flexmix_hub.api.machine import authenticated_machine
from flexmix_hub.infrastructure.database.session import get_session
from flexmix_hub.modules.fleet.models import MachineRegistry
from flexmix_hub.modules.monitoring.models import MachineHeartbeat

router = APIRouter(tags=["monitoring"])
HEARTBEAT_STALE_SECONDS = 120


class HeartbeatRequest(BaseModel):
    reported_at: datetime
    status: str = Field(min_length=1, max_length=32)
    schema_version: str = Field(min_length=1, max_length=64)
    selling_available: bool
    detail: str | None = Field(default=None, max_length=1000)


@router.post("/v1/beat")
def receive_heartbeat(
    heartbeat: HeartbeatRequest,
    machine: MachineRegistry = Depends(authenticated_machine),
    session: Session = Depends(get_session),
):
    now = datetime.now(timezone.utc)
    current = session.get(MachineHeartbeat, machine.mid)
    if current is None:
        current = MachineHeartbeat(machine_mid=machine.mid)
        session.add(current)
    current.received_at = now
    current.reported_at = heartbeat.reported_at
    current.status = heartbeat.status
    current.schema_version = heartbeat.schema_version
    current.selling_available = heartbeat.selling_available
    current.detail = heartbeat.detail
    session.commit()
    return {"ack": "ok", "mid": machine.mid, "received_at": now.isoformat()}


@router.get("/v1/prototype/monitoring/machines/{mid}")
def machine_status(mid: int, session: Session = Depends(get_session)):
    heartbeat = session.get(MachineHeartbeat, mid)
    if heartbeat is None:
        raise HTTPException(status_code=404, detail="Heartbeat not found")
    received_at = heartbeat.received_at
    if received_at.tzinfo is None:
        received_at = received_at.replace(tzinfo=timezone.utc)
    online = received_at >= datetime.now(timezone.utc) - timedelta(seconds=HEARTBEAT_STALE_SECONDS)
    return {
        "mid": mid, "online": online, "status": heartbeat.status,
        "selling_available": heartbeat.selling_available,
        "schema_version": heartbeat.schema_version,
        "received_at": heartbeat.received_at,
    }
