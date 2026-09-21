from pathlib import Path

from flexmix_machine.commands import LocalCommandExecutor


def test_command_execution_is_idempotent(tmp_path: Path):
    executor = LocalCommandExecutor(tmp_path / "commands.json")
    command = {"command_id": "c-1", "kind": "refresh_state", "payload": {}}
    assert executor.execute(command)["status"] == "acknowledged"
    assert executor.execute(command)["status"] == "acknowledged"
    assert (tmp_path / "commands.json").read_text().count("c-1") == 1
