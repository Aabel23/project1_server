"""Persistent registry state owned by the Hub.

This is intentionally separate from every machine database and does not model
orders, hardware, catalogue state, agents, or event synchronization.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from flexmix_hub.infrastructure.database.base import Base


class MachineStatus(str, Enum):
    ACTIVE = "active"
    DECOMMISSIONED = "decommissioned"


class FleetMidAllocation(Base):
    """One locked counter makes MID allocation safe under concurrent requests."""

    __tablename__ = "fleet_mid_allocation"

    singleton_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    next_mid: Mapped[int] = mapped_column(Integer, nullable=False)


class MachineRegistry(Base):
    """Minimal Phase 01 machine registry; deleted rows would violate C-05."""

    __tablename__ = "machine_registry"
    __table_args__ = (UniqueConstraint("device_uuid", name="uq_machine_registry_uuid"),)

    mid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    device_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    # Q-15 leaves key formats/proof unselected; this holds an opaque public value only.
    device_public_key: Mapped[str] = mapped_column(Text, nullable=False)
    tailnet_tag: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[MachineStatus] = mapped_column(
        SqlEnum(
            MachineStatus,
            name="machine_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decommissioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    credential_revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
