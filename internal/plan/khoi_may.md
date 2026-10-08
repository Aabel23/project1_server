# Khối phía máy

- **Trạng thái:** CHƯA THỰC HIỆN. Mọi khối ở đây ⏸ Q6: chờ user chọn nhánh `version1.0` hay `version1.1`.
- **Số dòng:** lấy theo `version1.0`. Nếu Q6 chọn `version1.1` thì đối chiếu lại số dòng trước khi làm.
- **Nơi đặt code:**
  - agent và helper nằm trong repo máy;
  - agent cài ra `/opt/flexmix-agent`;
  - test ở `tests/agent/<khối>/`, `tests/helper/`.
- **Nguyên tắc:** máy vẫn bán như cũ trong suốt quá trình. admin_gui còn trên máy tới X5.

## Nền của máy

### A-POS · Màn bán hàng đọc order-mode cục bộ

- **Trách nhiệm:** màn bán hàng không còn cần route của admin_gui để đọc order-mode.
- **Cần:** không.

| ID | Việc | Kiểm |
|---|---|---|
| A-POS.1 | Thêm route đọc `configuration/order_mode.py` trong `store_gui/serve.py`, chỉ trên loopback như hiện nay | `curl` trên Pi trả đúng `printQR`, `runDirect` |
| A-POS.2 | Đổi `ORDER_MODE_URL` ở `store_gui/drinks-pos.js:1549` sang route mới | Đổi order-mode bằng admin_gui cũ, POS thấy giá trị mới |

**Phạm vi:** chưa xoá import admin_gui (`store_gui/serve.py:96`, `:435`, `:569-592`). Việc đó làm ở X5.

### A-HOST · User, thư mục, service

- **Trách nhiệm:** chỗ chạy cho agent, tách khỏi user kiosk (B7).
- **Cung cấp:** service `flexmix-agent`, khung `agent/main.py` (đọc cấu hình, chờ giờ, vòng chính rỗng), phase cài trong `install.sh`.
- **Cần:** G0 (biết phiên bản `cryptography` cần ghim).

| ID | Việc | Kiểm |
|---|---|---|
| A-HOST.1 | User hệ thống `flexmix-agent`, không có shell | `id flexmix-agent` |
| A-HOST.2 | `/opt/flexmix-agent` root:root 755, venv riêng; `vendor/admin_functions` chép từ commit đã ghim; không import gì từ `/home/flexxource` | `sudo -u flexxource touch /opt/flexmix-agent/x` thất bại |
| A-HOST.3 | `/var/lib/flexmix-agent` thuộc `flexmix-agent`, 0700 | `sudo -u flexxource ls` thất bại |
| A-HOST.4 | Ghim `cryptography` kèm hash trong venv agent; không đụng thư viện của tiến trình bán hàng (`install.sh:223`) | `pip install --require-hashes`; tiến trình bán hàng import như cũ |
| A-HOST.5 | Unit `flexmix-agent.service`, tự khởi động lại | Kill thì tự lên |
| A-HOST.6 | Thiếu `QRPROTO_MACHINE_ID` thì dừng, không mặc định về 1 | Service báo lỗi rõ |
| A-HOST.7 | NTP: giữ `systemd-timesyncd` và bước chờ đồng bộ (`install.sh:536-563`), đổi `NTP=` về server; agent chờ đồng bộ xong mới gửi | Tắt chrony server: agent chờ, máy vẫn bán |
| A-HOST.8 | `install.sh`: phase cài agent và helper; hỏi URL `https://…`, `machine_id`. Chạy lại không đổi khoá. Bước `admin_gui.auth` giữ tới X5 | Cài trên Pi sạch; chạy hai lần không đổi `/var/lib/flexmix-agent` |

### A-DB · Bảng agent trên MySQL máy

- **Trách nhiệm:** chỗ ghi bền cho agent; tài khoản MySQL riêng.
- **Cần:** C0.6 (trạng thái ledger), C0.8 (ai ghi cột nào).

| ID | Việc | Kiểm |
|---|---|---|
| A-DB.1 | `database/migrations/0003_agent.sql`: `agent_ledger` (command_id, fingerprint, kind, state, result_json, acked, server_epoch) và `agent_state` (kid, server_epoch, applied, con trỏ, hash tồn kho, install_uuid) | Chạy qua `database/migrate.py` hai lần, lần hai không đổi gì |
| A-DB.2 | Tài khoản MySQL của agent, cấp quyền theo cột để không đọc được `order_ticket.payload` | `SELECT payload` bị từ chối |
| A-DB.3 | `innodb_flush_log_at_trx_commit=1`, `sync_binlog=1` | `SHOW VARIABLES` |

### H-LOCAL · Helper kiosk

