# Phương án kiến trúc server mẹ (sau hai vòng architect A/B)

Ngày: 2026-10-07. Trạng thái: **ĐỀ XUẤT, chờ user chốt** các mục ở §8.

Hồ sơ lịch sử: HTTP/HMAC/waitress và route ở đây không phải cấu hình hiện tại.
Đọc [bối cảnh mới](hieu_biet_server_me.md) và [plan](../../internal/plan/index.md)
để tiếp tục triển khai; giữ nội dung bên dưới làm căn cứ đối chiếu.

## 1. Hiện trạng version1.0 làm thay đổi thiết kế

- **Máy không mở cổng ra LAN.** `configuration/net_addresses.py:157-196` (`bind_hosts`) chỉ nghe loopback và tailnet.
- **Không xoá thẳng `admin_gui` được.**
  - `store_gui/serve.py:96` import `admin_gui.serve`; các dòng 435, 569-592 chuyển route qua đó.
  - `drinks-pos.js:1549` gọi `../api/order-mode` không cần đăng nhập.
  - Cần làm trước khi xoá: tách đọc order-mode ra một handler cục bộ, chuyển upload ảnh và media lên server.
- **Cơ chế thử độ phân giải (probation display)** nằm trong `admin_gui/serve.py:3219-3337`: một `threading.Timer` 20 giây. Phải chuyển sang agent.
- **QR mang `drink_id` (SKU 4 chữ số) và `ingredient_id`** (1–24, `qrproto/constants.py:53`). Seed ép id 1–13 giống nhau trên mọi máy (`database.sql:1220-1239`).
- **Lúc quét, máy đọc công thức hiện tại**, có lọc `deleted_at IS NULL` (`export_data.py:158,229`). Vé sống 24 giờ.
- **Nạp `add_gram` không idempotent** (`admin_functions/ingredients.py:354-365`).
- **`order_ticket.updated_at` đã có** từ migration 0002, kiểu `DATETIME` chính xác tới giây.
- **`main.py` gọi `os._exit`** khi bất kỳ thread nào chết.
- **`QRPROTO_MACHINE_ID`** lặng lẽ mặc định là 1 nếu không cấu hình.

## 2. Giao tiếp máy ↔ server

- **Máy chủ động mở mọi kết nối.** Agent là service systemd riêng, `flexmix-agent.service`, không chạy chung tiến trình bán hàng.
- **"Server gọi xuống" chạy bằng long-poll.**
  - Agent treo sẵn `GET /api/agent/commands?wait=25`.
  - Lệnh được commit vào `machine_command` trước, rồi mới đánh thức bằng `threading.Condition`. Server kiểm tra lại DB mỗi 1–2 giây làm dự phòng.
- **Lệnh và thời hạn:**
  - Máy offline (`last_seen` quá 3 chu kỳ): lệnh ghi nguyên liệu và lệnh phần cứng trả **409 ngay**.
  - Máy online: lệnh có `expires_at` ngắn (khoảng 10–30 giây) để giao lại được khi long-poll bị đứt.
- **Đọc nguyên liệu:**
  - Gửi lệnh `ingredients.read`, chờ khoảng 5 giây.
  - Quá hạn thì trả bản đệm `machine_ingredient_cache`, kèm `reported_at`, ở chế độ chỉ đọc.
  - Agent tự đẩy bản tồn kho lên mỗi khi hash bảng `ingredient` đổi.
- **Xác thực:**
  - HMAC-SHA256 trên chuỗi `method|path|ts|nonce|sha256(body)`, áp dụng cho cả request lẫn response.
  - Cửa sổ thời gian ±60–120 giây; nonce lưu ở bảng `agent_nonce`.
  - Secret 32 byte cho mỗi máy, server lưu `secret_enc` mã hoá bằng master key nằm trong env.
  - Cách này không mã hoá nội dung, nên vẫn bị nghe lén trên LAN.
- **Đăng ký máy:** `machine_id` = `QRPROTO_MACHINE_ID`. Một `hello` từ `install_uuid` lạ mà trùng `machine_id` đã có thì **từ chối**.

## 3. Chống trùng và gửi bù (mỗi bảng chỉ một nơi ghi)

- **Vé:** upsert theo `(machine_id, payload_hash)`.
  - Agent dùng con trỏ `(updated_at, serial)` và quét bằng `>=` có chồng lấn.
  - Server chỉ giữ bản sao; sửa trạng thái vé phải gửi lệnh `ticket.set_status` xuống máy.
- **Lỗi:** khoá `(machine_id, install_uuid, error_id)`.
- **Lệnh có tác dụng lên DB:** ghi `command_id` vào bảng `agent_command_done` **trong cùng transaction** với tác dụng của lệnh.
- **Lệnh không đụng DB** (in lại vé, display): ghi `command_id` trước rồi mới chạy, tức chạy tối đa một lần.

## 4. Quản lý nhiều menu

- **Thư viện món dùng chung.**
  - `drink` toàn hệ thống; SKU 1001–1999 cấp toàn server, không bao giờ cấp lại.
  - `menu` là thực thể riêng; `menu_item` có khoá `(menu_id, drink_id)` và giữ `price`, `available`, `featured`, `sort_order`.
  - Mỗi máy có đúng một `menu_id`.
  - Hai architect đã đồng ý điểm này sau vòng phản biện.
