"""backup metadata"""
from alembic import op
import sqlalchemy as sa
revision = "0007_backups"
down_revision = "0006_heartbeat"
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("backup_metadata",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("machine_mid", sa.Integer(), nullable=False),
        sa.Column("backup_id", sa.String(128), nullable=False), sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("stored_path", sa.String(1024), nullable=False), sa.Column("backup_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False), sa.Column("size_bytes", sa.BigInteger(), nullable=False), sa.Column("sha256", sa.String(64), nullable=False),
        sa.UniqueConstraint("machine_mid", "backup_id", name="uq_backup_machine_id"))
    op.create_index("ix_backup_metadata_machine_mid", "backup_metadata", ["machine_mid"])
def downgrade():
    op.drop_index("ix_backup_metadata_machine_mid", table_name="backup_metadata"); op.drop_table("backup_metadata")