- **Trách nhiệm:** việc cần quyền user kiosk: màn hình, máy in, file order-mode, dựng `menu-data.js`. Chỉ nhận tập lệnh cố định từ đúng uid của agent.
- **Cung cấp:** unix socket, ngữ pháp C0.7.
- **Cần:** C0.7.
- **Stub:** không cần. Test gọi socket trực tiếp.

| ID | Việc | Kiểm |
|---|---|---|
| H-LOCAL.1 | Service `User=flexxource`, file code thuộc root; unix socket | Socket đúng quyền |
| H-LOCAL.2 | `SO_PEERCRED`: chỉ nhận uid của `flexmix-agent` | uid khác bị đóng ngay |
| H-LOCAL.3 | Parse chặt theo C0.7; mode phải nằm trong danh sách màn hình hỗ trợ | Fuzz: mọi chuỗi ngoài ngữ pháp bị từ chối |
| H-LOCAL.4 | `display apply/keep/revert/status`: chuyển logic từ `admin_gui/serve.py:3219-3337`; nhớ mode cũ, tự quay về sau 20 s kể cả khi agent chết; `keep` lưu để sống qua reboot | Trên Pi: apply, kill agent, 20 s sau về mode cũ |
| H-LOCAL.5 | `order-mode set`: ghi `configuration/order_mode.py` | A-POS đọc được giá trị mới |
| H-LOCAL.6 | `print <hex64>`: in lại nhãn | In được trên máy in thật |
| H-LOCAL.7 | `menu publish`: gọi `store_gui/sync_menu.py:893` `publish_menu()` | `menu-data.js` được dựng lại |

admin_gui vẫn giữ cơ chế thử màn hình riêng của nó tới X5. Chỉ helper được agent gọi.

## Kênh

### A-NET · Kênh HTTPS và FM1 phía máy

- **Trách nhiệm:**
  - mọi gói từ agent lên server;
  - mở response;
  - lùi khi lỗi;
  - vòng long-poll và hello;
  - ghép máy phía máy (M1);
  - xử lý thông báo thu hồi.
- **Cung cấp:** `net.call(ROUTE, body)` trả `(status, body)` đã mở; vòng chính giao lệnh cho A-RUN và bản menu đích cho A-APPLY.
- **Cần:** C0.3, C0.4; `fm1_encoding.py` chép từ S-FM1 kèm commit nguồn.
- **Stub:** server giả dùng thư viện S-FM1 để mở gói và seal response; có chế độ trả 401 giả, cắt mạng, response sai.

| ID | Việc | Kiểm |
|---|---|---|
| A-NET.1 | Bản chép `fm1_encoding.py`; test so sha256 với bản gốc ở repo server | Hai bản lệch thì test đỏ |
| A-NET.2 | Seal request: `attempt_id` và `resp_key` 16 byte, HPKE tới khoá KEM đã ghim, ký Ed25519 | Vector C0.3 |
| A-NET.3 | Mở response chỉ bằng `resp_key` của attempt đang chờ; kiểm `attempt_id`, hạn BOOTTIME; xoá `resp_key` sau khi mở | Response của attempt khác không mở được |
| A-NET.4 | HTTPS chỉ tin CA đã ghim; không bao giờ dùng `http://` | Cert lạ bị từ chối |
| A-NET.5 | Lỗi mạng, 4xx thân cố định, response không mở được: lùi 1, 2, 5, 10, 30 s rồi attempt mới; không dừng hẳn (B5) | 401 giả chỉ làm lùi |
| A-NET.6 | Chỉ status `revoked` đã xác thực mới làm agent dừng gửi; ghi trạng thái, máy vẫn bán | Test |
| A-NET.7 | Ghép máy: nhận trust bundle và kiểm HMAC; sinh khoá Ed25519 0600; ghi `trust.json`; enroll với kid `enroll` và proof; hiện vân tay. `install.sh` hỏi mã ghép | Bundle sai 1 byte thì dừng |
| A-NET.8 | Vòng chính: hello, rồi long-poll liên tục; giao lệnh cho A-RUN, bản đích cho A-APPLY; thấy `server_epoch` đổi thì báo A-RUN và A-UP | Test với server giả |

**Xong khi:** test đạt; hacker và cybersecurity duyệt.

## Module của máy

### A-APPLY · Áp menu

- **Tham số đóng gói:** `{epoch, version, sha256}`. Món thiếu nguyên liệu bị bỏ.
- **Trách nhiệm:** N5 áp snapshot, N6 ẩn món 24 giờ.
- **Cần:**
  - `net.call` (A-NET);
  - C0.5;
  - H-LOCAL `menu publish`;
  - `vendor/admin_functions`.
- **Stub:** snapshot mẫu đúng C0.5, server media giả, helper giả.

