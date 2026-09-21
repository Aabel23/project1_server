"""Phase 03 prototype desired-state catalogue.

Revision ID: 0003_desired_state
Revises: 0002_fleet_registry
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_desired_state"
down_revision = "0002_fleet_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "desired_state_meta",
        sa.Column("singleton_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("singleton_id"),
    )
    op.execute(sa.text("INSERT INTO desired_state_meta (singleton_id, version) VALUES (1, 1)"))
    op.create_table(
        "catalogue_ingredient",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "catalogue_drink",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "catalogue_recipe_action",
        sa.Column("drink_id", sa.String(length=64), nullable=False),
        sa.Column("step_no", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.String(length=64), nullable=False),
        sa.Column("amount_grams", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["drink_id"], ["catalogue_drink.id"]),
        sa.ForeignKeyConstraint(["ingredient_id"], ["catalogue_ingredient.id"]),
        sa.PrimaryKeyConstraint("drink_id", "step_no"),
    )


def downgrade() -> None:
    op.drop_table("catalogue_recipe_action")
    op.drop_table("catalogue_drink")
    op.drop_table("catalogue_ingredient")
    op.drop_table("desired_state_meta")
