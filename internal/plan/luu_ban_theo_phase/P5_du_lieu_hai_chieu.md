# P5 · Dữ liệu hai chiều

- **Trạng thái:** CHƯA THỰC HIỆN.
- **Luồng thiết kế:** N5, N6 (phía máy), D1, D2, D3 (có dữ liệu), K3, luồng chính ở mục 3. Lỗi kiểm định: B13.

## Mục tiêu

- Menu đi từ server xuống màn bán hàng.
- Đơn, vé, lỗi và tồn kho đi từ máy lên server.
- Cả hai chiều đều không cần lệnh: chiều xuống do máy kéo, chiều lên do máy đẩy.

## Điều kiện vào

- P2 ✓, kể cả hợp đồng `menu_snapshot.md`.
- P4 ✓.

## Đầu ra

| Đầu ra | File |
|---|---|
| Route agent cho menu, media, ack, đơn, lỗi, tồn kho | `modules/agent_menu/`, `modules/agent_upload/` |
| Migration: `machine_menu_apply`, `machine_ingredient_cache` | `db/migrations/0004_sync.sql` |
| Agent áp menu | `agent/apply_menu.py` |
| Agent gửi đơn và lỗi | `agent/uploader.py` |
| Agent báo tồn kho | `agent/stock_report.py` |
| Test | `tests/p5/`, `tests/agent/` |

## Phase con

### P5.1 N5 · Server phát menu

| ID | Việc | Route | Kiểm |
|---|---|---|---|
| P5.1.1 | Trả snapshot theo `since`, kèm `server_epoch`, `version`, sha256, `media[]` (sha256, size) | `AGENT_MENU_PATH` (POST, FM1) | Snapshot đúng hợp đồng |
| P5.1.2 | Tải media theo sha256, chỉ qua TLS, ngoài FM1 | `AGENT_MEDIA_PATH = /api/agent/media/{sha256}` | sha256 lạ thì 404 |
| P5.1.3 | Nhận ack gồm `version`, `ok`, `excluded[]` (sku, reason, ingredient_id); ghi `machine_menu_apply`, `applied_menu_version` | `AGENT_MENU_ACK_PATH` | Trang Máy hiện bản đã áp và món bị loại |

### P5.2 N5 · Agent áp menu

Thứ tự theo `phuong_an_kien_truc.md` §4 "Agent áp snapshot":

| ID | Bước | Kiểm |
|---|---|---|
| P5.2.1 | Tải media còn thiếu theo sha256. Dừng khi vượt `size` ghi trong snapshot. Thư mục tạm có trần (B13) | Server trả file lớn hơn size thì agent dừng, không ghi |
| P5.2.2 | Kiểm nguyên liệu ngay lúc áp: món trỏ id không có trên máy, hoặc khác `expected_name` / `expected_data_type`, thì bỏ **toàn bộ** dòng công thức của món. Trigger `drink.in_stock` tự đặt hết hàng (`database.sql:1082-1180`) | Món thiếu nguyên liệu hiện "hết" trên POS |
| P5.2.3 | Một transaction: đổi tên tạm món bị đổi tên; upsert món, công thức, danh mục, `store_setting`; ghi `agent_state.applied` | Kill agent giữa transaction: DB máy giữ bản cũ nguyên vẹn |
| P5.2.4 | Commit xong thì nhờ helper chạy `menu publish`, dựng lại `menu-data.js` | POS poll thấy file mới |
| P5.2.5 | Gửi ack kèm danh sách món bị loại | Server nhận |

Dùng `vendor/admin_functions` (đã ghim ở P3.2.2) cho các thao tác DB, không viết SQL mới nếu hàm đã có.

### P5.3 N6 · Ẩn món trên máy