| ID | Việc | Kiểm |
|---|---|---|
| A-APPLY.1 | Tải media thiếu theo sha256; dừng khi vượt `size`; thư mục tạm có trần (B13) | File lớn hơn size thì dừng, không ghi |
| A-APPLY.2 | Kiểm nguyên liệu lúc áp: id không có trên máy hoặc khác `expected_name` / `expected_data_type` thì bỏ toàn bộ dòng công thức của món; trigger `drink.in_stock` tự đặt hết hàng (`database.sql:1082-1180`) | Món thiếu nguyên liệu hiện "hết" |
| A-APPLY.3 | Một transaction: đổi tên tạm, upsert món, công thức, danh mục, `store_setting`, ghi phần applied của `agent_state` | Kill giữa transaction: giữ bản cũ nguyên vẹn; hai món đổi tên chéo nhau vẫn áp được |
| A-APPLY.4 | Commit xong thì `menu publish`, rồi ack kèm món bị loại | POS thấy file mới |
| A-APPLY.5 | Món bị bỏ khỏi menu: `available=0`, giữ công thức 24 giờ rồi mới `deleted_at`; lịch sống qua khởi động lại | Nhãn in trước khi đổi menu vẫn pha được trong 24 giờ |

### A-STOCK · Báo tồn kho

- **Tham số đóng gói:** `{stock[], món hết[]}`. Gửi khi hash đổi.
- **Trách nhiệm:** K3.

| ID | Việc | Kiểm |
|---|---|---|
| A-STOCK.1 | Hash bảng `ingredient` hoặc trạng thái món đổi thì gửi `stock[]` và `out_of_stock[]` (sku, reason, ingredient_id) | Pha một ly: server giả nhận tồn mới |
| A-STOCK.2 | Lưu hash đã gửi vào phần của mình trong `agent_state` | Không đổi thì không gửi |

### A-UP · Gửi đơn và lỗi

- **Tham số đóng gói:** con trỏ, outbox; `install_uuid`, `error_id`.
- **Trách nhiệm:** D1, D2; đặt lại con trỏ khi epoch đổi (M6).

| ID | Việc | Kiểm |
|---|---|---|
| A-UP.1 | Đơn: mỗi 10 s hoặc khi có vé mới; đọc `updated_at >=` con trỏ, sắp theo `updated_at` rồi `serial`, tối đa 200 dòng; không gửi `payload` | Có chồng lấn, không sót; body không có `payload` |
| A-UP.2 | Nhận 200 thì lưu con trỏ; lỗi thì giữ con trỏ cũ | Cắt mạng giữa chừng không mất vé |
| A-UP.3 | Lỗi: `error_id` lớn hơn con trỏ, kèm `install_uuid` | Test |
| A-UP.4 | Epoch đổi: đặt lại con trỏ và gửi lại | Server giả không thấy dòng trùng nhờ upsert |

### A-RUN · Chạy lệnh

- **Tham số đóng gói:** `agent_ledger`. Claim trước khi chạy.
- **Trách nhiệm:**
  - ledger và outbox;
  - chạy các loại lệnh K1, K2, L1–L4;
  - trả lời `ledger.query`;
  - gửi lại ledger khi epoch đổi (M6).
- **Cần:**
  - `net.call` (A-NET);
  - C0.6;
  - H-LOCAL;
  - `vendor/admin_functions`.
- **Stub:** lệnh mẫu từ C0.6; helper giả; server giả nhận kết quả.

| ID | Việc | Kiểm |
|---|---|---|
| A-RUN.1 | Lệnh có tác dụng lên DB (nạp kho, sửa vé, xoá lỗi): ghi ledger `done` trong cùng transaction với tác dụng | Kill giữa chừng: cả hai cùng còn hoặc cùng mất |
| A-RUN.2 | Lệnh không đụng DB (in lại, màn hình, order-mode): ghi `claimed` trước rồi mới chạy | Crash sau claimed: không chạy lại, báo unknown |
| A-RUN.3 | Cùng `command_id` khác fingerprint thì từ chối | Test |
| A-RUN.4 | Hạn đo bằng BOOTTIME | Đổi giờ tường: hạn không đổi |
| A-RUN.5 | Outbox: kết quả nằm trong ledger tới khi `AGENT_RESULTS_PATH` nhận được response mở được | Cắt mạng sau khi chạy: kết quả lên khi có mạng |
| A-RUN.6 | Các loại lệnh: `ingredients.read`, `ledger.query`, `ingredient.refill/save/delete`, `ticket.set_status`, `error.delete`, `ticket.reprint`, `order_mode.set`, `display.apply/keep` | Một test mỗi loại |
| A-RUN.7 | Dọn ledger theo id sau thời gian giữ (30 ngày), không dọn dòng chưa đối soát | Test |
| A-RUN.8 | ⏸ Q4, Q10. Epoch đổi: gửi lại ledger N giờ gần nhất, kể cả dòng đã ack, rồi hello với menu đang áp | Server giả nhận đủ |
