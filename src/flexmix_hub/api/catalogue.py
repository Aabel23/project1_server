"""Prototype operator catalogue authoring; deliberately not production ACL."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from flexmix_hub.api.fleet import require_prototype_enrollment_token
from flexmix_hub.infrastructure.database.session import get_session
from flexmix_hub.modules.catalogue.models import CatalogueDrink, CatalogueIngredient, DesiredStateMeta
from flexmix_hub.modules.catalogue.service import (
    DrinkDraft, IngredientDraft, RecipeActionDraft, replace_catalogue,
)

router = APIRouter(prefix="/v1/prototype/catalogue", tags=["prototype-catalogue"])

class IngredientInput(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    kind: str = Field(min_length=1, max_length=32)

class ActionInput(BaseModel):
    ingredient_id: str = Field(min_length=1, max_length=64)
    amount_grams: int = Field(gt=0, le=9999)

class DrinkInput(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    price_cents: int = Field(ge=0)
    published: bool = False
    recipe: list[ActionInput] = Field(default_factory=list, max_length=100)

class CatalogueInput(BaseModel):
    ingredients: list[IngredientInput] = Field(default_factory=list, max_length=1000)
    drinks: list[DrinkInput] = Field(default_factory=list, max_length=1000)

def _validate(payload: CatalogueInput) -> None:
    ingredient_ids = [item.id for item in payload.ingredients]
    drink_ids = [item.id for item in payload.drinks]
    if len(set(ingredient_ids)) != len(ingredient_ids):
        raise HTTPException(422, "Duplicate ingredient id")
    if len(set(drink_ids)) != len(drink_ids):
        raise HTTPException(422, "Duplicate drink id")
    known = set(ingredient_ids)
    for drink in payload.drinks:
        referenced = [step.ingredient_id for step in drink.recipe]
        if len(set(referenced)) != len(referenced):
            raise HTTPException(422, "Duplicate recipe ingredient")
        if any(item not in known for item in referenced):
            raise HTTPException(422, "Recipe references unknown ingredient")

@router.put("", status_code=200)
def publish_catalogue(payload: CatalogueInput, _: None = Depends(require_prototype_enrollment_token), session: Session = Depends(get_session)):
    _validate(payload)
    version = replace_catalogue(
        session,
        ingredients=tuple(IngredientDraft(x.id, x.name, x.kind) for x in payload.ingredients),
        drinks=tuple(DrinkDraft(x.id, x.name, x.price_cents, x.published, tuple(RecipeActionDraft(a.ingredient_id, a.amount_grams) for a in x.recipe)) for x in payload.drinks),
    )
    return {"version": version}

@router.get("")
def read_catalogue(_: None = Depends(require_prototype_enrollment_token), session: Session = Depends(get_session)):
    meta = session.get(DesiredStateMeta, 1)
    return {
        "version": meta.version,
        "ingredients": [{"id": x.id, "name": x.name, "kind": x.kind} for x in session.scalars(select(CatalogueIngredient).order_by(CatalogueIngredient.id))],
        "drinks": [{"id": x.id, "name": x.name, "price_cents": x.price_cents, "published": x.published} for x in session.scalars(select(CatalogueDrink).order_by(CatalogueDrink.id))],
    }
