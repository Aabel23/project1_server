"""Crash-safe local desired-state persistence for the Phase 03 prototype.

This is a local state-file adapter because the real machine repository/database
is not present in this workspace. It does not access order_ticket or hardware.
"""

import json
import os
from pathlib import Path
from typing import Any

from flexmix_contracts.desired_state import CONTRACT


class SnapshotError(ValueError):
    pass


class LocalDesiredState:
    def __init__(self, path: Path, *, mid: int, available_ingredient_ids: set[str]):
        self.path = path
        self.mid = mid
        self.available_ingredient_ids = available_ingredient_ids

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text())

    def apply(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Validate fully, then atomically replace local state; repeats are no-ops."""
        if snapshot.get("contract") != CONTRACT or snapshot.get("target_mid") != self.mid:
            raise SnapshotError("Snapshot target or contract is invalid")
        version = snapshot.get("version")
        if not isinstance(version, int) or version < 1:
            raise SnapshotError("Snapshot version is invalid")
        ingredients = snapshot.get("ingredients")
        drinks = snapshot.get("drinks")
        if not isinstance(ingredients, list) or not isinstance(drinks, list):
            raise SnapshotError("Snapshot catalogue is invalid")

        current = self.load()
        if current is not None:
            if version == current["version"]:
                return current
            if version < current["version"]:
                raise SnapshotError("Refusing stale snapshot")

        ingredient_ids = {item.get("id") for item in ingredients if isinstance(item, dict)}
        if None in ingredient_ids or len(ingredient_ids) != len(ingredients):
            raise SnapshotError("Snapshot ingredients are invalid")
        eligible_drinks = []
        for drink in drinks:
            if not isinstance(drink, dict) or not isinstance(drink.get("recipe"), list):
                raise SnapshotError("Snapshot recipe is invalid")
            recipe_ingredients = {step.get("ingredient_id") for step in drink["recipe"] if isinstance(step, dict)}
            if None in recipe_ingredients or not recipe_ingredients.issubset(ingredient_ids):
                raise SnapshotError("Recipe references an unknown ingredient")
            # Machine-owned capability decides what can be sold locally.
            if recipe_ingredients.issubset(self.available_ingredient_ids):
                eligible_drinks.append(drink)

        local_state = {
            "version": version,
            "ingredients": [item for item in ingredients if item["id"] in self.available_ingredient_ids],
            "drinks": eligible_drinks,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(local_state, sort_keys=True, separators=(",", ":")))
        os.replace(temporary, self.path)
        return local_state
