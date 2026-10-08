# Khối phía server

- **Trạng thái:** CHƯA THỰC HIỆN.
- **Nơi đặt code:** theo mục "Module cô lập" của `index.md`.
  - S-DB ở `server/server/core/db/`, S-NET ở `core/net/`, UI-SHELL ở `server/server/static/shell/`.
  - S-SECA ở `security/seca/`, S-FM1 ở `security/fm1/`, S-EPOCH ở `core/epoch/`.
  - Mỗi module M-* ở `modules/<tên>/`, ví dụ `modules/menu/`.
  - Không khối nào import ruột khối khác. Mọi thứ nối qua `contracts/` và `wiring.py`.
- **Test:** `server/tests/<khối>/`. Mọi khối test được một mình bằng stub.

Mỗi khối dưới đây có các mục:

- trách nhiệm;
- hợp đồng: khối cung cấp gì, khối cần gì;
- stub dùng khi test riêng;
- các bước;
- điều kiện xong.

## Nền

### S-DB · MySQL và migration

- **Trách nhiệm:** kết nối, transaction, chạy migration. Không giữ bảng nghiệp vụ nào.
- **Cung cấp:** `db.transaction()` (context manager), `db.query()`, lệnh `manage.py migrate`.
- **Cần:** C0.9 (cấu hình DB).
- **Stub:** không cần. Test chạy với MySQL 8 thật trên máy dev, DB dùng một lần.

| ID | Việc | Kiểm |
|---|---|---|
| S-DB.1 | Pool mysql-connector, `transaction()` dạng context manager. Lấy kiểu viết từ `version1.0/database/db_core.py` | Lỗi giữa transaction thì rollback |
| S-DB.2 | Chạy migration theo số, ghi `schema_migration`. Kiểu làm theo `version1.0/database/migrate.py`. Mỗi khối mang file migration riêng | Chạy hai lần, lần hai không đổi gì |
| S-DB.3 | Từ chối khởi động nếu `innodb_flush_log_at_trx_commit` khác 1 hoặc `sync_binlog` khác 1 | Test với MySQL đặt sai |

**Xong khi:** `pytest tests/s_db -q` đạt.

### S-NET · TLS, hai cổng, giờ

- **Trách nhiệm:**
  - CA nội bộ và TLS 1.3;
  - hai server cheroot, cổng quản trị và cổng agent, mỗi cổng một pool;
  - cổng 80;
  - tín hiệu đánh thức dùng chung;
  - chrony, systemd, log.
- **Cung cấp:** `serve(admin_app, agent_app)`, `wake.notify(machine_id)` / `wake.wait(machine_id, timeout)`, `CA_CERT_PATH`.
- **Cần:** G0.7 (mẫu cheroot đã chạy), C0.2, C0.9.
- **Stub:** hai app Flask giả, mỗi app một route.

| ID | Việc | Kiểm |
|---|---|---|
| S-NET.1 | `make_ca.py`: sinh root và leaf. Root ghi ra đường dẫn do người vận hành chọn (USB), không ghi vào thư mục dự án. SAN và hạn leaf lấy từ cấu hình (Q9, Q4). Không dùng lại CA trong `.caddy-data` | `openssl x509 -text` thấy đúng SAN và hạn |
| S-NET.2 | `tls.py`: chỉ TLS 1.3; khoá phải có quyền 0600, sai thì dừng | `openssl s_client -tls1_2` bị từ chối |
| S-NET.3 | `main.py`: hai server cheroot, hai pool; tắt êm khi nhận SIGTERM | Route của app này gọi vào cổng kia thì 404 |
| S-NET.4 | Tín hiệu đánh thức theo máy, dùng chung giữa hai pool | Treo `wait`, gọi `notify`: trả về ngay |
| S-NET.5 | Cổng 80: chỉ chuyển hướng sang HTTPS và cho tải `ca.crt` kèm vân tay SHA-256 | `curl` trả 301; tải được `ca.crt` |
| S-NET.6 | Log: không ghi body, cookie, khoá | Log của một request mẫu không có các trường đó |
| S-NET.7 | `chrony.conf` (`local stratum 10`, `allow <dải LAN>`, không trỏ nguồn ngoài); unit `flexmix-server.service` chạy bằng user riêng | Máy trong LAN lấy được giờ; reboot thì server tự lên |

