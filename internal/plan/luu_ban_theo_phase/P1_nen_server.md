# P1 · Nền server và kênh quản trị

- **Trạng thái:** CHƯA THỰC HIỆN.
- **Luồng thiết kế:** A1, A2, A3, M2 (phía server), mục 6 (bảng cổng), mục 8 (schema), mục 10 (stack).

## Mục tiêu

Server chạy được trên Linux trong LAN:

- có hai cổng HTTPS dùng CA nội bộ;
- người quản lý đăng nhập được, quản lý nhân viên và gán máy cho nhân viên, y như admin_gui.

Chưa có máy nào nối vào ở phase này.

## Điều kiện vào

- P0 ✓. Phiên bản thư viện đã ghim, cheroot long-poll qua TLS đã chạy được.
- Có MySQL 8 trên máy dev.
- Muốn nghiệm thu P1.4 trên máy thật thì cần thêm Q9 (máy server, IP) và Q2 (cài root CA).

## Đầu ra

| Đầu ra | File |
|---|---|
| routing bản 2 và bảng `ROUTE_POLICY` | `server/server/config/routing.py` |
| Cấu hình chạy: cổng, đường dẫn file khoá, DB, các tham số | `server/server/config/settings.py` (mới) |
| Ứng dụng Flask và hai server cheroot | `server/server/app.py`, `server/server/main.py` |
| Lớp DB và migration đầu | `server/server/db/`, `db/migrations/0001_core.sql` |
| Công cụ tạo CA, cấu hình chrony, unit systemd | `server/deploy/server/` |
| Bảo mật A | `server/server/security/{tls,session,permissions,ratelimit}.py` |
| Module tài khoản, nhân viên, máy (phần quản trị) | `server/server/modules/accounts/`, `modules/machines/` |
| Trang quản trị: khung, đăng nhập, trang chủ, nhân viên, máy | `server/server/static/` |
| Test | `server/tests/p1/` |

`settings.py` là file mới so với cây thư mục ở mục 10. Lý do: `routing.py` chỉ giữ đường dẫn, còn cổng, đường dẫn khoá và các tham số W, hạn mã ghép… cần một chỗ riêng mà user đổi được.

## Phase con

### P1.1 Routing bản 2

Làm theo danh sách "Cần sửa routing.py khi bắt đầu code" ở mục 7 của thiết kế.

| ID | Việc | Kiểm |
|---|---|---|
| P1.1.1 | Đổi sang POST: `AGENT_COMMANDS_PATH`, `AGENT_MENU_PATH`. Đổi `AGENT_COMMAND_RESULT_PATH` thành `AGENT_RESULTS_PATH = "/api/agent/results"`. Đổi `AGENT_MEDIA_PATH` thành `/api/agent/media/{sha256}` | Test: mọi hằng `_PATH` khác nhau, bắt đầu bằng `/api/` |
| P1.1.2 | Bỏ `AGENT_HEARTBEAT_PATH`, `MACHINE_TOKEN_ROTATE_PATH` | `grep` không còn |
| P1.1.3 | Thêm `AGENT_TRUST_PATH`, `AGENT_ENROLL_PATH`, `MACHINE_ENROLL_CODE_PATH`, `MACHINE_REVOKE_PATH`, `MACHINE_COMMAND_PATH`, `MACHINE_COMMAND_CHECK_PATH`, `DISPLAY_APPLY_PATH`, `DISPLAY_KEEP_PATH`, `STEPUP_PATH`, `CLOCK_CONFIRM_PATH`, `CA_CERT_PATH`, cùng nhóm menu theo `menu_id` | Danh sách khớp mục 7 |
| P1.1.4 | Khai bảng `ROUTE_POLICY`: mỗi route agent một chế độ (`trust`, `enroll`, `fm1`, `tls_only` cho media). P1 chỉ khai báo; P4 mới dùng | Test: mọi hằng `AGENT_*` có mặt trong bảng |

- **Không làm:** chưa viết handler nào cho route agent.
- **Rollback:** `git revert`.

### P1.2 Khung ứng dụng và hai cổng

