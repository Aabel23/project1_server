# Server mẹ FlexMix: những gì đã hiểu và đã chốt

Cập nhật: 2026-10-07

## 1. Mục tiêu

- Server mẹ **thay thế hoàn toàn** `version1.0/admin_gui`. admin_gui trên máy sẽ bị xoá, và server trở thành nơi quản lý duy nhất.
- Chức năng quản lý giữ **y hệt admin_gui**. Chỉ thêm hai thứ:
  - quản lý **nhiều máy** từ một chỗ;
  - **mỗi máy một menu riêng** (bảng `drink` có cột `machine_id`).
- Phạm vi server chỉ gồm hai phần: giao diện quản lý và giao tiếp qua lại với các máy version1.0. Không thêm tính năng mới ngoài hai điểm trên.

## 2. Ràng buộc đã chốt

- Chạy trong mạng LAN nội bộ, giao tiếp qua HTTP. Chưa cần internet hay TLS.
- Dùng lại giao diện HTML/JS vanilla của admin_gui, không viết lại từ đầu.
- Dữ liệu quản lý (menu, công thức, cấu hình) do server sửa rồi đẩy xuống máy. Nguyên liệu nằm ở máy, server chỉ gọi xuống để đọc/ghi (xem mục 8).
- Máy offline vẫn bán theo bản sao menu cuối cùng nhận được.
- Stack (framework, DB) **chưa chốt**: sẽ đưa vài phương án để user chọn.
- Quy trình làm việc: hai architect đề xuất và phản biện tới khi ra phương án tốt nhất → báo user → user đồng ý mới dựng HTML mô tả hệ thống, chia nhỏ thành từng luồng.
- Thư mục này **không liên quan** tới `androidv0.1/server` (app là một phiên bản khác).

## 3. Hiện trạng version1.0 (nguồn để thay thế)

### admin_gui

- `admin_gui/serve.py` (khoảng 3.800 dòng) dùng `ThreadingHTTPServer` thuần, có khoảng 45 route `/api/*`.
- 14 trang: home, login, users, menu, bin, recipe-editor, ingredients, refill, report, tickets, errors, mode, display, cùng phần quyền (`permissions.py`, `auth.py`).

### Database

- MySQL, tên DB `beveragepos`, schema ở `database/database.sql`.
- Các bảng: `glass`, `drink_type`, `drink`, `category`, `store_setting`, `drink_category_mapping`, `ingredient`, `order_ticket`, `error_log`, `recipe`, `recipe_action`, `admin_user`, `role_permission`, `schema_migration`.

### Cấu hình lưu trong file, không lưu trong DB

- `configuration/order_mode.py`: bật/tắt printQR và runDirect.
- `configuration/display_mode.py`: độ phân giải màn hình kiosk, áp dụng có thời gian thử và tự hoàn tác nếu không bấm keep.

### Các phần khác trên máy

- `store_gui/sync_menu.py`: đọc DB rồi ghi ra `store_gui/menu-data.js` cho màn hình POS. Phải chạy lại sau mỗi lần menu, công thức hoặc tồn kho thay đổi.
- `database/admin_functions/` (drinks, ingredients): các hàm thao tác DB dùng chung. Sẽ **giữ lại** để agent trên máy dùng.

## 4. Phân loại chức năng theo chỗ dữ liệu sinh ra

| Loại | Chức năng | Hướng đi của dữ liệu |
|---|---|---|
| Server làm chủ | menu, thùng rác, công thức, ảnh/media, nguyên liệu | server → máy |
| Máy sinh ra | đơn hàng, vé, lỗi, báo cáo | máy → server |
| Hai bên cùng đổi | tồn kho, nạp nguyên liệu | máy báo mức tồn lên, server gửi lệnh nạp xuống |
| Lệnh phần cứng | in lại vé, order-mode, display | server → máy, máy phải online |
| Riêng của server | đăng nhập, users, quyền (thêm phân quyền theo máy) | ở lại server |

## 5. Endpoint

Toàn bộ endpoint đã được viết thành hằng `*_PATH` trong `server/server/routing.py`:

- **A0 – quản lý máy (mới):** danh sách máy, thêm/sửa/xoá máy, cấp lại token, trạng thái từng máy, ép đồng bộ ngay, sao chép menu giữa các máy.
- **A1 – tài khoản và quyền:** giữ nguyên route của admin_gui.
- **A2 – menu theo máy:** các route menu và cấu hình cửa hàng có thêm `{machine_id}`. Ảnh và media dùng chung cho mọi máy.
- **A3 – nguyên liệu và tồn kho:** theo từng máy.
- **A4 – báo cáo, vé, lỗi:** lọc bằng `?machine=<id>`, hoặc `?machine=all` để xem gộp.
- **A5 – lệnh xuống máy:** in lại vé, order-mode, display.
- **B – kênh của máy (`/api/agent/*`):** hello, heartbeat, tải menu, tải media, xác nhận đã áp dụng menu, gửi đơn, gửi lỗi, gửi tồn kho, lấy lệnh, báo kết quả lệnh.

## 6. Thay đổi cần làm phía máy (version1.0)

- Xoá thư mục `admin_gui/`.
- Bỏ bước tạo mật khẩu admin bằng `admin_gui.auth` trong `deploy/install.sh`. Thay bằng bước nhập địa chỉ server và token của máy.
- Xoá mục `admin_gui` trong `configuration/served_paths.py`.
- Thêm **agent**: tiến trình chạy nền gọi các route nhóm B, ghi dữ liệu vào MySQL cục bộ, rồi chạy `sync_menu`.

## 7. Thay đổi DB phía server (đề xuất)

- **Bảng mới:**
  - `machine` (id, tên, token_hash, last_seen, menu_version)
  - `machine_command` (hàng đợi lệnh gửi xuống máy)
  - `user_machine` (user được quản lý máy nào)
- **Thêm cột `machine_id`:** vào `drink`, `ingredient`, `store_setting`, `order_ticket`, `error_log`.
- **Dùng chung cho mọi máy:** `glass`, `drink_type`, `category`, ảnh và media.

## 8. User đã chốt (2026-10-07)

- Server có **database riêng**, giống DB của máy, cộng thêm: bảng `machine`, quản lý nhân viên, và một phương pháp quản lý **nhiều menu** (chưa có, cần đề xuất).
- **Nguyên liệu nằm ở máy.** Server gọi xuống máy để đọc dữ liệu, không giữ bản chính. (Mục 7 về `ingredient.machine_id` trên server vì thế không còn đúng.)
- Hướng giao tiếp máy ↔ server: giao cho hai architect chọn phương án tốt nhất.
- **Giữ** đổi độ phân giải màn hình từ xa.
- **Chấp nhận:** server sập thì máy vẫn bán, nhưng không sửa hay nạp được gì.
- Stack: architect đề xuất.

## 8b. Còn chờ

- Kết quả hai architect: hướng giao tiếp, phương pháp nhiều menu, schema DB server, stack.

## 9. Hiện trạng thư mục server/

- `main.py` rỗng.
- `server/routing.py` đã có.
- `agents/*.md` chứa định nghĩa vai agent. Chưa được đăng ký vào `.claude/agents/`, và mô tả của planner, reviewer, tester vẫn còn ghi "androidv1.0".
- `docs/thiet_ke_server_me.html`: bản HTML mô tả thiết kế, dựng lại ngày 2026-10-08 theo mẫu `FexMix_Munual.html` và quy ước trong `quy_uoc_so_do.md`.
- Thư mục chưa phải git repo.