**Xong khi:** test đạt; flood cổng quản trị không cắt poll treo ở cổng agent (lặp lại G0.7 trên code thật).

### UI-SHELL · Khung trang quản trị

- **Trách nhiệm:** phần dùng chung của mọi trang:
  - `admin.css`;
  - `admin-guard.js`;
  - đầu trang và bộ chọn máy;
  - hàm hiện chữ an toàn;
  - xử lý 401;
  - sinh `request_key`.

  Trang của từng chức năng thuộc khối module tương ứng.
- **Cung cấp:** `api(path, body)` tự gửi `X-FM-Req`; `newRequestKey()` dùng `crypto.randomUUID()`; `setText(el, s)`; `machinePicker()`.
- **Cần:** C0.2.
- **Stub:** server giả trả JSON cố định.

| ID | Việc | Kiểm |
|---|---|---|
| UI.1 | Chép `admin.css`, `admin-guard.js` từ `version1.0/admin_gui/`. Bỏ token trong `sessionStorage`; dùng cookie | `grep sessionStorage` không còn |
| UI.2 | 401 thì về trang đăng nhập và bỏ mọi thao tác đang chờ, không tự gửi lại | Test tay với server giả |
| UI.3 | Không có script inline, để chạy được dưới CSP `script-src 'self'` | Mở trang với header CSP, console không báo chặn |
| UI.4 | `setText` là đường duy nhất để hiện dữ liệu đến từ máy (B10) | Quy ước cho mọi trang: `grep innerHTML` chỉ còn chỗ chèn chuỗi cố định |

## Bảo mật

### S-SECA · Bảo mật A

- **Trách nhiệm:** mọi request của trang quản trị đi qua đây trước khi tới module.
- **Cung cấp:**
  - `require(area, machine_id=None)`;
  - `require_stepup()`;
  - `idempotent(request_key, body)`;
  - `check_epoch(form_epoch)`;
  - `session.rotate_key()`.
- **Cần:** `accounts.load_user`, `accounts.machines_of` (C0.10); `epoch.current()`.
- **Stub:** M-ACC giả (ba user: owner, manager có máy 1, staff), S-EPOCH giả.

| ID | Việc | Kiểm |
|---|---|---|
| S-SECA.1 | Token phiên ký bằng khoá trong file 0600; mang role, `machine_ids`, `server_epoch`, hạn, mốc phát | Sửa 1 byte thì 401 |
| S-SECA.2 | Cookie HttpOnly, Secure, SameSite=Strict | Header đủ ba cờ |
| S-SECA.3 | Header `X-FM-Req` bắt buộc cho request đổi dữ liệu | Thiếu thì 403 |
| S-SECA.4 | Mốc thu hồi phiên so bằng số giây epoch nguyên (B14) | Đổi mật khẩu thì phiên cũ hỏng |
| S-SECA.5 | CSP `script-src 'self'` trên mọi trang | Header có mặt |
| S-SECA.6 | Rate-limit đăng nhập theo user và IP | Vượt ngưỡng thì 429; cổng agent không bị ảnh hưởng |
| S-SECA.7 | Xác thực lại cho thao tác nhạy cảm (`STEPUP_PATH`): tạo mã ghép, thu hồi máy, đổi quyền, xác nhận giờ, chuyển vé về chưa dùng (theo Q3) | Thiếu xác thực lại thì 401 |
| S-SECA.8 | Quyền: khu vực theo role như admin_gui; máy theo `user_machine`; owner thấy mọi máy. Logic chép từ `admin_gui/auth.py` và `permissions.py`, không import | Bảng test role × khu vực × máy |
| S-SECA.9 | `idempotent`: cùng key trả kết quả cũ; cùng key khác body thì 409. Có `UNIQUE(created_by, request_key)` ở bảng của khối gọi | Ba ca |
| S-SECA.10 | `check_epoch`: epoch của form khác epoch hiện tại thì 409 "tải lại trang" | Test |