| ID | Việc | File | Kiểm |
|---|---|---|---|
| P1.2.1 | `settings.py`: đọc file cấu hình (`/etc/flexmix-server/server.toml` khi chạy thật, file mẫu trong repo). Giá trị mặc định lấy theo bảng tham số ở `index.md` | `config/settings.py` | Thiếu khoá bắt buộc thì dừng khi khởi động, không đoán |
| P1.2.2 | `app.py`: hai app Flask, một cho quản trị, một cho agent. App agent chỉ có route `/api/agent/*` | `app.py` | Gọi route quản trị vào cổng agent thì 404, và ngược lại |
| P1.2.3 | `main.py`: hai server cheroot, mỗi cổng một pool thread, một tín hiệu đánh thức chung (`threading.Condition`) theo mẫu đã chạy ở P0.5. Tắt êm khi nhận SIGTERM | `main.py` | `systemctl stop` không để kết nối treo; log ghi rõ cổng |
| P1.2.4 | Log: một logger, không ghi body, không ghi cookie, không ghi khoá | `main.py` | Test: log của một request đăng nhập không có mật khẩu |

### P1.3 DB server và migration đầu

| ID | Việc | File | Kiểm |
|---|---|---|---|
| P1.3.1 | Lớp kết nối: mysql-connector, pool, hàm `transaction()` dạng context manager. Lấy kiểu viết từ `version1.0/database/db_core.py` | `db/core.py` | Test: lỗi giữa transaction thì rollback |
| P1.3.2 | Chạy migration theo số, ghi vào `schema_migration`. Kiểu làm theo `version1.0/database/migrate.py` | `db/migrate.py` | Chạy hai lần liên tiếp, lần hai không đổi gì |
| P1.3.3 | `0001_core.sql`: `schema_migration`, `admin_user` (mốc thu hồi phiên kiểu BIGINT), `role_permission`, `machine` (không có `secret_enc`, có `clone_flag_at`, `menu_id`, `last_seen`), `user_machine`, `server_state` (`server_epoch`, `max_now_seen`) | `db/migrations/0001_core.sql` | Áp lên MySQL 8 rỗng thành công |
| P1.3.4 | Ghi yêu cầu cấu hình InnoDB: `innodb_flush_log_at_trx_commit=1`, `sync_binlog=1`. Server từ chối khởi động nếu hai giá trị này khác | `db/core.py` | Test với MySQL đặt sai thì không khởi động |

- Các bảng menu ở P2, khoá và credential ở P4, lệnh ở P6.
- Không có cột `machine_id` nào là khoá ngoại tới bảng nguyên liệu: nguyên liệu nằm ở máy (`hieu_biet_server_me.md` §8).

### P1.4 PKI, TLS và giờ

| ID | Việc | File | Kiểm |
|---|---|---|---|
| P1.4.1 | `make_ca.py`: sinh root và leaf. Root ghi ra đường dẫn do người vận hành chọn (USB), không ghi vào thư mục dự án. SAN của leaf lấy từ cấu hình (IP hoặc tên, Q9). Hạn leaf lấy từ tham số (Q4) | `deploy/server/make_ca.py` | `openssl x509 -text` thấy đúng SAN và hạn |
| P1.4.2 | `tls.py`: `SSLContext` chỉ TLS 1.3, nạp leaf và khoá quyền 0600; sai quyền thì dừng | `security/tls.py` | `openssl s_client -tls1_2` bị từ chối; `-tls1_3` được |
| P1.4.3 | Cổng 80: chỉ chuyển hướng sang HTTPS và cho tải `ca.crt` kèm vân tay SHA-256 (`CA_CERT_PATH`) | `app.py` | `curl http://…/` trả 301; tải được `ca.crt` |
| P1.4.4 | `chrony.conf`: `local stratum 10`, `allow <dải LAN>`, không trỏ nguồn ngoài (M2) | `deploy/server/chrony.conf` | `chronyc tracking` trên server; một máy trong LAN lấy được giờ |
| P1.4.5 | Unit systemd `flexmix-server.service`, chạy bằng user riêng, đọc được thư mục khoá | `deploy/server/flexmix-server.service` | Khởi động lại máy, server tự lên |

- **Không dùng lại CA cũ** trong `.caddy-data`, vì khoá riêng của nó đang nằm trong thư mục dự án (rủi ro ở mục 13).

### P1.5 Bảo mật A

