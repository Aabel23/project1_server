# C0.8 · Một nơi ghi dữ liệu

**Đề xuất để review, chưa duyệt.** Codex tiếp quản Claude ngày 08/10/2026.
Theo yêu cầu user, DB server tạm SQLite `var/flexmix.db`; sẽ migrate sang MySQL
sau. SQLite không chứng minh tiêu chí InnoDB, quyền SQL theo cột hay độ bền Pi.
S-DB cung cấp transaction/migration, không sở hữu logic bảng nghiệp vụ.

## Server

| Bảng | Khối duy nhất ghi nghiệp vụ | Người đọc / gọi API |
|---|---|---|
| schema_migration | S-DB | quản lý migrate |
| admin_user, role_permission, user_machine | M-ACC | S-SECA qua Accounts |
| machine | M-MAC | M-MENU/M-CMD/M-KEY đọc; đổi assignment/last_seen qua M-MAC |
| server_key, machine_credential, enrollment_code | M-KEY | S-FM1 qua Keys |
| packet_claim | S-FM1 | S-FM1 |
| glass, drink_type, category, drink, recipe, recipe_action, media_file, ingredient_registry | M-CAT | M-MENU/M-PUB qua Catalogue/Media |
| menu, menu_item, menu_item_category, menu_setting, menu_version | M-MENU | M-MAC/M-PUB qua Menus |
| machine_menu_apply | M-PUB | M-MAC qua Publish |
| sale, fault, machine_ingredient_cache | M-ING | M-REP đọc; M-CMD gọi Ingest, không UPDATE thẳng |
| machine_command | M-CMD | M-MAC qua Commands; S-EPOCH gọi mark_unknown_all |
| server_state | S-EPOCH | S-FM1/S-SECA qua Epoch |

Migration DDL và seed do file của chủ bảng định nghĩa, runner S-DB thực thi
trong lifecycle riêng; không tính runner thành writer nghiệp vụ thứ hai.
Module khác không DELETE/UPDATE/INSERT bảng không thuộc mình, dù nằm cùng
transaction. Muốn cập nhật nhiều khối thì wiring inject API của chủ bảng.
M-MENU tính target từ machine.menu_id và menu_version; không tự UPDATE machine.

**Đề xuất xử lý high-water:** thiết kế S-FM1 yêu cầu cập nhật high-water trong
machine_credential, nhưng chủ bảng vẫn là M-KEY. C0.10 thêm
`keys.advance_high_water(connection,kid,issued_at_ms)->Credential`: S-FM1
truyền connection của transaction claim, SQL do M-KEY thực thi. M-KEY kiểm
lại credential active/retiring theo policy đã chốt, reject absent/revoked bằng
Forbidden, cập nhật max(high-water,issued_at_ms), không giảm mốc. SQLite claim
dùng BEGIN IMMEDIATE; MySQL sau migrate phải khóa row credential để serialize
với revoke. Cùng transaction claim/high-water/epoch rollback cùng nhau.
Credential đọc trả hw_issued_at để S-FM1 kiểm W trước crypto. Cột thông báo
thu hồi last_revoked_notice_at vẫn do M-KEY ghi qua API throttling sẽ chốt tại
M-KEY; không cho S-FM1 UPDATE trực tiếp. Đây là đề xuất Codex cần crypto review,
không phải duyệt tự động hoặc thêm bảng. S-DB không tạo schema nghiệp vụ.

## Máy (Q6 vẫn chờ)

| Bảng / nhóm cột | Khối ghi trong phạm vi agent |
|---|---|
| agent_ledger, result outbox | A-RUN |
| agent_state: kid, server_epoch, install_uuid | A-NET |
| agent_state: applied epoch/version/hash, lịch ẩn món | A-APPLY |
| agent_state: con trỏ vé/lỗi | A-UP |
| agent_state: hash báo tồn đã ACK | A-STOCK |
| glass, drink_type, category, drink, recipe, recipe_action, drink_category_mapping, store_setting được sync | A-APPLY |
| ingredient, order_ticket, error_log do **lệnh từ server** thay đổi | A-RUN |

agent_state là ngoại lệ nháp theo plan: một writer cho **nhóm cột**, không writer
toàn bảng. Reviewer quyết định tách bảng hay giữ quyền theo cột; chưa coi đã
chốt. Setup schema A-DB không ghi trạng thái vận hành thay agent. Kiosk/POS/
runner hiện có vẫn là nguồn ghi ingredient/ticket/error của máy khi bán hàng;
quy tắc A-RUN chỉ nói writer của lệnh từ server, không xóa quyền chạy máy cũ.
Helper ghi file/order-mode/display, không ghi ledger; print đọc payload cục bộ.

## Kiểm và lỗi

Writer ngoài quyền là lỗi kiến trúc, reviewer từ chối; không có runtime proxy
SQL phân quyền trong SQLite. S-DB transaction rollback khi exception, ghi dùng
query placeholders `?`, không nội suy SQL. Query đọc không thay writer owner.
SQLite foreign_keys/synchronous FULL kiểm bằng S-DB, MySQL kiểm khi migrate.

Hợp lệ: M-CMD gọi `ingest.upsert_ticket(machine_id,row)` sau result đúng máy.
Từ chối: M-CMD UPDATE sale; M-MENU UPDATE machine; A-UP UPDATE toàn agent_state
xóa applied; S-FM1 UPDATE credential trực tiếp thay gọi API M-KEY.