**Xong khi:** test đạt; cybersecurity duyệt.

### S-FM1 · Middleware FM1 phía server

- **Trách nhiệm:** mọi request ở `/api/agent/*` đi qua pipeline mục 4.4 trước khi tới module. Khối giữ:
  - `packet_claim`;
  - high-water theo kid;
  - cửa sổ giờ W;
  - banner giờ server nhảy.
- **Cung cấp:**
  - `fm1_encoding.py` (bản gốc; A-NET chép bản này);
  - `fm1_crypto.py`;
  - decorator `agent_route(ROUTE)` trao cho handler `(machine_id, body)`.
- **Cần:** C0.3, C0.2 (`ROUTE_POLICY`), `keys.lookup_kid`, `keys.server_kem_private` (C0.10), `epoch.current()`.
- **Stub:** M-KEY giả (một kid active, một kid revoked), handler module giả, S-EPOCH giả.

| ID | Việc | Kiểm |
|---|---|---|
| S-FM1.1 | `fm1_encoding.py`: LP, Tuple có nhãn, dựng và parse M | Vector C0.3; khác nhãn thì không ra cùng chuỗi byte |
| S-FM1.2 | `fm1_crypto.py`: verify Ed25519, HPKE open, tách `resp_key`, seal response AES-128-GCM với nonce ngẫu nhiên. Không log `resp_key` | Vector; 10.000 lần seal không lặp nonce (A1) |
| S-FM1.3 | Kiểm rẻ trước (A2): khung, `ver`, M, audience, kid còn active, `route_id` khớp đường dẫn và có trong `ROUTE_POLICY`, `issued_at` trong W và không thấp hơn high-water trừ W, `attempt_id` chưa claim | Gói kid đã thu hồi bị chặn mà số lần gọi verify = 0 |
| S-FM1.4 | Verify, rồi HPKE open | Đổi 1 byte trong M, enc hoặc ct thì bị từ chối |
| S-FM1.5 | Một transaction: claim `(kid, attempt_id)`, kiểm lại credential, so `server_epoch`, cập nhật high-water | Phát lại bị chặn; hai gói cùng `attempt_id` gửi đồng thời chỉ một gói qua |
| S-FM1.6 | Gọi handler với `machine_id` lấy từ credential, không lấy từ body (B9) | Body ghi `machine_id` khác vẫn dùng id của credential |
| S-FM1.7 | Lỗi trước bước claim: HTTP 4xx thân cố định, không mã hoá; route không có trong `ROUTE_POLICY` thì từ chối (B6) | Đổi route của gói thì bị từ chối |
| S-FM1.8 | Dọn `packet_claim` theo high-water từng máy, không theo giờ hệ thống | Đổi giờ hệ thống không làm dọn sớm |
| S-FM1.9 | Giờ (M2): so giờ tường với đồng hồ đơn điệu, nhảy thì bật banner; `CLOCK_CONFIRM_PATH` (cần xác thực lại) đặt lại high-water | Đổi giờ server: banner hiện |

**Xong khi:** test đạt; hacker chạy bộ tấn công trên khối với stub (phát lại, đổi route, đổi byte, kid cũ); cybersecurity duyệt.

## Module

### M-ACC · Tài khoản và quyền

- **Tham số đóng gói:** `{user, role, machine_ids[]}`.
- **Trách nhiệm:** A1 đăng nhập, A2 nhân viên và quyền, A3 gán máy.
- **Cung cấp:** `accounts.load_user`, `accounts.machines_of`; route `LOGIN_PATH`, `WHOAMI_PATH`, `MY_PASSWORD_PATH`, `USERS_PATH`, `USER_*_PATH`, `PERMISSIONS_*_PATH`; trang login, users.
- **Cần:** S-SECA, S-DB, UI-SHELL.
- **Bảng:** `admin_user` (mốc thu hồi BIGINT), `role_permission`, `user_machine`.
- **Stub:** S-SECA thật được, vì S-SECA test riêng đã xong; hoặc dùng stub cho phép mọi thứ.

