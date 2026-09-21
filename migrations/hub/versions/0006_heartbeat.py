"""Phase 06 prototype heartbeat."""
from alembic import op
import sqlalchemy as sa

revision = "0006_heartbeat"
down_revision = "0005_commands"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "machine_heartbeat",
        sa.Column("machine_mid", sa.Integer(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("schema_version", sa.String(64), nullable=False),
        sa.Column("selling_available", sa.Boolean(), nullable=False),
        sa.Column("detail", sa.Text()),
        sa.PrimaryKeyConstraint("machine_mid"),
    )


def downgrade() -> None:
    op.drop_table("machine_heartbeat")
