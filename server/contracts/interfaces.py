"""C0.10/C0.11: chữ ký và dữ liệu đề xuất, không thực thi nghiệp vụ."""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Callable, Literal, Protocol


Body = dict[str, object]
Status = Literal["ok", "revoked", "bad_request", "not_found", "conflict", "epoch_changed", "error"]
Handler = Callable[[int, Body], tuple[Status, Body]]
Decorator = Callable[[Callable], Callable]


class ContractError(Exception):
    """Lỗi hợp đồng dự kiến; ánh xạ status/HTTP ghi trong interfaces.md."""


class NotFound(ContractError):
    pass


class Conflict(ContractError):
    pass


class Forbidden(ContractError):
    pass


class EpochChanged(Conflict):
    pass


@dataclass(frozen=True)
class User:
    user_id: int
    role: Literal["owner", "manager", "staff"]
    active: bool
    revoked_at: int
    areas: frozenset[str]


@dataclass(frozen=True)
class Credential:
    kid: str
    machine_id: int
    alg: str
    pubkey: bytes
    status: Literal["active", "retiring", "revoked"]
    generation: int
    hw_issued_at: int
    last_revoked_notice_at: int | None


@dataclass(frozen=True)
class MenuTarget:
    server_epoch: bytes
    version: int
    sha256: str


@dataclass(frozen=True)
class Command:
    command_id: bytes
    kind: str
    args: Body
    args_bytes: bytes
    fingerprint: bytes
    ttl_ms: int


@dataclass(frozen=True)
class Snapshot:
    target: MenuTarget
    snapshot: Body
    media: tuple[Body, ...]


class Database(Protocol):
    def transaction(self, *, immediate: bool = False) -> AbstractContextManager[sqlite3.Connection]: ...
    def query(self, sql: str, parameters: tuple = ()) -> list[dict]: ...


class Wake(Protocol):
    def notify(self, machine_id: int) -> None: ...
    def wait(self, machine_id: int, timeout: float) -> bool: ...


class Security(Protocol):
    def require(self, area: str, machine_id: int | None = None) -> Decorator: ...
    def require_stepup(self) -> Decorator: ...
    def idempotent(self, request_key: str, body: Body) -> AbstractContextManager[Body]: ...
    def check_epoch(self, server_epoch: bytes) -> None: ...


class Accounts(Protocol):
    def load_user(self, user_id: int) -> User | None: ...
    def machines_of(self, user_id: int) -> frozenset[int]: ...


class Keys(Protocol):
    def lookup_kid(self, kid: str) -> Credential | None: ...
    def server_kem_private(self) -> bytes: ...
    def advance_high_water(self, connection: sqlite3.Connection, kid: str, issued_at_ms: int) -> Credential: ...
    def reapply_revoked(self) -> None: ...


class AgentGate(Protocol):
    def agent_route(self, route_id: str) -> Callable[[Handler], Callable]: ...


class Commands(Protocol):
    def take_for_offer(self, machine_id: int, horizon: float) -> list[Command]: ...
    def cancel_for_revoke(self, machine_id: int) -> None: ...
    def mark_unknown_all(self) -> None: ...


class Menus(Protocol):
    def target_version(self, machine_id: int) -> MenuTarget | None: ...
    def snapshot(self, version: int) -> Snapshot: ...


class Catalogue(Protocol):
    def drinks_for(self, menu_id: int) -> list[Body]: ...


class Media(Protocol):
    def path_of(self, sha256: str) -> Path: ...


class Publish(Protocol):
    def applied_of(self, machine_id: int) -> Body | None: ...


class Ingest(Protocol):
    def upsert_ticket(self, machine_id: int, row: Body) -> None: ...
    def delete_faults(self, machine_id: int, ids: list[int]) -> None: ...
    def stock_of(self, machine_id: int) -> Body | None: ...


class Epoch(Protocol):
    def current(self) -> bytes: ...
    def check(self, connection: sqlite3.Connection) -> None: ...


class Session(Protocol):
    def rotate_key(self) -> None: ...


class AgentNet(Protocol):
    def call(self, route_id: str, body: Body) -> tuple[Status, Body]: ...


class Helper(Protocol):
    def call(self, command: str) -> Body: ...


class Registrar(Protocol):
    def add(self, route_id: str, handler: Callable) -> None: ...


class Module(Protocol):
    def setup(self, deps: Body, registrar: Registrar) -> None: ...
