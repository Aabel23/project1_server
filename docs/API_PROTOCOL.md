# Giao thức Hub – Agent

> Nguồn: [Kiến trúc đội máy FlexMix](../Kien_Truc_Doi_May.html), đề xuất bản 3 ngày 10/09/2026, tham chiếu `version1.0 @ ce17f05`. Tài liệu này được tách từ HTML; chưa đối chiếu mã nguồn ứng dụng và không xác nhận chức năng đã triển khai. “Yêu cầu” là mục tiêu trong đề xuất, “hiện trạng” là mô tả của nguồn, “đề xuất bổ sung” cần được duyệt. Các điểm chưa chốt nằm trong [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

## Cập nhật từ OWNER — DRAFT, 17/09/2026

DEC-001 (DRAFT): một thực đơn chung cả đội. Override theo điểm chưa được OWNER xác nhận; A-01 chỉ được trả lời phần menu chung.

DEC-009 (DRAFT): MID là số nguyên dương 1–999999, đã cấp không tái sử dụng kể cả decommission hoặc thay thế. Giới hạn QR còn mở tại Q-27; MID/UUID/machine_id/credential vẫn mở tại Q-12.

DEC-003 (DRAFT): không có phạm vi vé liên máy.

Theo DEC-006 (DRAFT), recipe được ghim tại thời điểm tạo ticket; recipe mới chỉ áp dụng cho ticket tạo sau khi version mới được publish, không đổi ticket đang tồn tại. C-17 vẫn giữ yêu cầu cửa sổ yên tĩnh cho thay đổi mã nguyên liệu; điều kiện chính xác và quy tắc xóa mềm vẫn mở tại Q-11. Pin recipe không bãi bỏ C-17 hoặc cho phép áp chúng ngay. Quan hệ publish tại Hub với apply tại máy offline và cách lưu recipe chưa chốt.

DEC-007 (DRAFT, nguồn ô Q-22; mapping sang Q-21 là đề nghị biên tập, chờ OWNER xác nhận): không cho Machine nhận order khi khởi động offline và chưa sync clock. Không suy ra RTC bắt buộc hoặc cơ chế xác nhận sync; Q-21 vẫn còn phần mở, Q-22 chưa được trả lời.

Các DEC được ghi tại [06_decisions.md](06_decisions.md), chưa ACCEPTED và chưa là căn cứ triển khai. Phần nguồn/hiện trạng được giữ để truy nguyên.

## Quy tắc chung

Máy chủ động mở kết nối HTTPS qua Tailscale. Sơ đồ nguồn yêu cầu mTLS; phần định danh còn yêu cầu Ed25519 ký mọi request. Cách kết hợp, chứng thư, header và dữ liệu ký chưa được định nghĩa (Q-15). Không tự coi giao thức này là OpenAPI hoàn chỉnh.

Mọi thời gian qua dây dùng UTC ISO-8601; máy báo múi giờ để Hub dựng ngày kinh doanh địa phương. Cột MySQL DATETIME cục bộ không tự mang timezone: cần chuyển đổi rõ tại adapter.

Máy bỏ qua trường bổ sung chưa hiểu. Hub không xóa hoặc đổi nghĩa trường trong contract đang dùng; thay đổi phá vỡ tương thích cần contract mới, chính sách nâng cấp chưa chốt. Máy thiếu schema phải từ chối snapshot và báo lý do.

## 1. Bản chụp trạng thái

`GET /v1/state?have=847`

- 304: không có bản mới cần áp theo mô tả nguồn.
- Bản mới: trả snapshot đầy đủ cho máy đã xác thực. Nguồn không định nghĩa đầy đủ status/header cho nhánh này.

| Trường nguồn | Ý nghĩa |
|---|---|
| `contract` | Phiên bản hợp đồng; kiểu và giá trị chưa chốt |
| `version` | Phiên bản snapshot |
| `min_schema` | Schema tối thiểu; thuật toán so sánh cần chốt |
| `generated_at` | Thời điểm UTC |
| `machine_id` | Danh tính máy đích; cần thống nhất MID/UUID |
| Khối danh mục | Đã lọc năng lực, ánh xạ mã và giải ghi đè; tên key/schema con chưa chốt |
| `assets[]` | Đường dẫn, SHA-256, số byte; tên key con chưa chốt |
| `signature` | Chữ ký; định dạng/canonicalization chưa chốt (Q-15); ai giữ khóa ký chưa chốt (Q-26) |

Agent kiểm tương thích, chữ ký, asset trước khi áp. Theo DEC-006 (DRAFT), recipe được ghim tại thời điểm tạo ticket; recipe mới chỉ áp dụng cho ticket tạo sau khi version mới được publish, không đổi ticket đang tồn tại. C-17 vẫn giữ yêu cầu cửa sổ yên tĩnh cho thay đổi mã nguyên liệu; điều kiện chính xác và quy tắc xóa mềm vẫn mở tại Q-11. Pin recipe không bãi bỏ C-17 hoặc cho phép áp chúng ngay. Quan hệ publish tại Hub với apply tại máy offline và cách lưu recipe chưa chốt. Upsert chỉ cột Hub sở hữu trong một transaction; lỗi trước commit giữ dữ liệu cũ. Sau commit, lỗi `sync_menu` cần phục hồi riêng, vẫn mở Q-22; DEC-007 không trả lời vấn đề này.

Rollback catalogue chỉ đến bản máy từng áp thành công và vẫn phải xét schema, asset, vé hiện hành. `have` và version khi quay về bản cũ cần đặc tả để không bị Hub lập tức đẩy lại bản vừa bỏ (Q-18).

## 2. Lô sự kiện

`POST /v1/events`

| Trường | Nội dung |
|---|---|
| `machine_id` | Máy nguồn |
| `kind` | `ticket`, `error` hoặc `audit` |
| `cursor_from` | Mốc bắt đầu; kiểu chưa chốt |
| `rows[]` | Dòng dữ liệu của loại tương ứng |
| `cursor_to` | Mốc đề nghị xác nhận |

Vé loại bỏ `note`; giữ serial, trạng thái và dữ liệu phục vụ báo cáo theo schema còn phải định nghĩa. Lỗi đọc theo `error_id`; vé đọc `updated_at` có overlap. ACK thành công phải là HTTP 200 kèm đúng `cursor_to` mà Hub đã ghi. Chỉ sau đó agent mới tiến mốc bền vững. Mất ACK thì gửi lại; Hub upsert vé theo `(machine_id, serial)`.

**Đề xuất bổ sung cần chốt:** Hub commit toàn lô rồi ACK; nếu cho phép thành công từng phần phải có quy ước cursor không bỏ qua dòng lỗi. Error/audit cần khóa idempotency riêng; vé cần chống ghi đè bởi bản cũ. Nguồn chưa có batch size, phân trang, giới hạn payload, backoff, mã lỗi hoặc chính sách poison record.

## 3. Nhịp tim

`POST /v1/beat`

Nguồn mô tả nội dung, chưa đặt tên key JSON/kiểu dữ liệu/tần suất. Không biến tên diễn giải sau thành key bắt buộc.

| Nhóm | Dữ liệu phải biểu diễn |
|---|---|
| Phiên bản | Tag đang chạy, snapshot đã áp, migration mới nhất và số migration, contract hỗ trợ |
| Sức khỏe | Uptime, nhiệt CPU, đĩa trống %, RAM, CmaFree, số lần dựng lại kiosk/giờ |
| Thời gian | Lệch NTP giây, timezone, trạng thái time-sync |
| Khả năng bán | Test mode, `order_mode` printQR/runDirect, runner đang mở, tuổi đơn, số vé phát hành/60 phút, máy in phản hồi, máy quét kết nối |
| Tồn đọng | Số lỗi chưa gửi, vé unused còn hạn, vé in_progress mắc kẹt, tuổi backup |

Để đáp ứng các cảnh báo, còn cần xác định biểu diễn trạng thái MySQL và thời điểm bắt đầu lỗi, thời gian không tương tác, tuổi test mode. Đây là khoảng trống giữa heartbeat và bảng cảnh báo, không phải trường đã có trong nguồn.

Tồn kho/khe cắm là snapshot định kỳ, nhưng nguồn chưa xác định nằm trong beat hay endpoint riêng. Backup, asset và diagnostics cũng chưa có wire protocol cụ thể.

## 4. Lệnh và ACK

Agent nhận lệnh qua kết nối nó mở (long-poll theo DEC-008 (DRAFT); endpoint, timeout và ACK vẫn chưa chốt). Nguồn không đặt URL nhận lệnh/ACK.

Envelope: `id`, `kind`, `args`, `issued_by`, `issued_at`, `expires_at`. ACK: `id`, trạng thái `accepted | refused | done | failed` và thông điệp. Tên key trạng thái/thông điệp, schema `args`, kiểu ID chưa chốt. Lệnh quá hạn không thực thi, ACK `refused`.

| Kind | Hành vi và điều kiện |
|---|---|
| `sync-now` | Kéo trạng thái; áp vẫn theo chốt snapshot |
| `set-order-mode` | Không được tắt cả printQR và runDirect |
| `set-display-mode` | Chỉ mode `xrandr --query` cho phép, tự hoàn tác 20 giây |
| `reprint-ticket` | In lại cùng vé, không tạo quyền pha thêm; cơ chế claim đảm bảo một lần dùng |
| `release-stranded` | Chỉ khi máy rảnh |
| `cancel-current-order` | Relay `/api/cancel`, trả vé theo đường hủy an toàn, audit người yêu cầu |
| `rollback-catalogue` | Chỉ bản từng áp thành công, xét an toàn vé |
| `run-backup-now` | Tạo và gửi gói theo chính sách backup |
| `restart-backend` | Từ chối khi đang pha |
| `collect-diagnostics` | Giới hạn dung lượng, phạm vi dữ liệu và ghi vết |
| `apply-release` | Máy rảnh, chữ ký độc lập, backup trước, kiểm sức khỏe và lùi mã khi thất bại |
| `run-pump`, `lamp-test`, `prime` | Luôn cần test mode xác nhận tại máy, kể cả backend chết |

Yêu cầu nguồn là giao lặp an toàn. **Đề xuất bổ sung:** lưu command ID/trạng thái bền vững trước và sau thực thi; retry trả lại kết quả cũ, không in lại/hủy thêm lần nữa. Quy tắc khôi phục khi crash giữa side effect và ghi kết quả cần chốt, không thể bảo đảm chỉ bằng ID trong RAM.

## API cục bộ liên quan

`POST /api/ticket` cần nhận giá đang hiển thị và phiên bản menu. Nếu không khớp, trả HTTP 409 kèm giá mới; UI báo và xác nhận trước khi in. Tên trường và error envelope chưa có trong nguồn. Kiểm `available` và `in_stock` tại cùng thao tác phát hành nguyên tử.

`/api/cancel` là relay hủy có sẵn theo nguồn. Các endpoint ticket/print/start/relay/test phải được siết xác thực hoặc chỉ loopback trước pha 06; xem SECURITY_SPEC.

## Tình huống kiểm tra giao thức

Snapshot chữ ký sai/min_schema quá mới/asset thiếu không được áp; DB lỗi không để nửa danh mục. Mất ACK phải gửi lại không nhân vé; hai máy cùng serial vẫn tách biệt. Lệnh hết hạn hoặc bị gửi lặp không thực hiện tác dụng mới. Timestamp phải phục hồi đúng ngày địa phương. Máy offline dài ngày nhận contract tương thích hoặc từ chối rõ ràng, không đoán.
