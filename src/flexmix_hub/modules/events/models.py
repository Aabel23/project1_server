from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from flexmix_hub.infrastructure.database.base import Base


class MachineOrderEvent(Base):
    """Hub monitoring copy; the machine remains order_ticket authority."""

    __tablename__ = "machine_order_event"
    __table_args__ = (UniqueConstraint("machine_mid", "event_id", name="uq_machine_event"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_mid: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    cursor: Mapped[int] = mapped_column(Integer, nullable=False)
    serial: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    drink_id: Mapped[str] = mapped_column(String(64), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Deliberately absent from the normal telemetry model.
