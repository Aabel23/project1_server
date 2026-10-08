"""Kiểm SQLite thật trên file tạm, không cần MySQL hay khối nghiệp vụ."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import subprocess
import sys
from threading import Barrier

import pytest

from server.core.db import Database
from server.core.db.migrations import MigrationError, discover, migrate


def write_migration(root, name, sql, *, block="core/db"):
    path = root / block / "migrations" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sql, encoding="utf-8")
    return path


def test_transaction_query_rollback_va_cau_hinh(tmp_path):
    db = Database(tmp_path / "nested/flexmix.db")
    assert db.query("CREATE TABLE item (id INTEGER PRIMARY KEY, name TEXT)") == []
    text = "dấu nháy '; DROP TABLE item; --"
    with db.transaction() as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conn.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 10000
        conn.execute("INSERT INTO item VALUES (?, ?)", (1, text))
    assert db.query("SELECT * FROM item") == [{"id": 1, "name": text}]
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")
    with pytest.raises(RuntimeError, match="giữa chừng"):
        with db.transaction() as conn:
            conn.execute("INSERT INTO item VALUES (?, ?)", (2, "rollback"))
            conn.execute("CREATE TABLE tam (id INTEGER)")
            raise RuntimeError("giữa chừng")
    assert db.query("SELECT COUNT(*) AS n FROM item") == [{"n": 1}]
    assert db.query("SELECT name FROM sqlite_master WHERE name = 'tam'") == []


def test_foreign_key_va_commit_loi_phai_rollback(tmp_path):
    db = Database(tmp_path / "fk.db")
    db.query("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
    db.query("""CREATE TABLE child (
        parent_id INTEGER REFERENCES parent(id) DEFERRABLE INITIALLY DEFERRED
    )""")
    with pytest.raises(sqlite3.IntegrityError):
        db.query("INSERT INTO child VALUES (?)", (99,))
    assert db.query("SELECT * FROM child") == []


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_timeout_khong_hop_le(tmp_path, timeout):
    with pytest.raises(ValueError, match="timeout"):
        Database(tmp_path / "bad.db", timeout=timeout)


def test_khong_dung_memory_voi_nhieu_connection():
    with pytest.raises(ValueError, match="file .db"):
        Database(":memory:")


def test_moi_thread_co_connection_rieng_va_ghi_khong_mat(tmp_path):
    db = Database(tmp_path / "threads.db")
    db.query("CREATE TABLE item (id INTEGER PRIMARY KEY)")
    ready = Barrier(4)

    def insert(number):
        ready.wait(timeout=10)
        with db.transaction(immediate=True) as conn:
            conn.execute("INSERT INTO item VALUES (?)", (number,))
        return conn

    with ThreadPoolExecutor(max_workers=4) as workers:
        connections = list(workers.map(insert, range(4)))
    assert len({id(conn) for conn in connections}) == 4
    assert db.query("SELECT id FROM item ORDER BY id") == [{"id": n} for n in range(4)]


def test_discover_ba_khu_vuc_thu_tu_va_trung_so(tmp_path):
    root = tmp_path / "server"
    write_migration(root, "0003_menu.sql", "SELECT 1;", block="modules/menu")
    write_migration(root, "0001_db.sql", "SELECT 1;")
    write_migration(root, "0002_seca.sql", "SELECT 1;", block="security/seca")
    assert [number for number, _, _ in discover(root)] == [1, 2, 3]
    write_migration(root, "0002_duplicate.sql", "SELECT 1;", block="modules/other")
    with pytest.raises(MigrationError, match="Trùng số migration 0002"):
        migrate(Database(tmp_path / "not_created.db"), root)
    assert not (tmp_path / "not_created.db").exists()


def test_discover_ten_sai_va_root_thieu(tmp_path):
    with pytest.raises(MigrationError, match="Không có thư mục"):
        discover(tmp_path / "missing")
    write_migration(tmp_path, "migration.sql", "SELECT 1;")
    with pytest.raises(MigrationError, match="NNNN_ten.sql"):
        discover(tmp_path)


def test_migrate_trigger_chuoi_comment_checksum_va_chay_lai(tmp_path):
    root = tmp_path / "server"
    write_migration(root, "0001_tables.sql", """
        -- Comment có dấu ; và dấu nháy '
        CREATE TABLE item (id INTEGER PRIMARY KEY, label TEXT);
        CREATE TABLE audit (message TEXT);
        CREATE TRIGGER item_added AFTER INSERT ON item BEGIN
            INSERT INTO audit VALUES ('đầu; cuối');
            INSERT INTO audit VALUES (NEW.label);
        END;
        /* Comment có dấu ; */
        INSERT INTO item VALUES (1, 'một; hai'); INSERT INTO item VALUES (2, 'ba');
        -- Comment cuối không có câu SQL
    """)
    write_migration(root, "0002_no_semicolon.sql", "INSERT INTO item VALUES (3, 'bốn')",
                    block="modules/menu")
    db = Database(tmp_path / "migrate.db")
    assert migrate(db, root) == [1, 2]
    assert db.query("SELECT message FROM audit") == [
        {"message": "đầu; cuối"}, {"message": "một; hai"},
        {"message": "đầu; cuối"}, {"message": "ba"},
        {"message": "đầu; cuối"}, {"message": "bốn"},
    ]
    journal = db.query("SELECT * FROM schema_migration ORDER BY version")
    assert len(journal) == 2 and all(len(row["checksum"]) == 64 for row in journal)
    assert migrate(db, root) == []
    assert db.query("SELECT * FROM schema_migration ORDER BY version") == journal
    assert db.query("SELECT COUNT(*) AS n FROM audit") == [{"n": 6}]


def test_checksum_doi_chan_truoc_migration_moi_va_file_thieu(tmp_path):
    root = tmp_path / "server"
    old = write_migration(root, "0001_old.sql", "CREATE TABLE old (id INTEGER);")
    db = Database(tmp_path / "history.db")
    migrate(db, root)
    write_migration(root, "0002_new.sql", "CREATE TABLE new (id INTEGER);")
    old.write_text("CREATE TABLE old (id TEXT);", encoding="utf-8")
    with pytest.raises(MigrationError, match="đã đổi"):
        migrate(db, root)
    assert db.query("SELECT name FROM sqlite_master WHERE name = 'new'") == []
    old.unlink()
    with pytest.raises(MigrationError, match="Thiếu file migration đã áp"):
        migrate(db, root)


@pytest.mark.parametrize("bad_sql", [
    "INSERT INTO missing_table VALUES (1);",
    "COMMIT;",
    "PRAGMA synchronous = OFF;",
    "DELETE FROM schema_migration;",
    "INSERT INTO tam VALUES ('chuỗi chưa đóng);",
])
def test_migrate_loi_rollback_ca_dot_va_so(tmp_path, bad_sql):
    root = tmp_path / "server"
    write_migration(root, "0001_ok.sql", "CREATE TABLE good (id INTEGER);")
    write_migration(root, "0002_bad.sql", "CREATE TABLE tam (id INTEGER);" + bad_sql)
    db = Database(tmp_path / "rollback.db")
    with pytest.raises(MigrationError, match="thất bại"):
        migrate(db, root)
    assert db.query("SELECT name FROM sqlite_master WHERE type = 'table'") == []


def test_migrate_loi_giu_nguyen_dot_da_commit(tmp_path):
    root = tmp_path / "server"
    write_migration(root, "0001_ok.sql", "CREATE TABLE good (id INTEGER);")
    db = Database(tmp_path / "committed.db")
    migrate(db, root)
    write_migration(root, "0002_bad.sql", "INSERT INTO good VALUES (1); SELECT * FROM missing;")
    with pytest.raises(MigrationError):
        migrate(db, root)
    assert db.query("SELECT * FROM good") == []
    assert db.query("SELECT version FROM schema_migration") == [{"version": 1}]


def test_migration_bo_sung_so_cu_bi_chan_khong_doi_db(tmp_path):
    root = tmp_path / "server"
    write_migration(root, "0001_base.sql", "CREATE TABLE config (value INTEGER); INSERT INTO config VALUES (0);")
    write_migration(root, "0003_last.sql", "UPDATE config SET value = 3;")
    db = Database(tmp_path / "upgrade.db")
    assert migrate(db, root) == [1, 3]
    journal = db.query("SELECT * FROM schema_migration ORDER BY version")
    write_migration(root, "0002_middle.sql", "UPDATE config SET value = 2;")
    write_migration(root, "0004_next.sql", "UPDATE config SET value = 4;")
    with pytest.raises(MigrationError, match="0002.*0003"):
        migrate(db, root)
    assert db.query("SELECT * FROM config") == [{"value": 3}]
    assert db.query("SELECT * FROM schema_migration ORDER BY version") == journal
    # Cấp số mới thay vì chèn vào lịch sử đã commit.
    (root / "core/db/migrations/0002_middle.sql").rename(root / "core/db/migrations/0005_middle.sql")
    assert migrate(db, root) == [4, 5]
    fresh = Database(tmp_path / "fresh.db")
    assert migrate(fresh, root) == [1, 3, 4, 5]
    assert db.query("SELECT * FROM config") == fresh.query("SELECT * FROM config")


def test_hai_runner_dong_thoi_chi_ap_mot_lan(tmp_path):
    root = tmp_path / "server"
    write_migration(root, "0001_item.sql", "CREATE TABLE item (id INTEGER); INSERT INTO item VALUES (1);")
    db = Database(tmp_path / "runner.db")
    ready = Barrier(2)

    def run(_):
        ready.wait(timeout=10)
        return migrate(db, root)

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(run, range(2)))
    assert sorted(results) == [[], [1]]
    assert db.query("SELECT * FROM item") == [{"id": 1}]
    assert db.query("SELECT version FROM schema_migration") == [{"version": 1}]


def test_cli_migrate_chay_lai_va_exit_code_loi(tmp_path):
    root = tmp_path / "server"
    write_migration(root, "0001_cli.sql", "CREATE TABLE item (id INTEGER);")
    repo = Path(__file__).resolve().parents[2]
    command = [sys.executable, "-m", "server.manage", "migrate", "--db", str(tmp_path / "cli.db"),
               "--migration-root", str(root)]
    first = subprocess.run(command, cwd=repo, capture_output=True, text=True, encoding="utf-8")
    assert first.returncode == 0, first.stderr
    assert "0001" in first.stdout
    second = subprocess.run(command, cwd=repo, capture_output=True, text=True, encoding="utf-8")
    assert second.returncode == 0, second.stderr
    assert "0 migration" in second.stdout
    write_migration(root, "0001_duplicate.sql", "SELECT 1;", block="security/seca")
    failed = subprocess.run(command, cwd=repo, capture_output=True, text=True, encoding="utf-8")
    assert failed.returncode == 1
    assert "Trùng số" in failed.stderr