| ID | Việc | Kiểm |
|---|---|---|
| M-ACC.1 | Đăng nhập: pbkdf2, `compare_digest`, 401 thân cố định | Sai thì 401; đúng thì có cookie |
| M-ACC.2 | Nhân viên: thêm, sửa, khoá, xoá; ba role, tám khu vực như admin_gui | So danh sách với `admin_gui/permissions.py` |
| M-ACC.3 | Gán máy cho nhân viên | Manager cửa hàng A không thấy máy B |
| M-ACC.4 | `manage.py create-owner` | Chạy trên DB rỗng tạo được owner |
| M-ACC.5 | Trang login, users chép từ admin_gui, đi qua UI-SHELL | Test tay |

### M-MAC · Máy và long-poll

- **Tham số đóng gói:** `{machine_id, kid, last_seen, epoch}`.
- **Trách nhiệm:**
  - danh sách máy, trạng thái online;
  - gán menu (N4);
  - hello;
  - long-poll, mỗi máy đúng một poll treo;
  - cờ nghi nhân bản.
- **Cung cấp:**
  - route `MACHINES_PATH`, `MACHINE_SAVE_PATH`, `MACHINE_DELETE_PATH`, `MACHINE_STATUS_PATH`;
  - handler agent `AGENT_HELLO_PATH`, `AGENT_COMMANDS_PATH`;
  - trang Máy.
- **Cần:** S-FM1 (`agent_route`), S-NET (`wake`), `commands.take_for_offer` (M-CMD), `menus.target_version` (M-MENU).
- **Bảng:** `machine` (`menu_id`, `last_seen`, `clone_flag_at`; không có `secret_enc`).
- **Stub:** M-CMD giả trả danh sách lệnh cố định; M-MENU giả trả số phiên bản; gọi handler trực tiếp, không qua FM1.

| ID | Việc | Kiểm |
|---|---|---|
| M-MAC.1 | Danh sách, tạo, sửa, xoá máy chưa ghép | Test route |
| M-MAC.2 | Gán menu cho máy (N4) | Đổi menu thì `target_version` đổi theo |
| M-MAC.3 | Hello: trả `target_menu_version`, `server_epoch`, `server_time` | Test handler |
| M-MAC.4 | Long-poll: `wait` tối đa 25 s; trả lệnh và bản menu đích; `wake` thì trả ngay | Treo, gọi `wake.notify`: trả ngay |
| M-MAC.5 | Mỗi máy một poll: poll mới thay poll cũ; hai poll cùng khoá từ hai IP khác nhau thì bật cờ nhân bản | Giả hai IP |
| M-MAC.6 | `last_seen`; online khi không quá ba chu kỳ chờ | Trang Máy hiện đúng |
| M-MAC.7 | Trang Máy: danh sách, trạng thái, menu đang gán, bản đã áp, món bị loại, tồn kho đệm (đọc từ M-PUB, M-ING) | Test tay |

### M-KEY · Khoá và ghép máy

- **Tham số đóng gói:** `{kid, alg, pubkey, status}`.
- **Trách nhiệm:**
  - khoá KEM server (file 0600);
  - credential máy;
  - mã ghép một lần;
  - trust bundle;
  - enroll;
  - thu hồi, `revoked.list`.
- **Cung cấp:**
  - `keys.lookup_kid`, `keys.server_kem_private`, `keys.reapply_revoked`;
  - route `MACHINE_ENROLL_CODE_PATH`, `MACHINE_REVOKE_PATH`;
  - handler `AGENT_TRUST_PATH` (chế độ `trust`), `AGENT_ENROLL_PATH` (chế độ `enroll`);
  - `manage.py make-server-key`.
