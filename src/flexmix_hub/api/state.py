"""Authenticated desired-state download; no event/command functionality."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from flexmix_hub.api.machine import authenticated_machine
from flexmix_hub.infrastructure.database.session import get_session
from flexmix_hub.modules.catalogue.models import DesiredStateMeta
from flexmix_hub.modules.catalogue.service import snapshot_for_machine
from flexmix_hub.modules.fleet.models import MachineRegistry

router = APIRouter(tags=["desired-state"])


@router.get("/v1/state", response_model=None)
def desired_state(
    have: int | None = Query(default=None, ge=1),
    machine: MachineRegistry = Depends(authenticated_machine),
    session: Session = Depends(get_session),
) -> dict | Response:
    version = session.get(DesiredStateMeta, 1).version
    if have == version:
        return Response(status_code=304)
    return snapshot_for_machine(session, machine)
