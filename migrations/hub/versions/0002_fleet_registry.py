"""Phase 01 prototype fleet registry.

Revision ID: 0002_fleet_registry
Revises: 0001_foundation
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_fleet_registry"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


machine_status = sa.Enum("active", "decommissioned", name="machine_status")


def upgrade() -> None:
    op.create_table(
        "fleet_mid_allocation",
        sa.Column("singleton_id", sa.Integer(), nullable=False),
        sa.Column("next_mid", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("singleton_id"),
    )
    op.execute(
        sa.text("INSERT INTO fleet_mid_allocation (singleton_id, next_mid) VALUES (1, 1)")
    )
    op.create_table(
        "machine_registry",
        sa.Column("mid", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("device_uuid", sa.String(length=36), nullable=False),
        sa.Column("device_public_key", sa.Text(), nullable=False),
        sa.Column("tailnet_tag", sa.String(length=64), nullable=False),
        sa.Column("status", machine_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decommissioned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("credential_revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("mid"),
        sa.UniqueConstraint("device_uuid", name="uq_machine_registry_uuid"),
    )


def downgrade() -> None:
    op.drop_table("machine_registry")
    op.drop_table("fleet_mid_allocation")
    machine_status.drop(op.get_bind(), checkfirst=True)
