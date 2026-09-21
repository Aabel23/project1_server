"""Temporary Phase 01 prototype enrollment API.

The endpoint is deliberately under /v1/prototype: its identity proof and wire
contract must be replaced after Q-12 and Q-15 are decided.
"""

import secrets
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from flexmix_hub.config import Settings
from flexmix_hub.infrastructure.database.session import get_session
from flexmix_hub.infrastructure.security.device_identity import decode_public_key
from flexmix_hub.modules.fleet.models import MachineRegistry, MachineStatus
from flexmix_hub.modules.fleet.service import (
    DuplicateMachineError,
    MachineAlreadyDecommissionedError,
    MachineNotFoundError,
    MidExhaustedError,
    decommission_machine,
    register_machine,
)

router = APIRouter(prefix="/v1/prototype/fleet", tags=["prototype-fleet"])


class RegisterMachineRequest(BaseModel):
    device_uuid: UUID
    # Temporary Q-15 assumption: standard-base64 raw Ed25519 public key.
    device_public_key: str = Field(min_length=1, max_length=16_384)

    @field_validator("device_public_key")
    @classmethod
    def validate_device_public_key(cls, value: str) -> str:
        decode_public_key(value)
        return value


class MachineResponse(BaseModel):
    mid: int
    device_uuid: UUID
    tailnet_tag: str
    status: MachineStatus
    created_at: datetime
    decommissioned_at: datetime | None
    fleet_env_template: str | None = None


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def require_prototype_enrollment_token(
    x_flexmix_prototype_enrollment_token: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.prototype_enrollment_token()
    if expected is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prototype enrollment is not configured",
        )
    if x_flexmix_prototype_enrollment_token is None or not secrets.compare_digest(
        x_flexmix_prototype_enrollment_token, expected
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def fleet_env_template(machine: MachineRegistry, settings: Settings) -> str:
    """Non-secret handoff only; a machine generates and retains its private key."""
    return "\n".join((
        "# Prototype enrollment handoff; install as /etc/flexmix/fleet.env (0600).",
        f"FLEXMIX_MID={machine.mid}",
        f"FLEXMIX_DEVICE_UUID={machine.device_uuid}",
        f"FLEXMIX_HUB_URL={settings.prototype_hub_url}",
        f"FLEXMIX_TAILNET_TAG={machine.tailnet_tag}",
        "FLEXMIX_DEVICE_PRIVATE_KEY_FILE=/etc/flexmix/device-ed25519.key",
        "FLEXMIX_RELEASE_PUBLIC_KEY_FILE=/etc/flexmix/release-signing-public-key.pem",
        "",
    ))


def response(machine: MachineRegistry, settings: Settings, *, include_template: bool) -> MachineResponse:
    return MachineResponse(
        mid=machine.mid,
        device_uuid=UUID(machine.device_uuid),
        tailnet_tag=machine.tailnet_tag,
        status=machine.status,
        created_at=machine.created_at,
        decommissioned_at=machine.decommissioned_at,
        fleet_env_template=fleet_env_template(machine, settings) if include_template else None,
    )


@router.post("/machines", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
def enroll_machine(
    payload: RegisterMachineRequest,
    _: None = Depends(require_prototype_enrollment_token),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> MachineResponse:
    try:
        machine = register_machine(
            session,
            device_uuid=payload.device_uuid,
            device_public_key=payload.device_public_key,
            tailnet_tag=settings.prototype_machine_tailnet_tag,
        )
    except DuplicateMachineError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Machine already registered") from error
    except MidExhaustedError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MID range exhausted") from error
    return response(machine, settings, include_template=True)


@router.get("/machines/{mid}", response_model=MachineResponse)
def get_machine(
    mid: int,
    _: None = Depends(require_prototype_enrollment_token),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> MachineResponse:
    machine = session.get(MachineRegistry, mid)
    if machine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")
    return response(machine, settings, include_template=False)


@router.post("/machines/{mid}/decommission", response_model=MachineResponse)
def decommission(
    mid: int,
    _: None = Depends(require_prototype_enrollment_token),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> MachineResponse:
    try:
        machine = decommission_machine(session, mid)
    except MachineNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found") from error
    except MachineAlreadyDecommissionedError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Machine already decommissioned") from error
    return response(machine, settings, include_template=False)
