"""Transaction boundaries for the Phase 01 registry."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flexmix_hub.modules.fleet.models import (
    FleetMidAllocation,
    MachineRegistry,
    MachineStatus,
)

MID_MIN = 1
MID_MAX = 999_999


class MidExhaustedError(Exception):
    pass


class DuplicateMachineError(Exception):
    pass


class MachineNotFoundError(Exception):
    pass


class MachineAlreadyDecommissionedError(Exception):
    pass


def register_machine(
    session: Session, *, device_uuid: UUID, device_public_key: str, tailnet_tag: str
) -> MachineRegistry:
    """Allocate a permanent MID and commit it with the registration atomically."""
    try:
        allocation = session.execute(
            select(FleetMidAllocation)
            .where(FleetMidAllocation.singleton_id == 1)
            .with_for_update()
        ).scalar_one()
        if allocation.next_mid > MID_MAX:
            raise MidExhaustedError

        now = datetime.now(timezone.utc)
        machine = MachineRegistry(
            mid=allocation.next_mid,
            device_uuid=str(device_uuid),
            device_public_key=device_public_key,
            tailnet_tag=tailnet_tag,
            status=MachineStatus.ACTIVE,
            created_at=now,
        )
        allocation.next_mid += 1
        session.add(machine)
        session.commit()
        session.refresh(machine)
        return machine
    except IntegrityError as error:
        session.rollback()
        raise DuplicateMachineError from error
    except Exception:
        session.rollback()
        raise


def decommission_machine(session: Session, mid: int) -> MachineRegistry:
    """Keep the record and revoke its Hub credential state; never release the MID."""
    machine = session.get(MachineRegistry, mid)
    if machine is None:
        raise MachineNotFoundError
    if machine.status is MachineStatus.DECOMMISSIONED:
        raise MachineAlreadyDecommissionedError

    now = datetime.now(timezone.utc)
    machine.status = MachineStatus.DECOMMISSIONED
    machine.decommissioned_at = now
    machine.credential_revoked_at = now
    session.commit()
    session.refresh(machine)
    return machine
