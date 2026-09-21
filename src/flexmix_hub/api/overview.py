"""Read-only prototype fleet overview for operators."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from flexmix_hub.api.fleet import require_prototype_enrollment_token
from flexmix_hub.infrastructure.database.session import get_session
from flexmix_hub.modules.backups.models import BackupMetadata
from flexmix_hub.modules.commands.models import CommandStatus, MachineCommand
from flexmix_hub.modules.events.models import MachineOrderEvent
from flexmix_hub.modules.fleet.models import MachineRegistry
from flexmix_hub.modules.monitoring.models import MachineHeartbeat

router = APIRouter(prefix="/v1/prototype/overview", tags=["prototype-overview"])
STALE_SECONDS = 120

@router.get("")
def overview(_: None = Depends(require_prototype_enrollment_token), session: Session = Depends(get_session)):
    now = datetime.now(timezone.utc)
    machines = session.scalars(select(MachineRegistry).order_by(MachineRegistry.mid)).all()
    result = []
    for machine in machines:
        beat = session.get(MachineHeartbeat, machine.mid)
        received = beat.received_at if beat else None
        if received and received.tzinfo is None: received = received.replace(tzinfo=timezone.utc)
        event_count, max_cursor = session.execute(select(func.count(MachineOrderEvent.id), func.max(MachineOrderEvent.cursor)).where(MachineOrderEvent.machine_mid == machine.mid)).one()
        command_rows = session.execute(select(MachineCommand.status, func.count(MachineCommand.id)).where(MachineCommand.machine_mid == machine.mid).group_by(MachineCommand.status)).all()
        command_counts = {status.value if isinstance(status, CommandStatus) else status: count for status, count in command_rows}
        backup = session.scalar(select(BackupMetadata).where(BackupMetadata.machine_mid == machine.mid).order_by(BackupMetadata.backup_time.desc()))
        backup_age = None
        if backup:
            backup_time = backup.backup_time.replace(tzinfo=timezone.utc) if backup.backup_time.tzinfo is None else backup.backup_time
            backup_age = max(0, (now - backup_time).total_seconds())
        result.append({"mid": machine.mid, "machine_status": machine.status.value, "online": bool(received and received >= now - timedelta(seconds=STALE_SECONDS)), "heartbeat_received_at": received, "event_count": event_count, "max_event_cursor": max_cursor, "command_counts": command_counts, "latest_backup_id": backup.backup_id if backup else None, "backup_age_seconds": backup_age, "backup_stale": backup_age is not None and backup_age > 36 * 3600})
    return {"machines": result}
