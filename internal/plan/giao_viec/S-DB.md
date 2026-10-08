# Giao việc khối S-DB · cho GPT Sol (Codex)

Dán toàn bộ file này vào Codex, mở tại thư mục `D:\PROJECT\CODE\InternProj\server`.

---

Bạn là coder của dự án "server mẹ FlexMix". Bạn làm đúng **một khối: S-DB**. Làm gọn, đúng phạm vi, không thêm việc ngoài danh sách. Code, comment và tài liệu viết tiếng Việt có dấu, câu ngắn.

## 0. Điều kiện bắt đầu

Kiểm tra trước khi làm gì khác:

1. `git log --oneline` có commit của khối C0 (hợp đồng).
2. Các file sau tồn tại:
   - `internal/contracts/interfaces.md`
   - `internal/contracts/db_ownership.md`
   - `server/config/settings.py`
   - `server/contracts/`
   - `tests/c0/test_isolation.py`

Thiếu bất kỳ thứ nào thì **dừng lại**, báo "C0 chưa xong" và không viết code.

## 1. Bối cảnh cần đọc

| File | Đọc phần nào |
|---|---|
| `internal/plan/index.md` | Mục "Module cô lập, nối tại một điểm", "Quy ước", "Định nghĩa khối xong" |
| `internal/plan/khoi_server.md` | Mục "S-DB · MySQL và migration": đây là đặc tả của bạn |
| `internal/contracts/interfaces.md` | Phần nói về S-DB: chữ ký hàm bạn phải cung cấp |
| `internal/contracts/db_ownership.md` | Bảng nào do khối nào ghi; S-DB không giữ bảng nghiệp vụ |
| `server/config/settings.py` | Cách đọc cấu hình DB |
| `D:\PROJECT\CODE\InternProj\version1.0\database\db_core.py`, `migrate.py` | Kiểu viết để chép logic. **Không import** từ đó |

## 2. Việc phải làm

Code đặt ở `server/core/db/`.

| ID | Việc | Kiểm |
|---|---|---|
| S-DB.1 | Pool mysql-connector, `transaction()` dạng context manager, `query()`. Chữ ký đúng như `interfaces.md` | Lỗi giữa transaction thì rollback |
| S-DB.2 | Chạy migration theo số, ghi bảng `schema_migration`. Mỗi khối mang file migration trong thư mục của nó (`server/modules/<tên>/migrations/`, `server/security/*/migrations/`, `server/core/*/migrations/`). Runner tự tìm các thư mục đó, sắp theo số rồi theo tên khối, và từ chối khi hai file trùng số. Thêm lệnh `python -m server.manage migrate` | Chạy hai lần, lần hai không đổi gì; hai file trùng số thì báo lỗi rõ |
| S-DB.3 | Khi khởi động, đọc `innodb_flush_log_at_trx_commit` và `sync_binlog`; khác 1 thì ném lỗi và không chạy | Test với giá trị sai |

`server/manage.py` có thể chưa có. Nếu chưa có thì tạo file tối thiểu, chỉ có lệnh `migrate`, và ghi chú rằng các lệnh khác do khối khác thêm qua điểm nối.

## 3. Test

- Đặt ở `tests/s_db/`.
- Máy dev **không có MySQL**:
  - Phần không cần DB thật (tìm và sắp migration, phát hiện trùng số, kiểm cấu hình bằng kết nối giả) phải chạy được ngay.
  - Phần cần MySQL thật đánh dấu `pytest.mark.skipif(not os.environ.get("FLEXMIX_TEST_MYSQL"), ...)`. Biến này là DSN tới một DB dùng một lần.
- `.venv` không theo vào worktree. Dùng Python trong `.venv` của thư mục repo gốc:
  ```
  ..\server\.venv\Scripts\python -m pytest tests/s_db tests/c0 -q
  ```
  Test `tests/c0/test_isolation.py` phải vẫn xanh.

## 4. Không được

- Chỉ sửa trong `server/core/db/`, `tests/s_db/`, `server/manage.py` (chỉ phần `migrate`) và `internal/plan/bang_chung/S-DB.md`.
- **Không sửa** `server/wiring.py`, `server/contracts/`, `server/config/routing.py`, `internal/contracts/`, `internal/plan/*.md`, `docs/`, `machine/`, `spike/`.
- Thấy hợp đồng thiếu hoặc sai thì **không tự sửa**. Ghi vào báo cáo, mục "Cần đổi hợp đồng".
- Không import module nghiệp vụ nào. Không cài phần mềm hệ thống. Chỉ `pip install` vào `.venv` khi thật cần (`mysql-connector-python`).

## 5. Git

1. Tạo nhánh và worktree riêng để không đụng agent khác:
   ```
   git worktree add ..\server-wt-s-db -b khoi/s-db
   ```
   Làm việc trong `..\server-wt-s-db`.
2. Chỉ `git add` đúng các file của bạn. Không dùng `git add -A` hay `git add .`.
3. Commit message tiếng Việt, mở đầu bằng `S-DB:`.
4. Không merge vào `main`. Operator sẽ review rồi mới merge.

## 6. Báo cáo khi xong

Ghi `internal/plan/bang_chung/S-DB.md`, gồm:

- danh sách file;
- lệnh test và output rút gọn;
- test nào bị skip vì thiếu MySQL;
- từng bước S-DB.1 đến S-DB.3: đạt, chưa đạt hay chưa kiểm được;
- mục "Cần đổi hợp đồng", nếu có.

Trả lời cuối ngắn gọn, đúng nội dung đó.
