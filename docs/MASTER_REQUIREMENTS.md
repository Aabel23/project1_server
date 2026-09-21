# Yêu cầu tổng thể FlexMix Fleet

> Nguồn: [Kiến trúc đội máy FlexMix](../Kien_Truc_Doi_May.html), đề xuất bản 3 ngày 10/09/2026, tham chiếu `version1.0 @ ce17f05`. Tài liệu này được tách từ HTML; chưa đối chiếu mã nguồn ứng dụng và không xác nhận chức năng đã triển khai. “Yêu cầu” là mục tiêu trong đề xuất, “hiện trạng” là mô tả của nguồn, “đề xuất bổ sung” cần được duyệt. Các điểm chưa chốt nằm trong [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

## Cập nhật từ OWNER — DRAFT, 17/09/2026

DEC-001 (DRAFT): một thực đơn chung cả đội. Override theo điểm chưa được OWNER xác nhận; A-01 chỉ được trả lời phần menu chung.

DEC-002/DEC-003 (DRAFT): chấp nhận mất khóa QR và không có vé liên máy.

DEC-005 (DRAFT): mở cửa 08:00–22:00 mỗi ngày; quản lý cửa hàng nhận cảnh báo; không có người trực ngoài giờ; cảnh báo ngoài giờ “xử lý trong ngày”. Chưa chốt múi giờ, SLA hoặc cách xử lý cảnh báo cuối ngày; không tự chuyển thành ngày làm việc kế tiếp.

DEC-008 (DRAFT): OWNER chọn Python, FastAPI, Pydantic, Uvicorn, MySQL 8, SQLAlchemy, PyMySQL, Alembic, Jinja2, long-poll, Nginx, systemd, pytest và MySQL container cho development. Phiên bản cụ thể và đóng gói còn mở; không suy ra VM, worker/hàng đợi, volume assets hay repo đã được duyệt.

Các DEC được ghi tại [06_decisions.md](06_decisions.md), chưa ACCEPTED và chưa là căn cứ triển khai. Phần nguồn/hiện trạng được giữ để truy nguyên.

## Mục tiêu và phạm vi

Quản lý nhiều máy FlexMix độc lập bằng một Hub: danh mục tập trung, giám sát, tài khoản theo điểm bán, sao lưu, lệnh vận hành và phát hành phần mềm theo vòng. **Hub không nằm trên đường bán hàng, phát hành/nhận vé hoặc pha chế.** Máy mất Hub vẫn sử dụng dữ liệu tại chỗ.

Nền tảng được nguồn mô tả: Raspberry Pi 5, Ubuntu 24.04, MySQL nội bộ `beveragepos`; mỗi máy pha một ly tại một thời điểm, dùng `current_recipe.json`; vé có hạn 24 giờ. MySQL 8 thuộc baseline DEC-008 (DRAFT); vị trí Hub/VM vẫn mở Q-06.

Không thuộc phạm vi hiện tại: cổng thanh toán, ghi nhận tiền mặt, vé dùng liên máy, điều phối khách sang máy rảnh, thay đổi giao thức QR để tăng giới hạn. Không xây dựng cơ chế bán hàng phụ thuộc database trên mây.

## Quy ước và tài liệu liên quan

| Tài liệu | Nội dung |
|---|---|
| [ARCHITECTURE](ARCHITECTURE.md) | Thành phần, luồng dữ liệu, năng lực và suy giảm |
| [DATABASE_SPEC](DATABASE_SPEC.md) | Quyền sở hữu, định danh, lưu trữ và migration |
| [API_PROTOCOL](API_PROTOCOL.md) | Bốn loại gói tin, đồng bộ và lệnh |
| [SECURITY_SPEC](SECURITY_SPEC.md) | Ranh giới tin cậy, khóa, quyền và dữ liệu riêng tư |
| [DEPLOYMENT](DEPLOYMENT.md) | Lộ trình, phát hành, sao lưu và cảnh báo |
| [OPEN_QUESTIONS](OPEN_QUESTIONS.md) | **Sổ theo dõi chuẩn** các câu hỏi chưa quyết định (Q-*), mapping Q-* ↔ D-* |
| [06_decisions](06_decisions.md) | Sổ DEC-*; đã ghi 9 DRAFT, chưa có ACCEPTED |
| [ARCHITECTURE_DECISIONS](ARCHITECTURE_DECISIONS.md) | Ràng buộc C-*, giả định A-*, D-* (đã ánh xạ sang Q-*), truy nguyên REQ-* ↔ C-* |
| [TECH_STACK](TECH_STACK.md) | Baseline OWNER đã trả lời ở DEC-008 (DRAFT); chi tiết Q-24 còn mở |
| [PROJECT_STRUCTURE](PROJECT_STRUCTURE.md) | Cấu trúc repository đề xuất (Q-25) |
| [ARCHITECTURE_REVIEW](../ARCHITECTURE_REVIEW.md) | Review lịch sử trước câu trả lời OWNER |
| [ARCHITECTURE_CONSISTENCY_REVIEW](ARCHITECTURE_CONSISTENCY_REVIEW.md) | Review hiện hành sau OWNER decisions, phát hiện và phần còn mở |

## Yêu cầu và điều kiện nghiệm thu

| ID | Yêu cầu mục tiêu | Điều kiện nghiệm thu |
|---|---|---|
| REQ-01 | Máy hoạt động độc lập với Hub và agent | Ngắt Hub hoặc dừng agent không ngắt bán, in, pha và đăng nhập khi phụ thuộc cục bộ còn hoạt động. DEC-007 (DRAFT): không nhận order khi boot offline chưa sync clock |
| REQ-02 | Hub cấp MID duy nhất, không tái sử dụng | Không thể đăng ký hai máy cùng MID; thanh lý vẫn giữ lịch sử. DEC-009 (DRAFT): miền 1–999999, không tái dùng kể cả thay thế |
| REQ-03 | Mỗi cột chỉ có một chủ ghi | Áp danh mục không ghi đè tồn kho, khe cắm, hiệu chuẩn hoặc `available` |
| REQ-04 | Máy tự gọi ra qua HTTPS/Tailscale | Đồng bộ không cần mở dịch vụ trên Wi-Fi tiệm |
| REQ-05 | Danh mục xuống dạng bản chụp đầy đủ | Kiểm chữ ký, schema, assets; transaction dữ liệu áp nguyên tử hoặc giữ dữ liệu cũ khi lỗi trước commit. Phục hồi sync_menu sau commit còn mở Q-22 |
| REQ-06 | Sự kiện giao ít nhất một lần | Gửi lặp không nhân doanh thu; chỉ tiến mốc sau ACK hợp lệ |
| REQ-07 | Bảo toàn mã đã in trên QR | Không đổi/tái cấp mã nguyên liệu cũ; giữ ánh xạ theo từng máy |
| REQ-08 | Chỉ phát hành món máy pha được | Tiền kiểm ở trình soạn và Hub; loại món thiếu khe, vượt giới hạn QR |
| REQ-09 | Bảo vệ vé đang lưu hành | Theo DEC-006 (DRAFT), recipe được ghim tại thời điểm tạo ticket; recipe mới chỉ áp dụng cho ticket tạo sau khi version mới được publish, không đổi ticket đang tồn tại. C-17 vẫn giữ yêu cầu cửa sổ yên tĩnh cho thay đổi mã nguyên liệu; điều kiện chính xác và quy tắc xóa mềm vẫn mở tại Q-11. Pin recipe không bãi bỏ C-17 hoặc cho phép áp chúng ngay. Quan hệ publish tại Hub với apply tại máy offline và cách lưu recipe chưa chốt. |
| REQ-10 | Không âm thầm đổi giá khách đang xem | `POST /api/ticket` so giá và phiên bản menu; lệch trả 409, xác nhận giá mới trước khi in |
| REQ-11 | Kiểm khả năng bán tại thời điểm phát hành | `INSERT ... SELECT` kiểm `available` và `in_stock`; chưa phải giữ chỗ tồn kho |
| REQ-12 | Phân biệt doanh thu vé và tiền thực thu | DEC-004 (DRAFT): thu tiền lúc in nhãn. Báo cáo used/completed_at chỉ phản ánh vé pha xong, không đủ đại diện tiền thực thu. OWNER chưa chọn schema thanh toán/hoàn tiền hoặc công thức báo cáo thay thế (Q-07, Q-17). |
| REQ-13 | Hạn giờ cổng chờ người | Sau 10 phút không tương tác, hủy an toàn, trả vé, ghi khách bỏ đi; cần chốt xử lý nguyên liệu đã dùng |
| REQ-14 | Có schema ledger và sao lưu khôi phục được | Migration chỉ ghi thành công sau hoàn tất; diễn tập phục hồi trên máy thử |
| REQ-15 | Bản phát hành được ký ngoài Hub | Máy từ chối mã không có chữ ký tin cậy trước khi thực thi |
| REQ-16 | Lệnh có hạn và không gây tác dụng lặp | Lệnh hết hạn bị từ chối; restart/release không chạy khi đang pha |
| REQ-17 | Bí mật máy và ghi chú khách không tự động gom về Hub | Payload vé bỏ `note`; gói chẩn đoán/sao lưu phải có chính sách lọc rõ ràng |
| REQ-18 | Giám sát khả năng bán, không chỉ tiến trình sống | Đủ dữ liệu cho 17 cảnh báo trong DEPLOYMENT; có giờ mở cửa và người nhận |
| REQ-19 | Tài khoản offline và phân quyền theo điểm bán | Tài khoản tiệm khác không được nhân bản nhầm; vai vận hành đội chỉ ở Hub |
| REQ-20 | Mọi thay đổi quản trị có dấu vết | Audit ghi người, thời gian, đối tượng, endpoint, trước/sau; không lộ bí mật |

Truy nguyên từng REQ-* sang ràng buộc C-* nằm tại [ARCHITECTURE_DECISIONS.md §Truy nguyên REQ-* ↔ C-*](ARCHITECTURE_DECISIONS.md).

## Năm điều kiện tiên quyết

1. Tách runtime/hiệu chuẩn/profile khỏi cây mã; phát hành vào thư mục mới và đổi symlink.
2. Bỏ MID nhập tay mặc định 1; Hub cấp phát và kiểm trùng.
3. Đảm bảo đồng bộ thời gian trước khi nhận đơn; agent báo lệch NTP.
4. Thêm `schema_migration` để kiểm tương thích và theo dõi migration.
5. Sao lưu đêm ra ổ khác; khi có agent thì đẩy bản phù hợp lên Hub và diễn tập phục hồi.

Nguồn gọi là “bảy file runtime” nhưng liệt kê tám đường dẫn; không dùng con số đó để bỏ sót file. Chi tiết Q-10.

Điều kiện số 2 cần Hub, trong khi pha 00 của nguồn nói "chưa có Hub"; trình tự này còn mở tại Q-21.

## Thay đổi của bản 3 so với bản 2, theo nguồn

Mục này chép lại nhật ký thay đổi của HTML để biết những điểm nào bản 2 đã bị sửa. Bản 2 không có trong workspace.

| Thay đổi | Lý do nguồn nêu |
|---|---|
| Lỗi chặn từ 3 lên 5 | Thêm "không có bảng ghi phiên bản schema" và "không có bản sao lưu"; cả hai là điều kiện tiên quyết của những lời hứa bản 2 đã viết |
| Lỗi chặn số 1 rộng hơn | Nguồn nói bảy file runtime nằm trong git, không phải hai (số đường dẫn liệt kê là tám, xem Q-10); hệ quả thật là `git pull` trên máy đang bán đã hỏng sẵn, không chỉ "ghi đè hiệu chuẩn" |
| Mục mới: tiền, vé, tồn kho | Bản 2 không hỏi con số doanh thu nghĩa là gì; có một lỗi lệch giá đang tồn tại |
| Mục mới: hợp đồng dữ liệu trên dây | Bốn gói tin, đủ để Hub và agent được viết độc lập |
| Vùng mã 1–24 là tài nguyên khan hiếm | Nguyên liệu bơm thường cũng tiêu số trong vùng đó; bảng ánh xạ phải là bộ cấp phát, không chỉ là bảng tra cứu |
| Sửa: Hub bị chiếm quyền | Bản 2 vừa hứa Hub không chạy được bơm vừa cho Hub lệnh `apply-release`; sửa bằng bản phát hành ký bằng khóa Hub không giữ |
| Sửa: mất thẻ nhớ | "Khôi phục được mọi thứ trừ khóa QR" chỉ đúng sau khi có sao lưu |
| Sửa: `threshold_gram` | Bản 2 xếp vào nhóm máy làm chủ; thực ra là dẫn xuất từ công thức của Hub |
| Bảng tình huống thêm 7 hàng | Sáu hàng không liên quan Hub, là những cách máy hôm nay đã hỏng được |
| Cảnh báo từ 10 lên 17 | Danh sách bản 2 không thấy trường hợp máy khỏe mà tiệm không bán được |
| Bảng quyền sở hữu từ 17 lên 25 dòng | `recipe_action`, `drink_category_mapping`, `deleted_at` và các dòng khác chưa có chủ |

## Ràng buộc nghiệp vụ

- Tối đa 10 bơm và 16 vị trí panel tay mỗi máy theo cấu hình nguồn.
- Mã lựa chọn `boolean`/`percentage` trong 1–24; tối đa 12 lựa chọn/đơn, tối đa 9999 g/chỉ thị.
- Mã 1–24 đã cấp bị giữ vĩnh viễn, kể cả nguyên liệu ngừng dùng. `weight` mới cấp từ 100 trở lên theo đề xuất.
- Phân biệt `published` (Hub), `available` (quầy), `in_stock` (dẫn xuất) và khả năng pha theo khe cắm.
- Tồn kho trừ khi pha xong hoặc xử lý pha hỏng, không đặt chỗ lúc in vé. Kiểm tồn lúc phát hành vẫn chưa loại bỏ hoàn toàn bán quá số nguyên liệu.
- Tắt bán không vô hiệu vé đã in; đổi giá không đổi `price`/`drink_name` đã chụp trong vé.

## Kiểm chứng cần thực hiện khi triển khai

Máy giả dùng MySQL cùng schema, không GPIO: mất ACK rồi gửi lại, hai máy trùng serial, áp snapshot lỗi giữa chừng, schema cũ, lỗi assets, lệch thời gian, vé đổi trạng thái, triển khai theo vòng và rollback. Máy thật: bán offline, claim một vé từ hai nhãn, hiệu chuẩn/khe cắm, chờ người rồi hủy, phục hồi mất điện, tự hoàn tác màn hình, phục hồi sao lưu. Đây là kế hoạch nghiệm thu, chưa phải kết quả thử nghiệm.
