"""python machine/database/check_machine_db.py [--mysql]

--mysql uses BEVERAGE_DB_HOST/PORT/USER/PASSWORD and a disposable database.
It never selects, migrates, or drops the configured BEVERAGE_DB_NAME.
"""

import ast
import os
from pathlib import Path
import re
import sqlite3
import sys
import uuid


SOURCE = Path(__file__).resolve().parents[3] / "version1.0"
SCHEMA = Path(__file__).with_name("machine.db")


def source_values(relative_path, names):
    tree = ast.parse((SOURCE / relative_path).read_text(encoding="utf-8-sig"))
    return {
        target.id: ast.literal_eval(node.value)
        for node in tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name) and target.id in names
    }


# Reuse the existing SQL splitter without importing DB config or machine hardware.
tree = ast.parse((SOURCE / "database/db_core.py").read_text(encoding="utf-8-sig"))
splitter = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "split_sql_statements")
namespace = {}
exec(compile(ast.Module(body=[splitter], type_ignores=[]), "split_sql", "exec"), namespace)
statements = namespace["split_sql_statements"](SCHEMA.read_text(encoding="utf-8"))
tables = {re.match(r"CREATE TABLE (\w+)", sql)[1]
          for sql in statements if sql.startswith("CREATE TABLE ")}
references = {name for sql in statements for name in re.findall(r"REFERENCES (\w+)", sql)}
assert references <= tables, references - tables
assert not tables & {"admin_user", "role_permission", "menu", "machine"}
assert not any(sql.startswith(("ALTER ", "DROP ", "INSERT ", "UPDATE ")) for sql in statements)
queries = []
for path, names in (
    ("store_gui/sync_menu.py", {"DRINK_QUERY", "SETTING_QUERY", "BESTSELLER_QUERY",
                               "CATEGORY_QUERY", "MAPPING_QUERY", "RECIPE_QUERY"}),
    ("database/export_data.py", {"MENU_QUERY", "ACTION_QUERY", "RECIPE_QUERY"}),
    ("scan/generate_drink_qr.py", {"DRINK_QUERY", "INGREDIENT_QUERY", "RECIPE_QUERY"}),
):
    values = source_values(path, names)
    assert values.keys() == names
    queries.extend(values.items())

# Prepare the actual reader SQL against declared columns in memory.
# This catches removed columns still used by runtime; it does NOT test MySQL DDL/triggers.
with sqlite3.connect(":memory:") as columns_check:
    for sql in statements:
        if not sql.startswith("CREATE TABLE "):
            continue
        table = re.match(r"CREATE TABLE (\w+)", sql)[1]
        columns = re.findall(
            r"^    (\w+)\s+(?:INT|BIGINT|VARCHAR|CHAR|TEXT|DECIMAL|DATETIME|BOOLEAN|TINYINT)\b",
            sql, re.MULTILINE,
        )
        columns_check.execute(f"CREATE TABLE {table} ({','.join(columns)})")
    for name, sql in queries:
        sql = sql.replace("NOW() - INTERVAL %s DAY", "datetime('now', '-' || ? || ' days')")
        columns_check.execute("EXPLAIN " + sql.replace("%s", "?"),
                              (30, 6) if name == "BESTSELLER_QUERY" else ())
print(f"Static checks passed: {len(tables)} tables, {len(statements)} statements, "
      f"{len(queries)} reader queries match declared columns.")

if "--mysql" not in sys.argv[1:]:
    print("MySQL execution not tested; use --mysql with a test MySQL 8 server.")
    raise SystemExit(0)

import mysql.connector

connection = mysql.connector.connect(
    host=os.getenv("BEVERAGE_DB_HOST", "localhost"),
    port=int(os.getenv("BEVERAGE_DB_PORT", "3306")),
    user=os.getenv("BEVERAGE_DB_USER", "root"),
    password=os.environ["BEVERAGE_DB_PASSWORD"],
    connection_timeout=5,
    autocommit=True,
)
database = "machine_schema_check_" + uuid.uuid4().hex
assert re.fullmatch(r"machine_schema_check_[0-9a-f]{32}", database)
cursor = connection.cursor()
created = False
try:
    cursor.execute(f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4")
    created = True
    cursor.execute(f"USE `{database}`")
    for sql in statements:
        cursor.execute(sql)

    # Execute the real non-admin reader queries against the schema.
    for name, sql in queries:
        cursor.execute(sql, (30, 6) if name == "BESTSELLER_QUERY" else None)
        cursor.fetchall()

    cursor.execute("INSERT INTO drink (drink_id,drink_name,price) VALUES (1001,'Test',30000)")
    cursor.execute("INSERT INTO ingredient (ingredient_id,ingredient_name,amount,threshold_gram) "
                   "VALUES (1,'Water',100,60)")
    cursor.execute("INSERT INTO recipe VALUES (1001,1,1,50)")
    cursor.execute("SELECT in_stock FROM drink WHERE drink_id=1001")
    assert cursor.fetchone() == (1,)
    connection.start_transaction()
    cursor.execute("UPDATE ingredient SET amount=10 WHERE ingredient_id=1")
    cursor.execute("SELECT in_stock FROM drink WHERE drink_id=1001")
    assert cursor.fetchone() == (0,)
    connection.rollback()
    cursor.execute("SELECT amount,in_stock FROM ingredient WHERE ingredient_id=1")
    assert cursor.fetchone() == (100, 1)
    cursor.execute("SELECT in_stock FROM drink WHERE drink_id=1001")
    assert cursor.fetchone() == (1,)

    cursor.execute("INSERT INTO order_ticket (drink_id,price,drink_name,payload,payload_hash) "
                   "SELECT drink_id,price,drink_name,'123',%s FROM drink WHERE drink_id=1001",
                   ("a" * 64,))
    for expected in (1, 0):
        cursor.execute("UPDATE order_ticket SET status='in_progress' "
                       "WHERE payload_hash=%s AND status='unused'", ("a" * 64,))
        assert cursor.rowcount == expected
    try:
        cursor.execute("INSERT INTO order_ticket (drink_id,payload,payload_hash) "
                       "VALUES (1001,'123',%s)", ("a" * 64,))
    except mysql.connector.IntegrityError as error:
        assert error.errno == 1062
    else:
        raise AssertionError("Duplicate QR must be rejected")
    cursor.execute("DELETE FROM recipe WHERE drink_id=1001")
    cursor.execute("SELECT in_stock FROM drink WHERE drink_id=1001")
    assert cursor.fetchone() == (0,)
    cursor.execute("DELETE FROM drink WHERE drink_id=1001")
    cursor.execute("SELECT price,drink_name FROM order_ticket")
    assert cursor.fetchone() == (30000, "Test")
    print("MySQL checks passed: readers, stock triggers/rollback, QR single claim, sale history.")
finally:
    if created:
        cursor.execute(f"DROP DATABASE `{database}`")
    cursor.close()
    connection.close()
