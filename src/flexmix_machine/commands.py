"""Minimal idempotent machine-side command executor."""

import json
import os
from pathlib import Path
from typing import Any


class LocalCommandExecutor:
    def __init__(self, path: Path):
        self.path = path

    def _read(self) -> dict[str, Any]:
        return json.loads(self.path.read_text()) if self.path.exists() else {"applied": []}

    def execute(self, command: dict[str, Any]) -> dict[str, str]:
        command_id = command["command_id"]
        state = self._read()
        if command_id in state["applied"]:
            return {"command_id": command_id, "status": "acknowledged"}
        if command.get("kind") != "refresh_state":
            return {"command_id": command_id, "status": "failed", "error": "unsupported command"}
        state["applied"].append(command_id)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(state, sort_keys=True))
        os.replace(temp, self.path)
        return {"command_id": command_id, "status": "acknowledged"}
