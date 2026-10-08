"""Kiểm import cô lập: absolute, relative và nhóm bảo mật riêng."""

import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2] / "server"


def imported_names(source: str, filename: str) -> list[str]:
    path = Path(filename)
    package = ("server", *path.parent.parts)
    imports = []
    for node in ast.walk(ast.parse(source, filename=filename)):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                if node.level > len(package):
                    imports.append("INVALID_RELATIVE_IMPORT")
                    continue
                prefix = package[:len(package) - node.level + 1]
            else:
                prefix = ()
            base = (*prefix, *(node.module.split(".") if node.module else ()))
            imports.extend(".".join((*base, alias.name)) for alias in node.names)
    return imports


def violations(source: str, filename: str) -> list[str]:
    owner = Path(filename).parts
    result = []
    for name in imported_names(source, filename):
        target = name.split(".")
        if target[0] == "INVALID_RELATIVE_IMPORT":
            result.append(name)
            continue
        if target[0] != "server":
            continue
        target = target[1:]
        if not target:
            continue
        if target[0] == "wiring" or target[0] == "main":
            result.append(name)
        elif target[0] == "modules":
            if len(target) < 2 or len(owner) < 2 or owner[:2] != tuple(target[:2]):
                result.append(name)
        elif owner[0] == "security" and target[0] == "security":
            if len(target) < 2 or owner[:2] != tuple(target[:2]):
                result.append(name)
        elif owner[0] in ("contracts", "config") and target[0] in ("core", "security"):
            result.append(name)
        elif owner[0] == "core" and target[0] == "security":
            result.append(name)
        elif owner[0] == "security" and target[0] not in ("security", "core", "contracts"):
            result.append(name)
        elif owner[0] == "modules" and target[0] not in ("modules", "core", "security", "config", "contracts"):
            result.append(name)
    return result


def test_repository_imports_are_isolated():
    errors = []
    for path in ROOT.rglob("*.py"):
        relative = path.relative_to(ROOT)
        if relative.as_posix() in ("wiring.py", "main.py", "__init__.py"):
            continue
        errors.extend(f"{relative}: {name}" for name in violations(path.read_text(encoding="utf-8"), str(relative)))
    assert not errors, "Import chéo khối:\n" + "\n".join(errors)


@pytest.mark.parametrize("source,filename", [
    ("import server.modules.keys.api", "modules/menu/api.py"),
    ("from server.modules import keys", "modules/menu/api.py"),
    ("from ..keys import api", "modules/menu/routes.py"),
    ("from .. import keys", "modules/menu/routes.py"),
    ("from server import wiring", "modules/menu/api.py"),
    ("from ... import wiring", "modules/menu/api.py"),
    ("from ...wiring import setup", "modules/menu/api.py"),
    ("from ..seca import session", "security/fm1/agent_gate.py"),
    ("from server.modules.menu import api", "security/fm1/agent_gate.py"),
    ("from server.security.seca import session", "core/net/serve.py"),
    ("from server.core.db import Database", "contracts/interfaces.py"),
])
def test_cross_imports_are_rejected(source, filename):
    assert violations(source, filename)


@pytest.mark.parametrize("source,filename", [
    ("from . import store", "modules/menu/api.py"),
    ("from server.modules.menu.store import load", "modules/menu/api.py"),
    ("from server.contracts.interfaces import Menus", "modules/menu/api.py"),
    ("from server.security.seca import require", "modules/menu/routes.py"),
    ("from server.config.routing import AGENT_MENU_PATH", "modules/menu/routes.py"),
    ("from . import claims", "security/fm1/agent_gate.py"),
    ("from ...core.db import Database", "security/fm1/agent_gate.py"),
    ("from server.contracts.interfaces import Keys", "security/fm1/agent_gate.py"),
    ("from ..db import Database", "core/net/serve.py"),
])
def test_own_and_shared_imports_are_allowed(source, filename):
    assert not violations(source, filename)