| ID | Việc | Kiểm |
|---|---|---|
| P5.3.1 | Món bị bỏ khỏi menu: đặt `available=0` và giữ công thức 24 giờ (thời gian sống của nhãn), rồi mới đặt `deleted_at` | Nhãn in trước khi đổi menu vẫn pha được trong 24 giờ |
| P5.3.2 | Việc đặt `deleted_at` chạy theo lịch trong agent; agent khởi động lại thì không mất lịch | Kill agent, mở lại, lịch vẫn chạy |

### P5.4 D1 · Gửi đơn và vé

| ID | Việc | Kiểm |
|---|---|---|
| P5.4.1 | Mỗi 10 s, hoặc ngay khi có vé mới: đọc `order_ticket` có `updated_at` từ con trỏ trở đi (`>=`), sắp theo `updated_at` rồi `serial`, tối đa 200 dòng | Có chồng lấn, không sót vé |
| P5.4.2 | Gửi: payload_hash, serial, drink_id, drink_name, price, note, status, các mốc thời gian, `updated_at`. Không gửi `payload` | Test: body không có trường `payload` |
| P5.4.3 | Server upsert `sale` theo `(machine_id, payload_hash)`, chỉ đè khi `updated_at` mới hơn hoặc bằng. `machine_id` lấy từ credential | Gửi trùng 3 lần chỉ có 1 dòng |
| P5.4.4 | Nhận 200 thì lưu con trỏ vào `agent_state`. Lỗi thì giữ con trỏ cũ | Cắt mạng giữa chừng: không mất vé |

### P5.5 D2 · Gửi lỗi

| ID | Việc | Kiểm |
|---|---|---|
| P5.5.1 | Gửi dòng `error_log` có `error_id` lớn hơn con trỏ, kèm `install_uuid` | |
| P5.5.2 | Server khoá theo `(machine_id, install_uuid, error_id)` | Cài lại DB máy, `error_id` đếm lại từ 1, không đè lỗi cũ |
| P5.5.3 | Lý do lỗi từ máy hiện bằng `textContent` trên trang Lỗi (B10) | Chuỗi `<script>` hiện ra như chữ |

### P5.6 K3 · Máy báo tồn kho và món hết

| ID | Việc | Kiểm |
|---|---|---|
| P5.6.1 | Khi hash bảng `ingredient` đổi, hoặc trạng thái món đổi: gửi `stock[]` và `out_of_stock[]` (sku, reason, ingredient_id) | Pha một ly, server nhận tồn mới |
| P5.6.2 | Server ghi `machine_ingredient_cache` kèm `reported_at`; trang Máy hiện "món hết, nguyên liệu dưới ngưỡng" kèm lý do | Hiện đúng hai loại lý do của K3 |

### P5.7 Luồng chính đầu–cuối (mục 3)

| ID | Kịch bản | Đạt khi |
|---|---|---|
| P5.7.1 | Đổi giá Peach Tea trong menu Quận 1 trên trình duyệt | Màn bán hàng của máy dùng menu đó hiện giá mới; máy dùng menu khác không đổi |
| P5.7.2 | Rút mạng máy, đổi giá, cắm lại | Trong lúc offline máy vẫn bán giá cũ; cắm lại thì áp giá mới |
| P5.7.3 | Bán 20 ly trên máy | Trang Báo cáo trên server có đủ 20 dòng, không trùng |
| P5.7.4 | Xem báo cáo `?machine=all` | Gộp đúng theo SKU |

## Cổng ra P5

- P5.7.1–P5.7.4 đạt trên Pi thử nối với server thật.
- `pytest tests/p5 tests/agent -q` đạt.
- Reviewer duyệt.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Đổi tên món làm vướng ràng buộc UNIQUE trong transaction | Đổi tên tạm trước (P5.2.3), có test riêng cho ca hai món đổi tên chéo nhau |
| `updated_at` chỉ chính xác tới giây làm sót vé | Quét `>=` có chồng lấn; upsert làm gửi trùng thành vô hại |
| Thẻ SD đầy vì media | Trần thư mục tạm và size trong snapshot (P5.2.1) |