- **Cần:** S-FM1, S-SECA (`require_stepup`), `commands.cancel_for_revoke` (M-CMD).
- **Bảng:** `server_key`, `machine_credential`, `enrollment_code`.
- **Stub:** M-CMD giả; gói enroll dựng bằng thư viện của S-FM1.

| ID | Việc | Kiểm |
|---|---|---|
| M-KEY.1 | Khoá KEM X25519 trong file 0600; `server_key` chỉ giữ kid, khoá công khai, trạng thái hiện tại/kế tiếp; hướng dẫn chép bản offline ra USB | Sai quyền file thì không khởi động |
| M-KEY.2 | Mã ghép ≥ 80 bit base32; chỉ lưu verifier và khoá MAC dẫn xuất; hạn 10 phút, 5 lần thử sai; cần xác thực lại | Sai 5 lần thì khoá; hết hạn thì từ chối |
| M-KEY.3 | Trust bundle: CA, khoá KEM, audience, epoch, HMAC `fm1-bundle` | Đổi 1 byte thì HMAC sai |
| M-KEY.4 | Enroll: kid `enroll`, chữ ký bằng khoá mới, `proof = HMAC(khoá dẫn từ mã, Tuple(pubkey, machine_id, install_uuid))`; tiêu mã cùng transaction với tạo credential | Proof sai thì từ chối; hai enroll đồng thời cùng mã chỉ một thành công |
| M-KEY.5 | Thu hồi: credential thành revoked, ghi thêm `revoked.list`, gọi `commands.cancel_for_revoke` | Test |
| M-KEY.6 | Gói của kid đã thu hồi: response seal status `revoked`, tối đa một lần mỗi phút mỗi kid; ngoài khoảng đó 4xx thân cố định | Gửi 100 gói trong một phút: chỉ một gói được seal |
| M-KEY.7 | Hiện vân tay khoá máy trên trang Máy | Test tay |

### M-CAT · Thư viện món

- **Tham số đóng gói:** `{sku 1001–1999, drink_name, image}`, `recipe[{ingredient_id 1–24, gram}]`.
- **Trách nhiệm:**
  - món, công thức, ảnh, media;
  - sổ cấp id nguyên liệu (K4);
  - thùng rác thư viện (N6 phía server);
  - nhập dữ liệu ban đầu (Q7).
- **Cung cấp:**
  - `catalogue.drinks_for(menu_id)` cho M-MENU dựng snapshot;
  - `media.path_of(sha256)` cho M-PUB;
  - route `EDITOR_PATH`, `RECIPE_PATH`, `IMAGES_PATH`, `IMAGE_UPLOAD_PATH`, `MEDIA_LIST_PATH`, `MEDIA_UPLOAD_PATH`, `INGREDIENT_REGISTRY_PATH`, `DELETE_PATH`, `RESTORE_PATH`, `PURGE_PATH`, `BIN_PATH`;
  - trang recipe-editor, bin.
- **Cần:** S-SECA, S-DB, UI-SHELL.
- **Bảng:** `glass`, `drink_type`, `category`, `drink` (bỏ `price`, `available`, `featured`, `in_stock`), `recipe` (`ingredient_id` không khoá ngoại, có `expected_name`, `expected_data_type`), `recipe_action`, `media_file`, `ingredient_registry`.

| ID | Việc | Kiểm |
|---|---|---|
| M-CAT.1 | SKU cấp toàn server, không bao giờ cấp lại, kể cả khi xoá hẳn | Xoá hẳn 1005 rồi thêm món: không nhận 1005 |
| M-CAT.2 | Công thức trỏ id trong sổ chung | Id không có trong sổ thì 400 |
| M-CAT.3 | Sổ id nguyên liệu: một tên một id, 1–24 (`qrproto/constants.py:53`); seed id 1–13 theo `database.sql:1220-1239` | Cấp quá 24 thì từ chối; seed khớp file nguồn |
| M-CAT.4 | Ảnh và media lưu theo sha256, ghi size, có trần kích thước | Trùng chỉ lưu một bản; quá trần thì 413 |
| M-CAT.5 | Thùng rác: xoá mềm, khôi phục, xoá hẳn | Như admin_gui |
| M-CAT.6 | ⏸ Q7. `manage.py import-machine-db`: nhập món, công thức, ảnh, tài khoản từ dump DB của một máy. Gặp xung đột (cùng SKU khác món, cùng id khác tên) thì báo, không tự gộp | Chạy trên dump thử |
| M-CAT.7 | Trang recipe-editor, bin chép từ admin_gui | Test tay |

