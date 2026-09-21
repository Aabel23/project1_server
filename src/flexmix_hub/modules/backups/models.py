from datetime import datetime
from sqlalchemy import DateTime, Integer, String, BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from flexmix_hub.infrastructure.database.base import Base

class BackupMetadata(Base):
    __tablename__ = "backup_metadata"
    __table_args__ = (UniqueConstraint("machine_mid", "backup_id", name="uq_backup_machine_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    machine_mid: Mapped[int] = mapped_column(Integer, index=True)
    backup_id: Mapped[str] = mapped_column(String(128), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    backup_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
