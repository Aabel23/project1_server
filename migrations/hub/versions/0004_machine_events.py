"""Phase 04 prototype order event inbox."""

from alembic import op
import sqlalchemy as sa

revision = "0004_machine_events"
down_revision = "0003_desired_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "machine_order_event",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("machine_mid", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("cursor", sa.Integer(), nullable=False),
        sa.Column("serial", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("drink_id", sa.String(length=64), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("machine_mid", "event_id", name="uq_machine_event"),
    )
    op.create_index("ix_machine_order_event_machine_mid", "machine_order_event", ["machine_mid"])


def downgrade() -> None:
    op.drop_index("ix_machine_order_event_machine_mid", table_name="machine_order_event")
    op.drop_table("machine_order_event")
