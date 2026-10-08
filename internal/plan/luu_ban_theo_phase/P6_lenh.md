# P6 · Lệnh xuống máy

- **Trạng thái:** CHƯA THỰC HIỆN.
- **Luồng thiết kế:** L0, K1, K2, L1, L2, L3, L4, phần còn lại của M3 và M5. Lỗi kiểm định: B2, B4, B9, B12, G4.

## Mục tiêu

Server gửi được lệnh xuống máy qua long-poll, và máy chạy mỗi lệnh tối đa một lần.

- Phân biệt rõ "chắc chắn chưa chạy" với "không biết đã chạy chưa".
- Mất response giữa chừng không bao giờ làm nạp kho hai lần.

## Điều kiện vào

- P5 ✓.
- Q3: có bắt nhập lại mật khẩu khi chuyển vé "đã dùng" về "chưa dùng" không. Chỉ chặn P6.4.

## Đầu ra

| Đầu ra | File |
|---|---|
| Migration `machine_command` | `db/migrations/0005_command.sql` |
| Hàng đợi và vòng đời lệnh phía server | `modules/commands/` |
| Ledger, outbox, chạy lệnh phía agent | `agent/ledger.py`, `agent/commands.py`, `agent/local_client.py` |
| Các trang nguyên liệu, nạp kho, vé, lỗi, mode, màn hình | `static/` |
| Test | `tests/p6/`, `tests/agent/` |

## Phase con

### P6.1 L0 · Vòng đời lệnh phía server

Trạng thái lấy theo sơ đồ L0: `queued`, `offered`, `done`, `failed`, `unknown`, `expired`, `cancelled`.

| ID | Việc | Kiểm |
|---|---|---|
| P6.1.1 | `machine_command`: `command_id` BINARY(16) ngẫu nhiên, `args_bytes`, fingerprint = `SHA256(Tuple("fm1-cmd", machine_id, kind, args_bytes))`, state, `intent_deadline`, `server_epoch`, `request_key` với `UNIQUE(created_by, request_key)`, `body_fingerprint`, `result_json` | Migration áp được |
| P6.1.2 | Tạo lệnh: commit vào DB trước, rồi mới đánh thức long-poll | Kill server ngay sau commit: lệnh vẫn còn, được giao khi lên lại |
| P6.1.3 | Chỉ đưa lệnh vào response khi hạn còn lại lớn hơn thời gian poll tối đa cộng biên. Đánh dấu `offered` ngay trước khi seal | Test hạn sát |
| P6.1.4 | Response mất: giao lại **cùng id** trong hạn. Hết hạn mà chưa có kết quả, hoặc epoch đổi: `unknown`. Không bao giờ tự gửi lại bằng id mới (G4) | Test cắt response ba lần liên tiếp |
| P6.1.5 | Nhận kết quả (`AGENT_RESULTS_PATH`, theo lô) chỉ khi lệnh thuộc đúng máy đã ký, đang `offered` hoặc `unknown`, và fingerprint khớp (B9) | Máy A gửi kết quả cho lệnh của máy B thì bị bỏ |
| P6.1.6 | Hoàn tất M5: khi thu hồi máy, lệnh `queued` thành `expired`, lệnh `offered` thành `unknown` | Test cùng P4.7 |
| P6.1.7 | Trạng thái lệnh cho trang quản trị | `MACHINE_COMMAND_PATH` |
| P6.1.8 | Nút "Kiểm tra" của lệnh `unknown`: gửi `ledger.query`; máy không có trong ledger thì lệnh thành `expired` | `MACHINE_COMMAND_CHECK_PATH` |

### P6.2 L0 · Ledger và outbox phía agent

| ID | Việc | Kiểm |
|---|---|---|
| P6.2.1 | Lệnh có tác dụng lên DB máy (nạp kho, sửa vé, xoá lỗi): ghi ledger `done` trong **cùng transaction** với tác dụng | Mất điện giữa chừng: cả hai cùng mất hoặc cùng còn (thử thật ở P8.2) |
| P6.2.2 | Lệnh không đụng DB (in lại, màn hình, order-mode): ghi `claimed` trước, rồi mới chạy | Crash sau khi claimed: không chạy lại, báo unknown |
| P6.2.3 | Cùng `command_id` mà khác fingerprint thì từ chối (conflict), không chạy | Test |
| P6.2.4 | Kiểm hạn lệnh bằng đồng hồ BOOTTIME, không dùng giờ tường | Đổi giờ tường máy: hạn không đổi |
| P6.2.5 | Outbox: kết quả nằm trong ledger tới khi `AGENT_RESULTS_PATH` nhận được response mở được; gửi lại nhiều lần vô hại | Cắt mạng sau khi chạy: kết quả lên khi có mạng lại |
| P6.2.6 | Dọn ledger theo id sau thời gian giữ (mặc định 30 ngày), không dọn dòng chưa đối soát | Test dọn |

### P6.3 K1, K2 · Nguyên liệu

