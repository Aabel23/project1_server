"""SQLite tạm cho S-DB; mỗi transaction dùng một kết nối riêng."""

from contextlib import contextmanager
import math
from pathlib import Path
import sqlite3


class Database:
    # ponytail: SQLite chỉ có một writer; chuyển MySQL khi cần nhiều writer.
    def __init__(self, path: str | Path, *, timeout: float = 10.0):
        if str(path) == ":memory:":
            raise ValueError("S-DB cần file .db để dùng nhiều kết nối.")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout phải là số hữu hạn lớn hơn 0.")
        self.path = Path(path)
        self.timeout = timeout

    @contextmanager
    def transaction(self, *, immediate: bool = False):
        """Commit khi thành công; rollback và đóng kết nối khi có lỗi.

        Không gọi commit/rollback hoặc executescript trong khối này.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=self.timeout, isolation_level=None)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA synchronous = FULL")
            with conn:
                conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
                yield conn
        finally:
            conn.close()

    def query(self, sql: str, parameters=()) -> list[dict]:
        """Một câu SQL có tham số; trả các dòng dạng dict, ghi không RETURNING trả []."""
        with self.transaction() as conn:
            cursor = conn.execute(sql, parameters)
            return [dict(row) for row in cursor.fetchall()] if cursor.description else []