| ID | Việc | File | Kiểm (test tự động) |
|---|---|---|---|
| P1.5.1 | Token phiên ký bằng khoá trong file 0600. Token mang `role`, `machine_ids`, `server_epoch`, hạn, mốc phát | `security/session.py` | Sửa 1 byte trong token thì 401 |
| P1.5.2 | Cookie HttpOnly, Secure, SameSite=Strict. Không còn token trong `sessionStorage` | `session.py` | Header `Set-Cookie` đủ ba cờ |
| P1.5.3 | Header chống CSRF `X-FM-Req` bắt buộc cho mọi request đổi dữ liệu | `session.py` | POST thiếu header thì 403 |
| P1.5.4 | Mốc thu hồi phiên so bằng số giây epoch nguyên, không so DATETIME (B14) | `session.py` | Test: đổi mật khẩu thì phiên cũ hỏng |
| P1.5.5 | CSP `script-src 'self'`, không có script inline | `app.py` | Header CSP có trên mọi trang; trang mẫu có inline script thì trình duyệt chặn |
| P1.5.6 | Rate-limit đăng nhập theo user và theo IP | `security/ratelimit.py` | Vượt ngưỡng thì 429; cổng agent không bị ảnh hưởng |
| P1.5.7 | Xác thực lại (`STEPUP_PATH`) cho thao tác nhạy cảm. Danh sách lấy ở A1 "Các bước và tham số" | `session.py` | Gọi thao tác nhạy cảm mà không xác thực lại thì 401 |
| P1.5.8 | Quyền theo khu vực và theo máy: khu vực giữ nguyên admin_gui; máy lấy từ `user_machine`, owner thấy mọi máy | `security/permissions.py` | Bảng test role × khu vực × máy |

- **Nguồn để chép logic:** `version1.0/admin_gui/auth.py` (pbkdf2, compare_digest) và `permissions.py`. Chép logic, không import.

### P1.6 Tài khoản, nhân viên, máy

| ID | Luồng | Route | File | Kiểm |
|---|---|---|---|---|
| P1.6.1 | A1 Đăng nhập | `LOGIN_PATH`, `WHOAMI_PATH`, `MY_PASSWORD_PATH` | `modules/accounts/` | Sai mật khẩu: 401 thân cố định; đúng: cookie |
| P1.6.2 | A2 Nhân viên và quyền | `USERS_PATH`, `USER_*_PATH`, `PERMISSIONS_*_PATH` | `modules/accounts/` | Ba role owner, manager, staff và tám khu vực như admin_gui |
| P1.6.3 | A3 Gán máy | `user_machine` | `modules/accounts/` | Manager cửa hàng A không thấy máy B |
| P1.6.4 | Danh sách và sửa máy (chưa ghép) | `MACHINES_PATH`, `MACHINE_SAVE_PATH`, `MACHINE_DELETE_PATH`, `MACHINE_STATUS_PATH` | `modules/machines/` | Tạo, sửa tên, xoá máy chưa ghép |
| P1.6.5 | Tạo owner đầu tiên bằng dòng lệnh, giống `admin_gui.auth --set-password` | `server/server/manage.py` | Chạy trên DB rỗng tạo được owner |

### P1.7 Trang quản trị: khung và các trang của P1

| ID | Việc | Kiểm |
|---|---|---|
| P1.7.1 | Chép `admin.css`, `admin-guard.js`, `login`, `home`, `users` từ `version1.0/admin_gui/` sang `server/server/static/` | Trang mở được qua HTTPS |
| P1.7.2 | `admin-guard.js`: bỏ đọc token từ `sessionStorage`; gửi `X-FM-Req`; 401 thì về trang đăng nhập và bỏ mọi thao tác đang chờ | Test tay: hết phiên thì quay về đăng nhập |
| P1.7.3 | Thêm bộ chọn máy chung ở đầu trang, theo quyền | Manager chỉ thấy máy của mình |
| P1.7.4 | Dữ liệu đến từ máy hiện bằng `textContent`, không bằng `innerHTML` (B10). P1 chỉ áp cho các trang chép ở P1.7.1; các trang khác áp ở phase chép trang đó | `grep innerHTML static/` chỉ còn chỗ chèn chuỗi cố định |
| P1.7.5 | Trang Máy: danh sách, trạng thái online, nút tạo mã ghép (nút bị khoá tới P4) | Hiện đúng danh sách |

## Cổng ra P1

- `pytest server/tests/p1 -q` đạt.
- Từ máy tính quản trị và một điện thoại đã cài root CA (Q2): mở được trang qua HTTPS không có cảnh báo, đăng nhập được, đổi quyền được.
- `openssl s_client` chứng minh chỉ có TLS 1.3.
- Reviewer và cybersecurity duyệt Bảo mật A.

## Rủi ro và quay lui

| Rủi ro | Cách xử lý |
|---|---|
| Trình duyệt di động không nhận cert leaf hạn dài | Thử ở P1.4 trên thiết bị thật; rút hạn leaf, đưa lại user chọn ở Q4 |
| CSP chặn trang chép từ admin_gui | Thiết kế ghi admin_gui không có script inline (A1). Nếu gặp thì tách script ra file, không nới CSP |
| Đổi IP server | Cấp lại leaf bằng `make_ca.py`; ghi vào runbook ở P8 |