- **Công thức** trỏ nguyên liệu bằng `ingredient_id` cục bộ, kèm `expected_name` và `expected_data_type`.
  - Server giữ **sổ cấp id nguyên liệu** cho toàn đội máy (tối đa 24 id).
- **Phát hành:**
  - Bấm phát hành tạo `menu_version`: snapshot JSON bất biến, kèm sha256. Máy có `target_menu_version_id`.
  - Server cho xem trước theo bản đệm nguyên liệu.
  - Agent kiểm tra lại **ngay lúc áp**: món nào không khớp nguyên liệu thì bị loại, danh sách loại gửi lên trong ack.
- **Agent áp snapshot:**
  1. Tải media trước.
  2. Mở một transaction:
     - đổi tên tạm các món bị đổi tên;
     - upsert món, công thức, danh mục, `store_setting`;
     - ghi `applied_version`.
  3. Commit, gọi `publish_menu()`, rồi ack.
- **Món bị bỏ khỏi menu:** đặt `available=0` và giữ công thức **24 giờ**, sau đó mới đặt `deleted_at`. Như vậy vé đã in vẫn pha được.
- **Sửa đồng thời:** `menu.row_version` làm khoá lạc quan, người lưu sau nhận 409.
- **Quyền sửa menu dùng chung:** chỉ owner, hoặc user quản lý mọi máy đang dùng menu đó.

## 5. Schema DB server (`flexmix_server`)

- **Giữ:** `schema_migration`, `glass`, `drink_type`, `category`, `admin_user`, `role_permission`.
- **Sửa:**
  - `drink`: bỏ `price`, `available`, `featured`, `in_stock`.
  - `recipe`: `ingredient_id` không có khoá ngoại, thêm `expected_name` và `expected_data_type`.
  - `recipe_action`: giữ nguyên.
- **Thêm:**
  - `machine`, `user_machine`, `machine_command`, `agent_nonce`
  - `menu`, `menu_item`, `menu_item_category`, `menu_setting`, `menu_version`, `machine_menu_apply` (ghi applied / excluded / error)
  - `media_file`, `ingredient_registry`, `machine_ingredient_cache`
  - `sale`: bản sao vé, không lưu payload
  - `fault`: bản sao lỗi
- **Phía máy thêm:** `agent_command_done`, `agent_state`.

## 6. Stack

- **Python + Flask + waitress + mysql-connector + MySQL 8**, SQL viết tay, migration đánh số.
- Chạy **một tiến trình**; số thread của waitress ≥ số máy + 8.
- **Lý do không chọn các phương án khác:**
  - `http.server` thuần: phải tự viết router và middleware.
  - FastAPI: driver MySQL là đồng bộ, đội phải đổi cách viết code.

## 7. Việc phía máy

1. Tách order-mode, upload ảnh và upload media ra khỏi `admin_gui`.
2. Xoá `admin_gui/`.
3. Thêm agent và unit systemd riêng cho agent.
4. Chuyển cơ chế thử độ phân giải vào agent.
5. Sửa `install.sh`: bỏ bước `admin_gui.auth`, thay bằng nhập URL server và secret của máy.
6. Cấu hình bắt buộc `QRPROTO_MACHINE_ID`.

## 8. Chờ user chốt

1. ~~Giá theo máy~~ → **User chốt 2026-10-07: tách menu.** Máy cần giá khác thì dùng menu riêng. Không làm bảng `machine_item_override`. Công thức vẫn nằm ở thư viện món dùng chung; giá, bật/tắt và thứ tự nằm trong `menu_item`. Cần thêm "sao chép menu" và thao tác hàng loạt (đổi giá một món trên nhiều menu cùng lúc).
2. Máy thiếu nguyên liệu → **đề xuất (chờ user ok):** không loại món, không chặn phát hành. Máy luôn nhận đủ menu; món nào không pha được thì hiện "hết" trên POS, và máy báo lên server trạng thái từng món kèm lý do.
   - Hết tồn: đã có sẵn. Trigger `drink.in_stock` (`database.sql:1082-1180`) tự tính; agent đẩy lên cùng bản tồn kho.
   - Máy không có nguyên liệu đó: agent bỏ **toàn bộ** dòng công thức của món. Trigger cho `in_stock=0` vì món không còn dòng công thức nào (`COUNT(*) > 0`). Agent báo lý do "thiếu nguyên liệu id X".
   - Server hiện cho từng máy: món hết, lý do (nạp lại được, hay cần lắp nguyên liệu / sửa menu).
3. Vé đã in pha theo công thức mới: **user OK** (giữ như hiện trạng).
4. Đổi giá và bật/tắt món: **áp ngay như admin_gui** (user chốt). Mỗi lần lưu tự tạo một phiên bản menu và đánh thức các máy.
5. Nhật ký thao tác: **tạm thời theo sát admin_gui**, không làm `audit_log`.
6. Server: **Linux, trong LAN, chưa có đồng bộ giờ.** Đề xuất: server chạy chrony làm NTP cho LAN (`allow <subnet>`, `local stratum 10`); máy trỏ NTP về server; agent chờ đồng bộ giờ xong mới ký request.
7. 999 món và 24 nguyên liệu: **user OK.**
