"""Minimal authenticated machine-to-Hub API for Phase 02.

No selling, mixing, event, catalogue, command, heartbeat, backup or release
operation is exposed here.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from flexmix_hub.infrastructure.database.session import get_session
from flexmix_hub.infrastructure.security.device_identity import (
    DeviceIdentityError,
    verify_request_signature,
)
from flexmix_hub.modules.fleet.models import MachineRegistry, MachineStatus

router = APIRouter(prefix="/v1/machine", tags=["machine"])
# Retained as a contract constant for the Phase 02 client/test helper.
SELF_PATH = "/v1/machine/self"


class MachineSelfResponse(BaseModel):
    mid: int
    device_uuid: UUID
    status: MachineStatus
    tailnet_tag: str


def authenticated_machine(
    request: Request,
    x_flexmix_device_uuid: str | None = Header(default=None),
    x_flexmix_device_signature: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> MachineRegistry:
    """Resolve the registered machine; MID never comes from the client."""
    try:
        device_uuid = UUID(x_flexmix_device_uuid or "")
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid machine credential") from error

    machine = session.query(MachineRegistry).filter_by(device_uuid=str(device_uuid)).one_or_none()
    if machine is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid machine credential")
    if machine.status is MachineStatus.DECOMMISSIONED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Machine is decommissioned")
    if x_flexmix_device_signature is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid machine credential")
    try:
        verify_request_signature(
            machine.device_public_key,
            x_flexmix_device_signature,
            method=request.method,
            path=request.url.path,
            device_uuid=device_uuid,
        )
    except DeviceIdentityError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid machine credential") from error
    return machine


@router.get("/self", response_model=MachineSelfResponse)
def machine_self(machine: MachineRegistry = Depends(authenticated_machine)) -> MachineSelfResponse:
    return MachineSelfResponse(
        mid=machine.mid,
        device_uuid=UUID(machine.device_uuid),
        status=machine.status,
        tailnet_tag=machine.tailnet_tag,
    )