### M-MENU · Menu

- **Tham số đóng gói:** `{menu_id, sku, price, available}`, `row_version`. Lưu là áp ngay.
- **Trách nhiệm:**
  - menu và mục menu (N2);
  - cấu hình trang chủ;
  - sao chép và sửa hàng loạt (N3);
  - dựng snapshot và tạo `menu_version` trong cùng transaction với mỗi lần lưu.
- **Cung cấp:**
  - `menus.target_version(machine_id)`, `menus.snapshot(version)`;
  - route `MENU_PATH`, `PRICE_PATH`, `AVAILABLE_PATH`, `FEATURED_PATH`, `FEATURED_CONFIG_PATH`, `BESTSELLER_CONFIG_PATH`, `LAYOUT_PATH`, `MENU_COPY_PATH`, `MENU_BULK_PATH`;
  - trang menu, home.
- **Cần:** S-SECA (`require`, `idempotent`, `check_epoch`), `catalogue.drinks_for` (M-CAT), `wake.notify` (S-NET), C0.5.
- **Bảng:** `menu`, `menu_item`, `menu_item_category`, `menu_setting`, `menu_version`.
- **Stub:** M-CAT giả trả danh sách món cố định; `wake` giả ghi lại lần gọi.

| ID | Việc | Kiểm |
|---|---|---|
| M-MENU.1 | Giá, bật/tắt, featured theo `menu_id`; mỗi request mang `row_version`, `request_key`, `server_epoch` | Người lưu sau nhận 409 |
| M-MENU.2 | Featured, bestseller, layout theo menu | Như admin_gui |
| M-MENU.3 | Một transaction: ghi mục, tăng `row_version`, dựng snapshot theo C0.5, tạo `menu_version`. Commit xong mới gọi `wake.notify` cho các máy dùng menu đó | Lỗi giữa chừng không để `menu_version` mồ côi; dựng hai lần ra cùng sha256 |
| M-MENU.4 | Quyền menu dùng chung: chỉ owner, hoặc người quản lý **mọi** máy đang dùng menu đó | Manager chỉ có máy A không sửa được menu A+B |
| M-MENU.5 | Sao chép menu; sửa hàng loạt một món trên nhiều menu, mỗi menu một phiên bản mới, quyền kiểm theo từng menu | Test |
| M-MENU.6 | Trang menu, home chép từ admin_gui | Test tay |

### M-PUB · Phát menu

- **Tham số đóng gói:** `{server_epoch, version, sha256}`, `media[{sha256, size}]`.
- **Trách nhiệm:** đưa snapshot và media cho máy; nhận ack.
- **Cung cấp:** handler `AGENT_MENU_PATH`, `AGENT_MENU_ACK_PATH` (`fm1`), `AGENT_MEDIA_PATH = /api/agent/media/{sha256}` (`tls_only`); `pub.applied_of(machine_id)` cho trang Máy.
- **Cần:** S-FM1, `menus.snapshot` (M-MENU), `media.path_of` (M-CAT).
- **Bảng:** `machine_menu_apply`.
- **Stub:** M-MENU giả trả snapshot mẫu đúng C0.5; gọi handler trực tiếp.

| ID | Việc | Kiểm |
|---|---|---|
| M-PUB.1 | Trả snapshot theo `since` | Đúng hợp đồng |
| M-PUB.2 | Media theo sha256, chỉ qua TLS | sha256 lạ thì 404 |
| M-PUB.3 | Ack: `version`, `ok`, `excluded[]` (sku, reason, ingredient_id) | Ghi `machine_menu_apply` |

### M-ING · Nhận dữ liệu máy

