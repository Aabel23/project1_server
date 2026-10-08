# P2 · Quản trị menu trên server

- **Trạng thái:** CHƯA THỰC HIỆN.
- **Luồng thiết kế:** N1, N2, N3, N4, N6 (phía server), K4, D3 (trang). Quyết định nền ở `phuong_an_kien_truc.md` §4 và §8.

## Mục tiêu

Mọi thao tác của các trang Menu, Trang chủ, Sửa công thức, Thùng rác trong admin_gui chạy được trên server, kèm hai điểm mới:

- **Menu là thực thể riêng.** Mỗi máy dùng đúng một menu.
- **Mỗi lần lưu tạo một `menu_version` bất biến.** Bản này kèm sha256, và đặt bản đích cho các máy đang dùng menu đó.

Chưa có máy nào nhận menu ở phase này. Máy áp menu ở P5.

## Điều kiện vào

- P1 ✓.
- Q7: dữ liệu ban đầu lấy từ đâu. Chỉ chặn P2.6. Các bước khác chạy được với dữ liệu thử.

## Đầu ra

| Đầu ra | File |
|---|---|
| Migration các bảng menu | `db/migrations/0002_menu.sql` |
| Module thư viện món, menu, media, sổ id nguyên liệu, báo cáo | `modules/catalogue/`, `modules/menus/`, `modules/media/`, `modules/ingredient_registry/`, `modules/reports/` |
| **Hợp đồng snapshot menu.** P5 dùng file này làm đầu vào | `internal/contracts/menu_snapshot.md` |
| Các trang menu, home, recipe-editor, bin, report, tickets, errors | `static/` |
| Test | `tests/p2/` |

## Phase con

### P2.1 Schema menu

`0002_menu.sql` gồm ba nhóm bảng:

| Nhóm | Bảng |
|---|---|
| Giữ từ DB máy | `glass`, `drink_type`, `category` |
| Sửa | `drink`: bỏ `price`, `available`, `featured`, `in_stock`.<br>`recipe`: `ingredient_id` không có khoá ngoại, thêm `expected_name`, `expected_data_type`.<br>`recipe_action`: giữ nguyên |
| Thêm | `menu` (có `row_version`), `menu_item` (khoá `(menu_id, drink_id)`, có `price`, `available`, `featured`, `sort_order`), `menu_item_category`, `menu_setting`, `menu_version` (snapshot JSON, sha256, `server_epoch`), `media_file` (sha256, size), `ingredient_registry`, `sale`, `fault` |

`sale` và `fault` tạo ở đây để trang D3 chạy được ngay, dù bảng còn rỗng. Dữ liệu đổ vào ở P5.

**Kiểm:**

- Migration áp lên DB của P1 thành công.
- Ràng buộc SKU 1001–1999 có test.

### P2.2 N1 · Thư viện món, công thức, ảnh, media

| ID | Việc | Route | Kiểm |
|---|---|---|---|
| P2.2.1 | Thêm và sửa món. SKU cấp toàn server, không bao giờ cấp lại kể cả khi món bị xoá hẳn | `EDITOR_PATH` | Test: xoá hẳn SKU 1005 rồi thêm món mới, món mới không nhận 1005 |
| P2.2.2 | Công thức trỏ nguyên liệu bằng id trong sổ chung (P2.3), lưu kèm `expected_name` và `expected_data_type` | `RECIPE_PATH` | Id không có trong sổ thì 400 |
| P2.2.3 | Ảnh và media: lưu file theo sha256, ghi size. Có giới hạn kích thước khi tải lên | `IMAGES_PATH`, `IMAGE_UPLOAD_PATH`, `MEDIA_LIST_PATH`, `MEDIA_UPLOAD_PATH` | Tải trùng file thì chỉ một bản; file quá giới hạn thì 413 |
| P2.2.4 | Chép trang `recipe-editor.js` và `menu-store.js`, sửa theo cookie phiên và `textContent` | | Test tay: sửa công thức Peach Tea, mọi menu có món này đều đổi |

- **Nguồn chép logic:** `version1.0/admin_gui/serve.py` (handler editor, recipe, upload) và `database/admin_functions/drinks`.

### P2.3 K4 · Sổ cấp id nguyên liệu

| ID | Việc | Kiểm |
|---|---|---|
| P2.3.1 | Bảng `ingredient_registry`: mỗi tên nguyên liệu đúng một id, trong khoảng 1–24 (`qrproto/constants.py:53`) | Test: cấp tới id 24 thì lần cấp sau bị từ chối |
| P2.3.2 | Endpoint sổ cấp id. Thẻ K4 của thiết kế ghi "cần thêm". Đặt hằng mới `INGREDIENT_REGISTRY_PATH` trong `routing.py` | Có trong `routing.py` và có test |
| P2.3.3 | Seed: id 1–13 theo `version1.0/database/database.sql:1220-1239`, để khớp các máy hiện có | So bảng seed với file nguồn |

