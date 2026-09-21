# Đặc tả dữ liệu

> Nguồn: [Kiến trúc đội máy FlexMix](../Kien_Truc_Doi_May.html), đề xuất bản 3 ngày 10/09/2026, tham chiếu `version1.0 @ ce17f05`. Tài liệu này được tách từ HTML; chưa đối chiếu mã nguồn ứng dụng và không xác nhận chức năng đã triển khai. “Yêu cầu” là mục tiêu trong đề xuất, “hiện trạng” là mô tả của nguồn, “đề xuất bổ sung” cần được duyệt. Các điểm chưa chốt nằm trong [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

## Cập nhật từ OWNER — DRAFT, 17/09/2026

DEC-001 (DRAFT): một thực đơn chung cả đội. Override theo điểm chưa được OWNER xác nhận; A-01 chỉ được trả lời phần menu chung.

DEC-009 (DRAFT): MID là số nguyên dương 1–999999, đã cấp không tái sử dụng kể cả decommission hoặc thay thế. Giới hạn QR còn mở tại Q-27; MID/UUID/machine_id/credential vẫn mở tại Q-12.

Theo DEC-006 (DRAFT), recipe được ghim tại thời điểm tạo ticket; recipe mới chỉ áp dụng cho ticket tạo sau khi version mới được publish, không đổi ticket đang tồn tại. C-17 vẫn giữ yêu cầu cửa sổ yên tĩnh cho thay đổi mã nguyên liệu; điều kiện chính xác và quy tắc xóa mềm vẫn mở tại Q-11. Pin recipe không bãi bỏ C-17 hoặc cho phép áp chúng ngay. Quan hệ publish tại Hub với apply tại máy offline và cách lưu recipe chưa chốt.

DEC-004 (DRAFT): thu tiền lúc in nhãn. Báo cáo used/completed_at chỉ phản ánh vé pha xong, không đủ đại diện tiền thực thu. OWNER chưa chọn schema thanh toán/hoàn tiền hoặc công thức báo cáo thay thế (Q-07, Q-17).

DEC-005 (DRAFT): mở cửa 08:00–22:00 mỗi ngày; quản lý cửa hàng nhận cảnh báo; không có người trực ngoài giờ; cảnh báo ngoài giờ “xử lý trong ngày”. Chưa chốt múi giờ, SLA hoặc cách xử lý cảnh báo cuối ngày; không tự chuyển thành ngày làm việc kế tiếp.

DEC-002/DEC-003 (DRAFT): chấp nhận mất khóa QR; không vé liên máy. Không thêm bảng ký gửi khóa hoặc thẩm quyền vé ở Hub.

Các DEC được ghi tại [06_decisions.md](06_decisions.md), chưa ACCEPTED và chưa là căn cứ triển khai. Phần nguồn/hiện trạng được giữ để truy nguyên.

## Mức độ hoàn chỉnh

Đây là mô hình logic và quy tắc ghi dữ liệu rút từ nguồn, không phải DDL sẵn chạy. Không có mã nguồn/DDL ứng dụng trong workspace để kiểm chứng kiểu cột, khóa ngoại hay trigger. Các bảng Hub chưa được nguồn định nghĩa đầy đủ; không tự coi tên bảng gợi ý là hợp đồng đã duyệt.

## Quyền sở hữu dữ liệu

| Dữ liệu | Chủ ghi | Đồng bộ/quy tắc |
|---|---|---|
| `drink`, `recipe`, `glass`, `drink_type`, `category` | Hub, trừ cột nêu riêng | Danh mục xuống |
| `recipe_action` | Hub | Cùng transaction và dãy `step_no` với recipe; gồm media, `cup_returns` |
| `drink_category_mapping` | Hub | Danh mục xuống, thống nhất phân loại báo cáo |
| `drink.deleted_at` | Hub | Tombstone; quy tắc áp còn mở Q-11. DEC-006 chỉ chọn pin recipe, chưa quyết định xóa mềm; A-06 giữ khuyến nghị nguồn để truy nguyên |
| `ingredient.id/name/type/data_type` | Hub qua ánh xạ | Giữ nguyên ID cũ tại máy |
| `ingredient.amount/in_stock/max_gram` | Máy | Hub chỉ đọc |
| `ingredient.threshold_gram` | Dẫn xuất | `recalculate_thresholds()`: 110% lượng dùng lớn nhất trong các công thức |
| `ingredient.gpio` | Máy | Bản đồ bơm/panel, gửi lên |
| `drink.published` (mới) | Hub | Món thuộc thực đơn điểm bán |
| `drink.available` | Máy | Công tắc quầy; Hub không ghi đè |
| `drink.in_stock` | Trigger | Tính lại từ tồn kho, không copy từ Hub |
| `store_setting` | Hub | Giải ghi đè máy > điểm bán > đội |
| `admin_user`, `role_permission` | Hub | Theo điểm bán, giữ hash/salt/rounds |
| `order_ticket` | Máy | Bản sao Hub cập nhật theo trạng thái |
| `error_log` | Máy | Gửi tăng dần; nguồn yêu cầu Hub giữ vĩnh viễn |
| `order_ticket.note` | Máy | Không có trong telemetry; tối đa 200 ký tự theo nguồn |
| `schema_migration` (mới) | Máy | Hub nhận trạng thái schema |
| Gói sao lưu đêm | Máy | Bản sao trên ổ khác, sau đó lên Hub theo chính sách lọc |
| `audit_log` (mới) | Máy ghi, Hub gộp (theo nguồn) | Máy gửi lên như `error_log`. Audit cho thao tác tại Hub là **đề xuất bổ sung**, không có trong bảng sở hữu của nguồn; có hay không, và tách khóa với audit của máy thế nào, còn mở tại Q-30 |
| `pump_calib.json`, `calib_loadcell.json` | Máy | Sao lưu, không đồng bộ giá trị chung |
| `machine_profile.json` | Máy | GPIO/I2C/máy in; sao lưu |
| `order_mode.json`, `display_mode.json` | Máy áp lệnh Hub | Không ghi đè file tùy tiện |
| `recipe/image`, `recipe/media` | Hub | Asset theo hash |
| `store_gui/menu-data.js` | Dẫn xuất | Dựng từ DB bằng `sync_menu`, không truyền file |
| `QRPROTO_KEY`, `admin_account.json` | Máy | Không gửi Hub |

## Định danh và ánh xạ

MID do Hub cấp, duy nhất và không tái sử dụng. Miền 1–999999 trong nguồn là miền của câu hỏi nhập tay trong `install.sh` hiện trạng, cơ chế sẽ bị bỏ; OWNER đã chọn miền cấp phát 1–999999 trong DEC-009 (DRAFT); giới hạn payload QR vẫn chưa xác nhận (Q-27). UUID thiết bị và MID đều xuất hiện trong nguồn nhưng quan hệ chính xác với trường wire `machine_id` cần chốt Q-12.

- Khóa vé ở Hub: `(machine_id, serial)`; không thay serial để tránh trùng giữa các máy.
- Khóa lỗi gợi ý: `(machine_id, error_id)`; khóa audit cần định nghĩa một ID ổn định (đề xuất bổ sung; Q-14, Q-30).
- Ánh xạ nguyên liệu: máy + mã cục bộ → nguyên liệu chuẩn; một mã đã cấp không đổi nghĩa hoặc tái dùng.
- Mã lựa chọn mới dùng 1–24, `weight` mới từ 100 trở lên; không ép đổi mã cũ. Các khoảng hiện trạng được nguồn nêu: ingredient 0001–0999, drink 1001–1999, glass 3001–3999.
- ID drink/SKU xung đột khi nhận máy khác chưa được giải chi tiết như ingredient; không tự động đánh số lại vé (Q-13).

## Thành phần logic Hub cần lưu

| Nhóm | Dữ liệu tối thiểu |
|---|---|
| Đăng ký máy | MID, UUID, điểm bán, khóa công khai/trạng thái thu hồi, múi giờ, vòng release |
| Điểm bán | Giờ mở cửa, phạm vi người dùng, ghi đè cấu hình/giá |
| Danh mục chuẩn | Món, nguyên liệu, công thức, bước tay, phân loại, media |
| Ánh xạ/cấp phát | Mã theo máy, mã đã ngừng dùng, người duyệt đối chiếu |
| Trạng thái mong muốn | Snapshot theo máy, version, min_schema, chữ ký, assets, lịch sử áp |
| Quan sát máy | Vé, lỗi, audit, tồn kho/khe cắm mới nhất, heartbeat |
| Vận hành | Lệnh/ACK, release đã ký, vòng triển khai, metadata backup |

Các quan hệ logic: điểm bán có nhiều máy; máy có nhiều snapshot/lệnh/vé; một nguyên liệu chuẩn có nhiều ánh xạ theo máy. Schema vật lý, kiểu tiền, index và retention còn phải chốt.

## Migration tại máy

Nguồn đề xuất `schema_migration(name PK, applied_at, checksum, duration_ms)`. Chỉ ghi dòng sau migration thành công. Heartbeat báo tên migration cuối và số dòng. MySQL DDL không được coi là có rollback transaction; cần phát hiện schema dở dang và cho phép chạy lại an toàn. Thứ tự migration và cách so `min_schema` cần xác định, không chỉ so số dòng hoặc tên tùy ý.

`recipe_action` được nguồn mô tả là chỉ tạo bởi Python migration trong `db_core.py`, không có trong `database.sql`; quy trình bootstrap phải bao phủ cả hai.

Thêm `order_ticket.updated_at DATETIME(3) ON UPDATE CURRENT_TIMESTAMP(3)` và index phục vụ đọc thay đổi. Default, backfill bản ghi cũ, xử lý các dòng trùng thời gian và chỉ mục ghép chưa chốt. Thêm `drink.published` với quy tắc backfill chưa chốt. `audit_log` cần người thực hiện, thời gian, endpoint, đối tượng, trước/sau; phải lọc bí mật.

## Vé, tồn kho và báo cáo

Các trạng thái được nguồn nhắc tới: `unused`, `in_progress`, `used`, `expired`; chưa đủ để tự định nghĩa toàn bộ state machine cho hủy/hỏng. `claim()` là UPDATE nguyên tử tại máy, hai bản in vẫn chỉ được pha một lần. Khi reboot, nguồn mô tả trả vé mắc kẹt về `unused`.

`price` và `drink_name` được chụp khi phát hành, không tính lại theo danh mục mới. Báo cáo hiện trạng lọc `status='used'` và `completed_at`, gom theo ngày địa phương. Không có bảng thanh toán; không suy diễn vé phát hành là tiền đã thu.

Tồn kho bị trừ bởi `consume_inventory` khi hoàn tất hoặc `charge_for_failed_order` khi hỏng giữa chừng. Kiểm `available`/`in_stock` lúc phát hành là cải thiện đề xuất, không đặt chỗ nguyên liệu. Chỉ số vé chưa quét dựa trên `unused + expired` là xấp xỉ trong nguồn; vé từng claim rồi được trả có thể bị đếm sai (Q-17).

## Nguyên tử, cursor và lưu giữ

Snapshot chỉ thay đổi dữ liệu Hub sở hữu; không xóa vật lý lịch sử hay ghi đè cột máy sở hữu. Ghi version đã áp trong cùng giao dịch dữ liệu là đề xuất bổ sung để tránh báo version sai sau crash. Tính lại threshold và trạng thái tồn theo cơ chế thực tế cần kiểm tra.

Vé được đọc bằng thời gian cập nhật có overlap; cần giải pháp cho cập nhật đến muộn và trang nhiều dòng cùng timestamp. Hub không được để bản gửi lại cũ ghi đè trạng thái mới hơn. Cursor chỉ lưu bền sau 200 và ACK khớp. Retention máy không được dọn mất bản ghi chưa được xác nhận.

Giữ 7 backup đêm trên ổ khác, 3 backup trước migration; số snapshot và backup trên Hub là N chưa chốt. Lịch sử máy thanh lý được giữ; MID cũ không được gán cho máy mới. Không phục hồi vé cũ sang danh tính máy thay thế một cách tự động.
