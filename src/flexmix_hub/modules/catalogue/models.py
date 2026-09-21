"""Hub-owned catalogue records used to build desired-state snapshots."""

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from flexmix_hub.infrastructure.database.base import Base


class DesiredStateMeta(Base):
    __tablename__ = "desired_state_meta"

    singleton_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)


class CatalogueIngredient(Base):
    __tablename__ = "catalogue_ingredient"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)


class CatalogueDrink(Base):
    __tablename__ = "catalogue_drink"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CatalogueRecipeAction(Base):
    __tablename__ = "catalogue_recipe_action"

    drink_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("catalogue_drink.id"), primary_key=True
    )
    step_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingredient_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("catalogue_ingredient.id"), nullable=False
    )
    amount_grams: Mapped[int] = mapped_column(Integer, nullable=False)