### P2.4 N2 · Sửa menu và phát hành phiên bản

| ID | Việc | Route | Kiểm |
|---|---|---|---|
| P2.4.1 | Giá, bật/tắt, featured theo `menu_id`. Mọi request đổi dữ liệu mang `row_version`, `request_key`, `server_epoch` | `PRICE_PATH`, `AVAILABLE_PATH`, `FEATURED_PATH` | Hai người cùng sửa: người lưu sau nhận 409 |
| P2.4.2 | Cấu hình featured, bestseller, layout theo menu | `FEATURED_CONFIG_PATH`, `BESTSELLER_CONFIG_PATH`, `LAYOUT_PATH` | Như admin_gui |
| P2.4.3 | Trong cùng một transaction với mỗi lần lưu: ghi `menu_item`, tăng `row_version`, dựng snapshot, tạo `menu_version` mới, đặt bản đích cho mọi máy dùng menu đó. Sau commit thì gọi tín hiệu đánh thức | | Test: lỗi giữa chừng thì không có `menu_version` mồ côi |
| P2.4.4 | Gửi lại cùng `request_key` thì trả kết quả cũ. Cùng key mà khác body thì 409. `server_epoch` khác thì 409 "tải lại trang" | | Test ba ca |
| P2.4.5 | Quyền sửa menu dùng chung: chỉ owner, hoặc người quản lý **mọi** máy đang dùng menu đó (A3) | | Test: manager chỉ có máy A thì không sửa được menu A+B |

### P2.5 Hợp đồng snapshot

Viết `internal/contracts/menu_snapshot.md` trước khi code P2.4.3. Reviewer duyệt file này, vì P5 dựa vào nó.

**Nội dung hợp đồng:**

- các trường;
- cách sắp thứ tự để sha256 ổn định;
- danh sách media (sha256, size);
- `server_epoch` và `version`;
- giới hạn kích thước.

**Kiểm:** một test dựng snapshot từ cùng dữ liệu hai lần, sha256 phải giống nhau.

### P2.6 N3, N4 và nhập dữ liệu ban đầu

| ID | Việc | Route | Kiểm |
|---|---|---|---|
| P2.6.1 | N3: sao chép menu | `MENU_COPY_PATH` | Menu mới có đủ món, giá, thứ tự |
| P2.6.2 | N3: đổi giá hoặc bật/tắt một món trên nhiều menu cùng lúc. Thẻ N3 của thiết kế ghi "cần thêm": đặt `MENU_BULK_PATH` | `MENU_BULK_PATH` (mới) | Mỗi menu bị đổi có một `menu_version` mới; quyền kiểm theo từng menu |
| P2.6.3 | N4: gán menu cho máy | `MACHINE_SAVE_PATH` (trường `menu_id`) | Đổi menu thì bản đích của máy đổi theo |
| P2.6.4 | ⏸ Q7: công cụ nhập thư viện món, công thức, ảnh, tài khoản từ bản dump DB của một máy version1.0 | `manage.py import-machine-db` | Chạy trên bản dump thử: số món và công thức khớp |

### P2.7 N6 phía server và D3

| ID | Việc | Route | Kiểm |
|---|---|---|---|
| P2.7.1 | Thùng rác thư viện món: xoá mềm, khôi phục, xoá hẳn (SKU vẫn không cấp lại) | `DELETE_PATH`, `RESTORE_PATH`, `PURGE_PATH`, `BIN_PATH` | Như admin_gui |
| P2.7.2 | Trang Báo cáo, Vé, Lỗi đọc từ `sale` và `fault`, có lọc `?machine=<id>` hoặc `?machine=all` | `REPORT_PATH`, `ORDERS_PATH`, `TICKETS_PATH`, `ERRORS_PATH` | Bảng rỗng thì trang hiện "chưa có dữ liệu", không lỗi |
| P2.7.3 | Chép các trang `menu`, `home`, `bin`, `report`, `tickets`, `errors` sang `static/`, đổi `innerHTML` thành `textContent` cho dữ liệu đến từ máy | | `grep innerHTML` |

Phần "máy ẩn món 24 giờ rồi mới vào thùng rác" làm phía máy ở P5.3.

## Cổng ra P2

- `pytest server/tests/p2 -q` đạt.
- Test tay trên trình duyệt:
  1. Tạo món mới.
  2. Gắn món vào hai menu.
  3. Đổi giá trên một menu.
  4. Thấy `menu_version` tăng đúng menu đó.
- `menu_snapshot.md` đã được duyệt.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Dữ liệu các máy hiện có lệch nhau: cùng SKU khác món, cùng id nguyên liệu khác tên | P2.6.4 phải báo xung đột, không tự gộp. Đưa danh sách xung đột cho user |
| Snapshot quá lớn khi có nhiều ảnh | Ảnh không nằm trong snapshot, chỉ có sha256 và size; máy tải riêng (P5.1) |
