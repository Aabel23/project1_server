from __future__ import annotations
import hashlib, json, shutil, subprocess, tempfile, tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence
import uuid

BACKUP_FILES = ("pump_calib.json", "calib_loadcell.json", "machine_profile.json")

class BackupError(RuntimeError): pass

class MachineBackupManager:
    def __init__(self, root: Path, source_dir: Path, dump_runner: Callable[[Path], None] | None = None, max_backups: int = 7):
        self.root, self.source_dir, self.dump_runner, self.max_backups = Path(root), Path(source_dir), dump_runner, max_backups
        self.root.mkdir(parents=True, exist_ok=True)

    def _dump(self, target: Path) -> None:
        if self.dump_runner:
            self.dump_runner(target); return
        try:
            with target.open("wb") as out:
                subprocess.run(["mysqldump", "--single-transaction"], stdout=out, stderr=subprocess.PIPE, check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise BackupError("mysqldump failed") from exc

    def create_backup(self) -> Path:
        stamp = datetime.now(timezone.utc)
        name = f"backup-{stamp.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex}.tar.gz"
        dest = self.root / name
        with tempfile.TemporaryDirectory() as td:
            stage = Path(td); self._dump(stage / "mysql.sql")
            for filename in BACKUP_FILES:
                src = self.source_dir / filename
                if not src.is_file(): raise BackupError(f"missing required backup file: {filename}")
                shutil.copy2(src, stage / filename)
            (stage / "manifest.json").write_text(json.dumps({"backup_id": name[:-7], "created_at": stamp.isoformat(), "files": ["mysql.sql", *BACKUP_FILES]}))
            with tarfile.open(dest, "w:gz") as archive:
                for filename in ("mysql.sql", *BACKUP_FILES, "manifest.json"): archive.add(stage / filename, arcname=filename)
        self._retain(); return dest

    create_nightly_backup = create_backup

    def _retain(self):
        backups = sorted(self.root.glob("backup-*.tar.gz"), key=lambda p: p.name, reverse=True)
        for old in backups[self.max_backups:]: old.unlink(missing_ok=True)

    @staticmethod
    def restore_backup(package: Path, target_dir: Path) -> None:
        target_dir = Path(target_dir); target_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(package, "r:gz") as archive:
            names = {m.name for m in archive.getmembers()}
            required = {"mysql.sql", *BACKUP_FILES, "manifest.json"}
            if not required <= names or any(Path(n).is_absolute() or ".." in Path(n).parts for n in names): raise BackupError("invalid backup package")
            archive.extractall(target_dir, filter="data")

    @staticmethod
    def upload(package: Path, send: Callable[[Path], object]) -> bool:
        try: send(package); return True
        except Exception: return False
