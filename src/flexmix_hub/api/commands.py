import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from flexmix_hub.api.machine import authenticated_machine
from flexmix_hub.infrastructure.database.session import get_session
from flexmix_hub.modules.commands.models import CommandStatus, MachineCommand
from flexmix_hub.modules.fleet.models import MachineRegistry

router = APIRouter(tags=["commands"])


class CreateCommand(BaseModel):
    machine_mid: int = Field(ge=1)


def require_token(request: Request, token: str | None = Header(default=None, alias="X-Flexmix-Prototype-Enrollment-Token")):
    expected = request.app.state.settings.prototype_enrollment_token()
    if expected is None or token is None or token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/v1/prototype/commands", status_code=201)
def create_command(data: CreateCommand, _: None = Depends(require_token), session: Session = Depends(get_session)):
    if session.get(MachineRegistry, data.machine_mid) is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    command = MachineCommand(
        command_id=str(uuid4()), machine_mid=data.machine_mid, kind="refresh_state",
        payload=json.dumps({"kind": "refresh_state"}), status=CommandStatus.PENDING,
        attempts=0, created_at=datetime.now(timezone.utc),
    )
    session.add(command); session.commit()
    return {"command_id": command.command_id, "status": command.status}


@router.get("/v1/commands/poll")
def poll_commands(machine: MachineRegistry = Depends(authenticated_machine), session: Session = Depends(get_session)):
    command = session.scalar(select(MachineCommand).where(
        MachineCommand.machine_mid == machine.mid,
        MachineCommand.status.in_([CommandStatus.PENDING, CommandStatus.DELIVERED, CommandStatus.FAILED]),
    ).order_by(MachineCommand.created_at).limit(1))
    if command is None:
        return {"commands": []}
    command.status = CommandStatus.DELIVERED
    command.attempts += 1
    command.delivered_at = datetime.now(timezone.utc)
    session.commit()
    return {"commands": [{"command_id": command.command_id, "kind": command.kind, "payload": json.loads(command.payload)}]}


class CommandAck(BaseModel):
    command_id: UUID
    status: str = Field(pattern="^(acknowledged|failed)$")
    error: str | None = Field(default=None, max_length=255)


@router.post("/v1/commands/ack")
def acknowledge_command(ack: CommandAck, machine: MachineRegistry = Depends(authenticated_machine), session: Session = Depends(get_session)):
    command = session.scalar(select(MachineCommand).where(
        MachineCommand.command_id == str(ack.command_id), MachineCommand.machine_mid == machine.mid
    ))
    if command is None:
        raise HTTPException(status_code=404, detail="Command not found")
    if command.status is CommandStatus.ACKNOWLEDGED and ack.status == "acknowledged":
        return {"ack": "ok", "command_id": command.command_id, "status": command.status}
    command.status = CommandStatus.ACKNOWLEDGED if ack.status == "acknowledged" else CommandStatus.FAILED
    command.last_error = ack.error
    command.acknowledged_at = datetime.now(timezone.utc) if ack.status == "acknowledged" else None
    session.commit()
    return {"ack": "ok", "command_id": command.command_id, "status": command.status}