- **Tham số đóng gói:** `{payload_hash}`, `{error_id}`, `stock[]`. `machine_id` luôn lấy từ credential.
- **Trách nhiệm:** nhận đơn, vé (D1), lỗi (D2), tồn kho (K3) và giữ bản sao. Khối này là nơi duy nhất ghi `sale`, `fault`, `machine_ingredient_cache`.
- **Cung cấp:** handler `AGENT_ORDERS_PATH`, `AGENT_ERRORS_PATH`, `AGENT_STOCK_PATH`; `ingest.upsert_ticket(machine_id, row)` cho M-CMD; `ingest.delete_faults(machine_id, ids)`; `ingest.stock_of(machine_id)`.
- **Cần:** S-FM1, C0.4.
- **Bảng:** `sale`, `fault`, `machine_ingredient_cache`.

| ID | Việc | Kiểm |
|---|---|---|
| M-ING.1 | Upsert `sale` theo `(machine_id, payload_hash)`, chỉ đè khi `updated_at` mới hơn hoặc bằng; không nhận trường `payload` | Gửi trùng 3 lần chỉ 1 dòng |
| M-ING.2 | `fault` khoá `(machine_id, install_uuid, error_id)` | Cài lại DB máy không đè lỗi cũ |
| M-ING.3 | `machine_ingredient_cache` kèm `reported_at`; danh sách món hết kèm lý do | Test |

### M-REP · Báo cáo

- **Tham số đóng gói:** `{machine | all, from, to}`.
- **Trách nhiệm:** trang Báo cáo, Vé, Lỗi (D3). Chỉ đọc bản sao.
- **Cung cấp:** route `REPORT_PATH`, `ORDERS_PATH`, `TICKETS_PATH`, `ERRORS_PATH`; trang report, tickets, errors.
- **Cần:** S-SECA, đọc bảng của M-ING.
- **Stub:** dữ liệu `sale`, `fault` mẫu.

| ID | Việc | Kiểm |
|---|---|---|
| M-REP.1 | Lọc một máy hoặc `all`; gộp theo SKU | So với dữ liệu mẫu |
| M-REP.2 | Bảng rỗng thì hiện "chưa có dữ liệu" | Test |
| M-REP.3 | Lý do lỗi từ máy hiện bằng `setText` (B10) | Chuỗi `<script>` hiện như chữ |

### M-CMD · Hàng đợi lệnh

- **Tham số đóng gói:** `{command_id 16B, fingerprint, ttl_ms}`. Trạng thái: queued → offered → done | unknown.
- **Trách nhiệm:**
  - vòng đời lệnh L0;
  - nhận kết quả;
  - nút Kiểm tra;
  - mọi thao tác quản trị sinh lệnh: nguyên liệu K1, K2; vé và lỗi L1; in lại L2; order-mode L3; màn hình L4.
- **Cung cấp:**
  - `commands.take_for_offer`, `commands.cancel_for_revoke`, `commands.mark_unknown_all`;
  - handler `AGENT_RESULTS_PATH`;
  - route `INGREDIENTS_PATH`, `INGREDIENT_SAVE_PATH`, `INGREDIENT_DELETE_PATH`, `INGREDIENT_REFILL_PATH`, `INGREDIENT_REFILL_ALL_PATH`, `TICKET_STATUS_PATH`, `ERRORS_DELETE_PATH`, `TICKET_REPRINT_PATH`, `ORDER_MODE_PATH`, `DISPLAY_APPLY_PATH`, `DISPLAY_KEEP_PATH`, `MACHINE_COMMAND_PATH`, `MACHINE_COMMAND_CHECK_PATH`;
  - trang ingredients, refill, mode, display, nút trên trang tickets và errors.
- **Cần:** S-FM1, S-SECA, `wake.notify`, `ingest.upsert_ticket`, `ingest.delete_faults`, `ingest.stock_of` (M-ING), C0.6.
- **Bảng:** `machine_command`.
- **Stub:** M-ING giả; máy giả trả kết quả theo kịch bản (xong, lỗi, mất response, trễ).

