"""Migration đánh số của từng khối; chưa có schema nghiệp vụ."""

import hashlib
from pathlib import Path
import re
import sqlite3

from . import Database


class MigrationError(Exception):
    """Lịch sử hoặc nội dung migration không hợp lệ."""


def discover(root: str | Path) -> list[tuple[int, str, Path]]:
    """Tìm NNNN_ten.sql dưới core, security, modules; số không được trùng."""
    root = Path(root)
    if not root.is_dir():
        raise MigrationError(f"Không có thư mục migration gốc: {root}")
    found = []
    seen = {}
    for area in ("core", "security", "modules"):
        for path in sorted(root.glob(f"{area}/*/migrations/*.sql")):
            match = re.fullmatch(r"([0-9]{4})_([a-z0-9_]+)\.sql", path.name)
            if match is None:
                raise MigrationError(f"Tên migration phải là NNNN_ten.sql: {path}")
            number = int(match[1])
            if number in seen:
                raise MigrationError(f"Trùng số migration {number:04d}: {seen[number]} và {path}")
            seen[number] = path
            found.append((number, path.relative_to(root).as_posix(), path))
    return sorted(found, key=lambda item: (item[0], item[1]))


def _statements(sql: str):
    # SQLite nhận biết cả dấu ; trong chuỗi, comment và thân trigger.
    start = 0
    for end, char in enumerate(sql):
        if char == ";" and sqlite3.complete_statement(sql[start:end + 1]):
            yield sql[start:end + 1]
            start = end + 1
    remaining = sql[start:]
    if remaining.strip():
        if not sqlite3.complete_statement(remaining + "\n;"):
            raise MigrationError("Câu SQL cuối migration chưa hoàn chỉnh.")
        yield remaining


def _authorize(action, arg1, arg2, database, source):
    # Migration không được tự commit hoặc thay cấu hình làm mất rollback.
    blocked = {sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_SAVEPOINT,
               sqlite3.SQLITE_PRAGMA, sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}
    writes = {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
              sqlite3.SQLITE_DROP_TABLE}
    journal = "schema_migration"
    if action in blocked or (action in writes and arg1 == journal):
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_ALTER_TABLE and arg2 == journal:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def migrate(db: Database, root: str | Path) -> list[int]:
    """Áp cả đợt trong một transaction; lỗi thì rollback cả schema và sổ.

    SQLite chỉ có một writer; BEGIN IMMEDIATE tuần tự hóa hai runner.
    """
    # Đọc một lần để checksum và câu SQL luôn thuộc cùng nội dung.
    files = [(number, name, path.read_bytes()) for number, name, path in discover(root)]
    payloads = [(number, name, hashlib.sha256(data).hexdigest(), data.decode("utf-8-sig"))
                for number, name, data in files]
    with db.transaction(immediate=True) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS schema_migration (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        applied = {row["version"]: row for row in conn.execute("SELECT * FROM schema_migration")}
        unknown = set(applied) - {number for number, _, _, _ in payloads}
        if unknown:
            raise MigrationError(f"Thiếu file migration đã áp: {sorted(unknown)}")
        latest = max(applied, default=-1)
        for number, name, checksum, sql in payloads:
            if number in applied and (applied[number]["checksum"] != checksum
                                      or applied[number]["name"] != name):
                raise MigrationError(f"Migration {number:04d} đã đổi sau khi áp: {name}")
            if number not in applied and number <= latest:
                raise MigrationError(
                    f"Migration {number:04d} phải có số mới lớn hơn {latest:04d} đã áp: {name}"
                )
        added = []
        for number, name, checksum, sql in payloads:
            if number in applied:
                continue
            conn.set_authorizer(_authorize)
            try:
                for statement in _statements(sql):
                    conn.execute(statement)
            except (sqlite3.Error, MigrationError) as error:
                raise MigrationError(f"Migration {name} thất bại: {error}") from error
            finally:
                conn.set_authorizer(None)
            conn.execute("INSERT INTO schema_migration (version, name, checksum) VALUES (?, ?, ?)",
                         (number, name, checksum))
            added.append(number)
        return added
