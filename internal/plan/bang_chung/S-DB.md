# Bằng chứng S-DB · SQLite tạm

Ngày 08/10/2026 (Bangkok). Trạng thái: **review sửa lỗi đạt trên dev; chờ MySQL/R1**.

Cập nhật sau review: đã sửa P2 chèn migration số cũ, test đỏ trước sửa và xanh
sau sửa; bộ kiểm tích hợp đạt 161 test. Chi tiết/kiểm lại tại [REVIEW_CODEX.md](REVIEW_CODEX.md).

Theo yêu cầu mới của user, S-DB dùng file SQLite `.db` trước, sẽ migrate sang
MySQL sau. Không coi SQLite là bằng chứng đạt các tiêu chí InnoDB của plan gốc.
Thông báo phối hợp: `internal/plan/giao_viec/CODEX_SQLITE_THONG_BAO_CLAUDE.md`
ở repo chính. Không sửa hợp đồng C0, settings hoặc wiring trong nhánh S-DB.

## File

- `server/core/db/__init__.py`: kết nối, transaction và query.
- `server/core/db/migrations.py`: tìm migration, kiểm lịch sử, áp migration.
- `server/manage.py`: lệnh migrate tối thiểu.
- `tests/s_db/test_db.py`: kiểm với SQLite thật trên file tạm.
- `internal/plan/bang_chung/S-DB.md`: báo cáo này.

Không có dependency mới, bảng nghiệp vụ, file DB hoặc khóa bí mật trong commit.
Chỉ S-DB ghi bảng `schema_migration`.

## API tạm

```python
from server.core.db import Database
from server.core.db.migrations import discover, migrate

db = Database(path, timeout=10.0)
with db.transaction(immediate=False) as conn:
    conn.execute(sql, parameters)
rows = db.query(sql, parameters=())
files = discover(root)
versions = migrate(db, root)
```

- `path` bắt buộc, là file SQLite; không nhận `:memory:` vì mỗi transaction
  mở và đóng kết nối riêng. Dùng chung đối tượng `Database` giữa thread được;
  không chia sẻ `conn`. Không gọi commit/rollback/executescript trong transaction.
- `transaction()` commit khi thành công, rollback cả DDL/DML khi có lỗi, rồi
  đóng kết nối. `immediate=True` lấy quyền ghi trước; runner dùng chế độ này
  để hai tiến trình không cùng áp một migration.
- `query()` chạy một câu SQL, trả `list[dict]`; DDL/DML không có RETURNING trả
  `[]`. Cần `lastrowid` hoặc `rowcount` thì dùng cursor trong `transaction()`.
  Các câu `query()` riêng là các transaction riêng.
- Tham số SQL là `?` hoặc tham số đặt tên của SQLite. Không dùng `%s` của MySQL.
- `root` là thư mục package `server`, chứa `core`, `security`, `modules`.
  `discover()` trả `(number: int, name: str, path: Path)`, tìm tại
  `core/*/migrations/`, `security/*/migrations/`, `modules/*/migrations/`.
  Tên file là `NNNN_ten.sql`; số dùng chung toàn server, không được trùng.
  `name` là đường dẫn tương đối từ root; sắp theo số rồi theo tên khối.
- `migrate()` trả danh sách số vừa áp. SHA-256 tính từ bytes gốc; đổi nội dung,
  đổi tên hoặc thiếu file đã áp đều bị từ chối trước khi chạy phần mới.
  Migration bổ sung phải có số lớn hơn mọi số đã áp; số cũ bị từ chối cả đợt.
  Đợt lỗi rollback cả migration mới và sổ; đợt đã commit trước đó giữ nguyên.
- SQL được tách bằng `sqlite3.complete_statement`, hỗ trợ chuỗi, comment và
  trigger có dấu `;`. Migration không tự điều khiển transaction, thay PRAGMA,
  attach database hoặc ghi bảng sổ. Đây là SQL nguồn tin cậy, không phải sandbox
  để chạy SQL người dùng.

```text
python -m server.manage migrate
python -m server.manage migrate --db var/flexmix.db --migration-root server
```

Mặc định DB ở `var/flexmix.db` tính từ thư mục chạy lệnh; migration root lấy
từ package `server`. Nếu chưa có migration nghiệp vụ, chỉ tạo sổ rỗng. CLI
trả exit code 1 khi thất bại và xuất tiếng Việt UTF-8 cả trên Windows.

## Phép kiểm

Chạy trong worktree `server-wt-s-db`, dùng venv của repo chính:

```text
..\server\.venv\Scripts\python.exe -m pytest tests/s_db tests/c0 -q
...............................                                          [100%]
31 passed in 0.98s
```

20 phép kiểm S-DB và 11 phép kiểm routing C0 hiện có đạt. Không có test bị
skip. `tests/c0/test_isolation.py` chưa có trong commit nền của worktree;
không ghi nhận phép kiểm đó đã đạt. Parent sẽ chạy lại với C0 mới khi ráp.

Kiểm thực tế: tham số SQL, commit và rollback DML/DDL; foreign key kể cả lỗi
ở lúc commit; PRAGMA foreign_keys=1, synchronous=2 (FULL), busy_timeout=10000;
timeout sai; 4 thread dùng 4 connection và giữ đủ dữ liệu; 2 runner đồng thời
chỉ áp một lần; tìm đủ ba khu vực; tên/số sai; trigger/chuỗi/comment; checksum,
file thiếu, chạy lại; migration hỏng rollback cả đợt; CLI thành công/chạy lại/lỗi.

## Từng bước của plan gốc

| Bước | Kết quả |
|---|---|
| S-DB.1 | Transaction/query SQLite tạm đã kiểm; pool mysql-connector chưa làm theo thay đổi của user |
| S-DB.2 | Discovery, thứ tự, sổ, checksum, idempotence, rollback và CLI đã kiểm với SQLite |
| S-DB.3 | Chưa đạt tiêu chí MySQL: không có InnoDB hoặc sync_binlog trên SQLite; không giả lập kết quả |

SQLite một writer, không có pool MySQL; timeout mặc định 10 giây. Bật
foreign_keys và synchronous FULL trên từng kết nối. Chưa kiểm mất điện,
phần cứng Pi, tải sản xuất hoặc lần ráp R1.

## Cần đổi hợp đồng / migrate sau

C0 còn thiếu tại commit nền. Cần đối chiếu API tạm với C0 do Codex tiếp tục
thực hiện khi Claude hết token; chỉ lần ráp mới thêm settings/wiring.

Khi môi trường MySQL sẵn sàng, bổ sung backend mysql-connector, đổi SQL và
placeholder theo dialect MySQL, chốt kiểu dữ liệu nghiệp vụ, chuyển dữ liệu
có đối chiếu số dòng/ràng buộc, kiểm InnoDB/sync_binlog và chạy lại test MySQL.
MySQL DDL có implicit commit, nên không được suy ra rollback DDL của MySQL
từ bằng chứng SQLite này. Chưa tạo công cụ chuyển dữ liệu vì chưa có schema
nghiệp vụ cần chuyển.
