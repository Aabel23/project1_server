"""Lệnh migrate độc lập; các lệnh khác được thêm ở lần ráp sau."""

import argparse
from pathlib import Path
import sqlite3
import sys

from server.core.db import Database
from server.core.db.migrations import MigrationError, migrate


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Quản lý server FlexMix")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("migrate", help="Áp migration SQLite tạm")
    command.add_argument("--db", type=Path, default=Path("var/flexmix.db"))
    command.add_argument("--migration-root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args(argv)
    try:
        added = migrate(Database(args.db), args.migration_root)
    except (MigrationError, sqlite3.Error, OSError, UnicodeError, ValueError) as error:
        parser.exit(1, f"Migration thất bại: {error}\n")
    print(f"Đã áp {len(added)} migration: {', '.join(f'{number:04d}' for number in added) or 'không có'}")
    return 0


if __name__ == "__main__":
    # Giữ thông báo tiếng Việt khi Windows chuyển output qua pipe.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
