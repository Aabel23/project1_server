"""Desired-state generation for the minimal Phase 03 prototype."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from flexmix_contracts.desired_state import CONTRACT
from flexmix_hub.modules.catalogue.models import (
    CatalogueDrink,
    CatalogueIngredient,
    CatalogueRecipeAction,
    DesiredStateMeta,
)
from flexmix_hub.modules.fleet.models import MachineRegistry

@dataclass(frozen=True)
class IngredientDraft:
    id: str
    name: str
    kind: str


@dataclass(frozen=True)
class RecipeActionDraft:
    ingredient_id: str
    amount_grams: int


@dataclass(frozen=True)
class DrinkDraft:
    id: str
    name: str
    price_cents: int
    published: bool
    recipe: tuple[RecipeActionDraft, ...]


def replace_catalogue(
    session: Session, *, ingredients: tuple[IngredientDraft, ...], drinks: tuple[DrinkDraft, ...]
) -> int:
    """Replace the small prototype catalogue and advance one desired-state version.

    Production authoring, review, tombstones, mappings and rollback remain out
    of scope. This transaction never touches machine-owned data.
    """
    try:
        session.execute(delete(CatalogueRecipeAction))
        session.execute(delete(CatalogueDrink))
        session.execute(delete(CatalogueIngredient))
        session.add_all(
            [CatalogueIngredient(id=row.id, name=row.name, kind=row.kind) for row in ingredients]
        )
        for drink in drinks:
            session.add(
                CatalogueDrink(
                    id=drink.id,
                    name=drink.name,
                    price_cents=drink.price_cents,
                    published=drink.published,
                )
            )
            session.add_all(
                [
                    CatalogueRecipeAction(
                        drink_id=drink.id,
                        step_no=index,
                        ingredient_id=action.ingredient_id,
                        amount_grams=action.amount_grams,
                    )
                    for index, action in enumerate(drink.recipe, start=1)
                ]
            )
        meta = session.execute(
            select(DesiredStateMeta)
            .where(DesiredStateMeta.singleton_id == 1)
            .with_for_update()
        ).scalar_one()
        meta.version += 1
        session.commit()
        return meta.version
    except Exception:
        session.rollback()
        raise


def snapshot_for_machine(session: Session, machine: MachineRegistry) -> dict:
    """Build a complete, Hub-owned desired state for an authenticated machine."""
    meta = session.get(DesiredStateMeta, 1)
    ingredients = session.scalars(select(CatalogueIngredient).order_by(CatalogueIngredient.id)).all()
    drinks = session.scalars(
        select(CatalogueDrink)
        .where(CatalogueDrink.published.is_(True))
        .order_by(CatalogueDrink.id)
    ).all()
    actions_by_drink: dict[str, list[CatalogueRecipeAction]] = defaultdict(list)
    for action in session.scalars(
        select(CatalogueRecipeAction).order_by(
            CatalogueRecipeAction.drink_id, CatalogueRecipeAction.step_no
        )
    ):
        actions_by_drink[action.drink_id].append(action)
    return {
        "contract": CONTRACT,
        "version": meta.version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        # Temporary Q-12 mapping: target is the Hub-assigned MID.
        "target_mid": machine.mid,
        "ingredients": [
            {"id": item.id, "name": item.name, "kind": item.kind} for item in ingredients
        ],
        "drinks": [
            {
                "id": drink.id,
                "name": drink.name,
                "price_cents": drink.price_cents,
                "recipe": [
                    {
                        "step_no": action.step_no,
                        "ingredient_id": action.ingredient_id,
                        "amount_grams": action.amount_grams,
                    }
                    for action in actions_by_drink[drink.id]
                ],
            }
            for drink in drinks
        ],
    }