| ID | Việc | Kiểm |
|---|---|---|
| M-CMD.1 | `machine_command`: `command_id` BINARY(16) ngẫu nhiên, `args_bytes`, fingerprint `fm1-cmd`, state, `intent_deadline`, `server_epoch`, `request_key` UNIQUE theo người tạo, `body_fingerprint`, `result_json` | Migration áp được |
| M-CMD.2 | Tạo lệnh: commit trước, rồi mới `wake.notify`. Epoch khác hoặc máy offline thì 409, không tạo lệnh | Kill ngay sau commit: lệnh còn |
| M-CMD.3 | `take_for_offer`: chỉ đưa lệnh còn hạn lớn hơn thời gian poll cộng biên; đánh dấu `offered` ngay trước khi seal | Test hạn sát |
| M-CMD.4 | Mất response: giao lại cùng id trong hạn. Hết hạn mà chưa có kết quả, hoặc epoch đổi: `unknown`. Không bao giờ tự gửi lại bằng id mới (G4) | Cắt response ba lần liên tiếp |
| M-CMD.5 | Nhận kết quả chỉ khi lệnh thuộc đúng máy, đang `offered` hoặc `unknown`, fingerprint khớp (B9) | Máy A gửi kết quả lệnh máy B thì bị bỏ |
| M-CMD.6 | Kiểm tra: gửi `ledger.query`; máy không có trong ledger thì `expired` | Test |
| M-CMD.7 | K1: `ingredients.read` hạn 5 s; quá hạn hoặc offline thì trả bản đệm từ `ingest.stock_of`, chỉ đọc | Test |
| M-CMD.8 | K2: refill, refill-all, save, delete, hạn 30 s; trang hiện thành công / lỗi / chưa rõ, không báo "thất bại" khi chưa biết | Bấm đúp ra một lệnh |
| M-CMD.9 | L1: `ticket.set_status`, `error.delete`; kết quả cập nhật bản sao qua M-ING. ⏸ Q3: chuyển vé đã dùng về chưa dùng cần xác thực lại | Test |
| M-CMD.10 | L2 `ticket.reprint` (2 phút), L3 `order_mode.set` (30 s), L4 `display.apply` / `display.keep` (10 s) | Test với máy giả |
| M-CMD.11 | Trang ingredients, refill, mode, display chép từ admin_gui; nút khoá khi máy offline | Test tay |

## Cắt ngang

### S-EPOCH · Khôi phục DB server

- **Trách nhiệm:**
  - giữ `server_epoch` ở bảng và ở file ngoài backup;
  - phát hiện khôi phục;
  - kéo các hệ quả;
  - đối soát;
  - `restore.sh`.
- **Cung cấp:** `epoch.current()`, `epoch.check()` (S-FM1 gọi trong transaction claim).
- **Cần:** `commands.mark_unknown_all` (M-CMD), `session.rotate_key` (S-SECA), `keys.reapply_revoked` (M-KEY).
- **Bảng:** `server_state`. File `/var/lib/flexmix-server/epoch`.
- **Stub:** ba khối kia giả, ghi lại lần gọi.

| ID | Việc | Kiểm |
|---|---|---|
| S-EPOCH.1 | Epoch 16 byte ở bảng và file; so khi khởi động và trong transaction claim | Khôi phục khi đang chạy: request kế tiếp thấy lệch |
| S-EPOCH.2 | Lệch hoặc thiếu file: sinh epoch mới, gọi ba hệ quả, bật banner | Mỗi hệ quả được gọi đúng một lần |
| S-EPOCH.3 | ⏸ Q4, Q10. Nhận ledger N giờ từ máy; giải lệnh unknown; liệt kê lệnh máy đã chạy mà server không có | Test với ledger mẫu |
| S-EPOCH.4 | `restore.sh`: dừng service, nạp DB, sinh epoch mới, khởi động | Chạy trên server thử |

**Giới hạn đã biết:** chụp và khôi phục cả ổ đĩa thì không phát hiện được.