| ID | Việc | Route, lệnh | Kiểm |
|---|---|---|---|
| P6.3.1 | K1: máy online thì gửi `ingredients.read`, hạn 5 s. Quá hạn hoặc offline thì trả bản đệm kèm `reported_at`, chỉ đọc | `INGREDIENTS_PATH` | Rút mạng máy: trang hiện bản đệm và nhãn "chỉ đọc" |
| P6.3.2 | K2: `request_key` do trang sinh bằng `crypto.randomUUID()` khi mở form; epoch khác hoặc máy offline thì 409 không tạo lệnh; key đã có lệnh thì trả trạng thái lệnh cũ | `INGREDIENT_REFILL_PATH`, `INGREDIENT_REFILL_ALL_PATH`, `INGREDIENT_SAVE_PATH`, `INGREDIENT_DELETE_PATH` | Bấm đúp ra một lệnh |
| P6.3.3 | Lệnh `ingredient.refill` (fill / set_gram / add_gram), `ingredient.save`, `ingredient.delete`; id nguyên liệu lấy từ sổ chung (P2.3); hạn 30 s | | Nạp đúng một lần |
| P6.3.4 | Trang hiện "thành công", "lỗi" hoặc "chưa rõ" kèm nút Kiểm tra; không bao giờ báo "thất bại" khi chưa biết | | Test tay |
| P6.3.5 | Gặp 401: trang bỏ mọi thao tác đang chờ, không tự gửi lại sau khi đăng nhập | | Test tay |

### P6.4 L1 · Vé và lỗi

| ID | Việc | Kiểm |
|---|---|---|
| P6.4.1 | `ticket.set_status` (payload_hash, status) qua `TICKET_STATUS_PATH`; máy đổi trong transaction kèm ledger; server upsert bản sao `sale` từ kết quả | Đổi trạng thái vé, cả máy và server đều đổi |
| P6.4.2 | `error.delete` (error_ids[]) qua `ERRORS_DELETE_PATH`; máy xoá xong thì server xoá bản sao | |
| P6.4.3 | ⏸ Q3: nếu user đồng ý thì chuyển vé "đã dùng" về "chưa dùng" phải xác thực lại | Thiếu xác thực lại thì 401 |

### P6.5 L2 · In lại vé

- **Lệnh:** `ticket.reprint` (payload_hash), hạn 2 phút, qua `TICKET_REPRINT_PATH`.
- **Cách chạy:** agent ghi ledger `claimed` rồi gửi helper `print <hex64>`.
- **Kiểm:** crash ngay sau claimed thì không in lần hai.

### P6.6 L3 · Order-mode

- **Lệnh:** `order_mode.set` (printQR, runDirect), hạn 30 s, qua `ORDER_MODE_PATH`.
- **Cách chạy:** agent nhờ helper ghi file `configuration/order_mode.py`.
- **Kiểm:** POS đọc giá trị mới qua route cục bộ ở P3.1.

### P6.7 L4 · Độ phân giải màn hình

| ID | Việc | Kiểm |
|---|---|---|
| P6.7.1 | `display.apply` (mode), hạn 10 s, qua `DISPLAY_APPLY_PATH`. Agent ghi claimed, gửi helper, báo "đang thử" | Trang hiện nút Giữ và đồng hồ |
| P6.7.2 | `display.keep` qua `DISPLAY_KEEP_PATH`. Helper huỷ đồng hồ, lưu mode để sống qua reboot | Reboot giữ mode mới |
| P6.7.3 | Hết 20 s không bấm Giữ: helper tự quay về mode cũ, kể cả khi agent đã chết | Kill agent sau apply: màn hình vẫn quay về |

### P6.8 Trang quản trị cho lệnh

- **Việc:**
  - Chép các trang `ingredients`, `refill`, `tickets`, `errors`, `mode`, `display` từ `version1.0/admin_gui/` sang `static/`.
  - Nút gửi lệnh bị khoá khi máy offline.
  - Dữ liệu đến từ máy hiện bằng `textContent`.
- **Kiểm:** `grep innerHTML static/`; test tay từng trang.

## Cổng ra P6

Tester chạy kịch bản "mất response giữa chừng" cho `ingredient.refill`:

1. Cắt kết nối sau khi máy chạy xong, trước khi server nhận kết quả.
2. Người dùng bấm lại.
3. Server giao lại cùng id.
4. Máy trả kết quả cũ.

Đạt khi tồn kho chỉ tăng đúng một lần.

Các điều kiện khác:

- P6.7.3 đạt trên Pi thật.
- `pytest tests/p6 tests/agent -q` đạt.
- Reviewer và cybersecurity duyệt.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Quá nhiều lệnh `unknown` phải đối soát tay | Giao lại cùng id trong hạn (P6.1.4); chỉ `unknown` khi hết hạn hoặc epoch đổi (G4) |
| Helper chết đúng lúc in | Ledger `claimed` trước khi in: thà mất một lần in còn hơn in hai nhãn dùng được |
