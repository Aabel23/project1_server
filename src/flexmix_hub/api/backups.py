from datetime import datetime, timezone
import hashlib, re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from flexmix_hub.api.machine import authenticated_machine
from flexmix_hub.infrastructure.database.session import get_session
from flexmix_hub.modules.backups.models import BackupMetadata

router = APIRouter(tags=["backups"])
ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

@router.post("/v1/backups", status_code=201)
async def upload_backup(request: Request, machine=Depends(authenticated_machine), session=Depends(get_session)):
    backup_id = request.headers.get("X-Flexmix-Backup-Id", "")
    if not ID_RE.fullmatch(backup_id): raise HTTPException(400, "invalid backup id")
    content_length = request.headers.get("content-length")
    if content_length and (not content_length.isdigit() or int(content_length) > 100 * 1024 * 1024):
        raise HTTPException(413, "backup too large")
    data = await request.body()
    if len(data) > 100 * 1024 * 1024:
        raise HTTPException(413, "backup too large")
    raw_time = request.headers.get("X-Flexmix-Backup-Time")
    try:
        backup_time = datetime.fromisoformat(raw_time) if raw_time else datetime.now(timezone.utc)
    except ValueError as exc:
        raise HTTPException(400, "invalid backup time") from exc
    root = Path(request.app.state.settings.backup_root) / str(machine.mid); root.mkdir(parents=True, exist_ok=True)
    existing = session.scalar(select(BackupMetadata).where(BackupMetadata.machine_mid == machine.mid, BackupMetadata.backup_id == backup_id))
    if existing: return {"status": "ok", "backup_id": backup_id, "duplicate": True}
    path = root / f"{backup_id}.tar.gz"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)
    now = datetime.now(timezone.utc)
    session.add(BackupMetadata(machine_mid=machine.mid, backup_id=backup_id, filename=path.name, stored_path=str(path), backup_time=backup_time, received_at=now, size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    session.commit(); return {"status": "ok", "backup_id": backup_id}

@router.get("/v1/prototype/backups/{mid}/latest")
def latest_backup(mid: int, machine=Depends(authenticated_machine), session=Depends(get_session)):
    if machine.mid != mid:
        raise HTTPException(403, "Machine identity mismatch")
    item = session.scalar(select(BackupMetadata).where(BackupMetadata.machine_mid == mid).order_by(BackupMetadata.backup_time.desc()))
    if not item: raise HTTPException(404, "no backup")
    bt = item.backup_time.replace(tzinfo=timezone.utc) if item.backup_time.tzinfo is None else item.backup_time
    age = max(0, (datetime.now(timezone.utc) - bt).total_seconds())
    return {"backup_id": item.backup_id, "machine_mid": mid, "age_seconds": age, "stale": age > 36 * 3600}
