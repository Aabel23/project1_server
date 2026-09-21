"""Phase 05 prototype command queue."""
from alembic import op
import sqlalchemy as sa

revision = "0005_commands"
down_revision = "0004_machine_events"
branch_labels = None
depends_on = None
command_status = sa.Enum("pending", "delivered", "acknowledged", "failed", name="command_status")


def upgrade() -> None:
    op.create_table(
        "machine_command",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("command_id", sa.String(64), nullable=False),
        sa.Column("machine_mid", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("status", command_status, nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.String(255)),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("command_id", name="uq_machine_command_id"),
    )
    op.create_index("ix_machine_command_machine_mid", "machine_command", ["machine_mid"])


def downgrade() -> None:
    op.drop_index("ix_machine_command_machine_mid", table_name="machine_command")
    op.drop_table("machine_command")
