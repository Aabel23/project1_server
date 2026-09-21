# Architectural constraints và quyết định cần chốt

Nguồn: [Kien_Truc_Doi_May.html](../Kien_Truc_Doi_May.html), bản 3 ngày 10/09/2026. Tên mục trong bảng là vị trí truy nguyên trong HTML. Không lấy các đề xuất của bộ Markdown trước làm yêu cầu gốc.

Tài liệu liên quan: [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md) (REQ-*), [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) (sổ theo dõi câu hỏi chuẩn, Q-*), [06_decisions.md](06_decisions.md) (quyết định đã xác nhận), [TECH_STACK.md](TECH_STACK.md), [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md), [ARCHITECTURE_REVIEW.md](../ARCHITECTURE_REVIEW.md).

**REQUIREMENT** = ràng buộc nêu trong nguồn, chưa khẳng định đã thực hiện. **ASSUMPTION** = giả định/khuyến nghị chưa duyệt. **OPEN QUESTION** = quyết định cần câu trả lời. Các quyết định bên dưới chưa có trạng thái “đã chấp thuận”.

## Cập nhật từ OWNER — DRAFT, 17/09/2026

Chỉ ghi câu trả lời thực tế ở DEC-001..DEC-009; các C-* giữ nội dung nguồn và có chú thích DRAFT khi liên quan. D-* là câu hỏi lịch sử; trạng thái và phần thiếu xem OPEN_QUESTIONS. Q-09 chưa rõ nghĩa, không được coi là bác yêu cầu hai người duyệt.

Các DEC được ghi tại [06_decisions.md](06_decisions.md), chưa ACCEPTED và chưa là căn cứ triển khai. Phần nguồn/hiện trạng được giữ để truy nguyên.

## Architectural constraints trích từ nguồn

Mọi dòng C-* trong bảng này mang nhãn **REQUIREMENT**.

| ID | Architectural constraint | Mục nguồn |
|---|---|---|
| C-01 | Hub không bao giờ ở trên đường bán hoặc pha; mất Hub chỉ làm cũ menu và ngừng đồng bộ  **DEC-007 (DRAFT, mapping Q-21 chờ xác nhận): không nhận order khi boot offline chưa sync clock. Đây là điều kiện cục bộ, không đưa Hub lên đường bán và không quy định Hub là nguồn giờ.** | Một nguyên tắc |
| C-02 | Mỗi máy giữ MySQL và thẩm quyền vé tại chỗ; claim là UPDATE nguyên tử, không phân xử từ xa  **DEC-003 (DRAFT): không có vé liên máy.** | Một nguyên tắc; Ai làm chủ cái gì |
| C-03 | Agent là systemd unit riêng; crash agent không làm backend hoặc runner chết theo | Hai luồng, cố ý khác hình dạng |
| C-04 | Máy mở kết nối HTTPS qua Tailscale, mTLS; không mở `:8080` trên Wi-Fi tiệm; SSH bảo trì qua Tailscale | Cái gì đi qua ranh giới; Tin cậy |
| C-05 | MID do Hub cấp duy nhất, không mặc định 1, không tái sử dụng khi thanh lý; lịch sử vé dùng `(machine_id, serial)`  **DEC-009 (DRAFT): MID 1–999999, không tái sử dụng cả khi thay thế.** | Năm lỗi chặn; Một máy, từ lúc lắp tới lúc thanh lý |
| C-06 | Chia chủ sở hữu theo cột: Hub giữ danh mục và `published`; máy giữ tồn kho, GPIO, `available`, vé, hiệu chuẩn; Hub không ghi đè các cột máy | Ai làm chủ cái gì |
| C-07 | `threshold_gram`, `drink.in_stock`, `menu-data.js` là dẫn xuất, tính/dựng lại; không đồng bộ như dữ liệu chủ | Ai làm chủ cái gì |
| C-08 | Đi xuống là snapshot đầy đủ có version, contract, min_schema, chữ ký, assets hash; lọc theo năng lực máy | Hai luồng; Hợp đồng dữ liệu trên dây |
| C-09 | Áp snapshot trong một transaction dữ liệu; `recipe` và `recipe_action` cùng transaction; lỗi giữ thực đơn cũ theo phát biểu nguồn. **Giới hạn đã ghi tại Q-22: transaction chỉ rollback trước commit; lỗi sync_menu sau commit chưa có cơ chế phục hồi được chốt.** | Ai làm chủ cái gì; Hai luồng |
| C-10 | Lỗi đọc theo error_id, vé theo updated_at có overlap; không ghi outbox trên đường bán; Hub ghi lặp vô hại | Hai luồng |
| C-11 | Cursor chỉ tiến khi nhận 200 và ACK đúng cursor_to đã được ghi; giao ít nhất một lần | Hợp đồng dữ liệu trên dây |
| C-12 | Thời gian trên dây là UTC ISO-8601, máy khai timezone; schema thiếu thì từ chối snapshot; contract không xóa/đổi nghĩa trường đang dùng | Hợp đồng dữ liệu trên dây |
| C-13 | Không đổi hoặc tái dùng mã nguyên liệu đã cấp; Hub ánh xạ mã cục bộ sang nguyên liệu chuẩn; nhận máy cũ phải có người duyệt | Vùng tên nguyên liệu; Nhận một máy đang chạy vào đội |
| C-14 | Mã boolean/percentage thuộc 1–24, ≤12 lựa chọn/đơn, ≤9999 g/chỉ thị; cấu hình nguồn có 10 bơm và 16 panel; chỉ một ly đồng thời | Năng lực của một máy; phần mở đầu |
| C-15 | Giữ vùng mã mới 1–24 cho lựa chọn, weight mới từ 100; cấp theo máy và từ chối khi hết mã, không dọn bằng đánh số lại | Năng lực của một máy |
| C-16 | Tiền kiểm khả năng bán ở trình soạn và Hub; không gửi món máy thiếu khe để pha | Năng lực của một máy |
| C-17 | Thay đổi chạm vào mã nguyên liệu chỉ áp trong cửa sổ yên tĩnh bảo vệ vé 24 giờ; giá/tên được chụp vào vé lúc phát hành. Phần công thức và xóa mềm **không** thuộc dòng này, xem A-06. Điều kiện chính xác của cửa sổ còn mở: Q-11  **DEC-006 (DRAFT) chỉ chốt pin recipe, không chốt quy tắc mã nguyên liệu/xóa mềm.** | Vùng tên nguyên liệu (bảng Quy tắc); Tiền, vé, và tồn kho |
| C-18 | Bảo vệ lệch giá bằng giá/phiên bản menu trong yêu cầu phát hành, trả 409 khi lệch; kiểm available/in_stock trong thao tác issue | Tiền, vé, và tồn kho; pha 00b |
| C-19 | Cổng chờ người có timeout 10 phút; hủy và trả vé an toàn; có cancel-current-order vì release-stranded chỉ chạy khi máy rảnh | Cái gì còn chạy khi cái gì hỏng |
| C-20 | QRPROTO_KEY và khóa phiên máy ở tại máy; note không gửi telemetry, chỉ lấy có chủ đích qua diagnostics  **DEC-002 (DRAFT): chấp nhận mất khóa QR; backup/note vẫn mở Q-16.** | Ai làm chủ cái gì; Tin cậy; Ghi chú của khách |
| C-21 | Tài khoản PBKDF2 nhân bản theo điểm bán, offline login; sessions_valid_from theo đồng bộ; vai vận hành đội chỉ ở Hub | Tin cậy |
| C-22 | Lệnh có ID, người phát, hạn dùng, ACK; lặp phải an toàn, hết hạn phải từ chối; restart/release chỉ khi rảnh | Các lệnh, và những lệnh phải từ chối |
| C-23 | Test phần cứng luôn cần chế độ thử tại máy; display mode phải hợp lệ và giữ tự hoàn tác 20 giây; siết API cục bộ trước pha 06 | Tin cậy; Các lệnh |
| C-24 | Release ký bằng khóa Hub không giữ; agent kiểm trước thực thi; Hub chỉ chọn bản đã ký | Tin cậy |
| C-25 | Runtime/profile/hiệu chuẩn tách khỏi cây git; checkout tag vào thư mục mới và đổi symlink; giữ nền tảng deploy/install.sh | Năm lỗi chặn; Đưa phần mềm xuống các tiệm |
| C-26 | Có schema_migration, sao lưu trước migration; lùi mã trên schema đã migrate nên migration phải tương thích mã cũ | Năm lỗi chặn; Đưa phần mềm xuống các tiệm |
| C-27 | Backup đêm ra ổ khác, giữ 7 bản; backup trước migration giữ 3; Hub giữ N bản và cảnh báo backup >36 giờ; diễn tập restore | Năm lỗi chặn; Đưa phần mềm xuống các tiệm |
| C-28 | Phát hành vòng máy thử → điểm bán → toàn đội, có cổng sức khỏe; có rollback catalogue riêng và chỉ đến snapshot từng áp thành công | Đưa phần mềm xuống các tiệm; Các lệnh |
| C-29 | Đồng bộ thời gian trước nhận đơn, báo lệch NTP; giám sát phải đo khả năng bán, có 17 cảnh báo và audit thao tác  **DEC-005 (DRAFT) ghi giờ và người nhận; DEC-007 (DRAFT) ghi điều kiện boot.** | Năm lỗi chặn; Cảnh báo gì; Nhật ký thao tác |
| C-30 | Không dùng MySQL replication hay máy client mỏng, không QR key chung, không gom hiệu chuẩn dùng chung | Những hướng không chọn |

**REQUIREMENT — Ranh giới ý nghĩa dữ liệu từ nguồn:** hiện trạng không có thanh toán trong phần mềm; báo cáo “doanh thu” tính vé `used` theo `completed_at`. Vé không giữ chỗ tồn kho. Đây là giới hạn phải phản ánh đúng trong kiến trúc Hub, không phải yêu cầu xây thêm thanh toán hoặc reservation.

## Truy nguyên REQ-* ↔ C-*

Bảng chỉ ghi các cặp đối chiếu được trực tiếp từ văn bản. "Một phần" nghĩa là hai bên cùng nói về một chủ đề nhưng phạm vi không trùng khớp. REQ-* nằm tại [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md).

| REQ-* | C-* | Mức |
|---|---|---|
| REQ-01 | C-01, C-03 | Trực tiếp |
| REQ-02 | C-05 | Trực tiếp |
| REQ-03 | C-06, C-07 | Trực tiếp |
| REQ-04 | C-04 | Trực tiếp |
| REQ-05 | C-08, C-09, C-12 | Trực tiếp |
| REQ-06 | C-10, C-11 | Trực tiếp |
| REQ-07 | C-13, C-15 | Trực tiếp |
| REQ-08 | C-14, C-16 | Trực tiếp |
| REQ-09 | C-17 (mã nguyên liệu); A-06 (khuyến nghị nguồn); DEC-006 DRAFT (pin recipe); xóa mềm vẫn mở | Trực tiếp với nguồn; cập nhật DRAFT |
| REQ-10 | C-18 | Trực tiếp |
| REQ-11 | C-18 | Trực tiếp |
| REQ-12 | Đoạn REQUIREMENT không đánh số "Ranh giới ý nghĩa dữ liệu" ở trên | Trực tiếp |
| REQ-13 | C-19 | Trực tiếp |
| REQ-14 | C-26, C-27 | Trực tiếp |
| REQ-15 | C-24 | Trực tiếp |
| REQ-16 | C-22 | Trực tiếp |
| REQ-17 | C-20 | Một phần: REQ-17 nêu thêm chính sách lọc gói chẩn đoán/sao lưu |
| REQ-18 | C-29 | Một phần: C-29 còn gồm đồng bộ thời gian và audit |
| REQ-19 | C-21 | Trực tiếp |
| REQ-20 | C-29 | Một phần: C-29 chỉ nói "audit thao tác" |

C-* không có REQ-* tương ứng: C-02, C-23, C-25, C-28, C-30. Trong số đó C-25 trùng với điều kiện tiên quyết số 1 của MASTER_REQUIREMENTS.md; C-05, C-26, C-27, C-29 cũng trùng một phần với điều kiện tiên quyết số 2, 4, 5, 3.

## ASSUMPTION dùng để đề xuất kiến trúc Hub

| ID | Giả định/đề xuất chưa duyệt | Căn cứ |
|---|---|---|
| A-01 | Một danh mục chuẩn, ghi đè giá/trạng thái theo điểm bán; capability lọc theo máy  **DEC-001 (DRAFT) chọn menu chung; override chưa được xác nhận.** | Chính nguồn ghi là giả định ở câu hỏi 01; `published` vẫn tách `available` |
| A-02 | Hub trên một VM với MySQL 8  **DEC-008 (DRAFT) chọn MySQL 8; VM chưa được chọn.** | Khuyến nghị ở câu hỏi 06 |
| A-03 | Python/FastAPI, module trong một ứng dụng, worker cùng codebase, MySQL giữ hàng đợi  **DEC-008 (DRAFT) chọn Python/FastAPI; module/worker/hàng đợi còn là giả định.** | Đề xuất trong TECH_STACK, không có tên framework trong nguồn |
| A-04 | Long-poll để giao lệnh; UI render server; assets trên volume  **DEC-008 (DRAFT) chọn long-poll/Jinja2; volume assets còn là giả định.** | Lựa chọn tối thiểu trong các cơ chế nguồn cho phép |
| A-05 | Repo này chứa Hub và hợp đồng giao tiếp; repo máy hiện hữu giữ backend/agent/installer | Đề xuất tổ chức mã, nguồn không bắt buộc mono/multi-repo |
| A-06 | Thay đổi công thức, và rút món (`drink.deleted_at`), được giữ lại và chỉ áp trong cửa sổ yên tĩnh  **Khuyến nghị lịch sử: DEC-006 (DRAFT) chọn pin recipe thay cho chờ yên tĩnh đối với công thức; xóa mềm chưa được OWNER chọn.** | Nguồn nêu **ba phương án** cho thay đổi công thức (Chấp nhận / Ghim công thức vào vé / Áp lúc yên tĩnh) và ghi "tôi khuyên cách thứ ba". Luồng đi xuống và pha 04 của nguồn dùng phương án này. Với `deleted_at`, nguồn viết "phải đi qua cùng một cửa sổ yên tĩnh" như công thức, nên nó đi theo cùng lựa chọn. Tách khỏi C-17 để đúng quy ước nhãn; chưa được duyệt. Câu hỏi: Q-11 |

## OPEN QUESTION — quyết định nghiệp vụ nguồn hỏi trực tiếp

> **Sổ theo dõi chuẩn là [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).** Các `D-*` dưới đây được giữ nguyên để truy nguyên; cột Q-* chỉ ra câu hỏi đang được theo dõi. Khi trả lời, ghi quyết định vào [06_decisions.md](06_decisions.md) theo `Q-*`, không theo `D-*`.

| ID | Quyết định cần chốt | Tác động kiến trúc | Q-* |
|---|---|---|---|
| D-01 | Menu chung hay riêng từng điểm?  **DEC-001 DRAFT; còn override.** | Mô hình catalogue, override, snapshot | Q-01 |
| D-02 | Số máy và địa bàn vận hành? | Sizing VM, số worker, mức cần thiết của pha 06 | Q-02 |
| D-03 | Máy có cùng GPIO và nguyên liệu tại từng khe không? | Profile, ánh xạ và capability | Q-03 |
| D-04 | Khóa QR chấp nhận mất, cất ngoại tuyến hay ký gửi Hub?  **DEC-002 DRAFT.** | Ký gửi Hub thay đổi ranh giới C-20, cần quyết định thay thế rõ ràng | Q-04 |
| D-05 | Có vé liên máy không?  **DEC-003 DRAFT.** | Nếu có phải thiết kế riêng thẩm quyền vé/QR, không tự đưa vào baseline | Q-05 |
| D-06 | Hub đặt ở đâu và có đồng ý VM/MySQL 8 không? | Stack, lưu trữ và vận hành | Q-06 |
| D-07 | Thu tiền khi in nhãn hay giao ly?  **DEC-004 DRAFT; còn mô hình báo cáo.** | Cách diễn giải doanh thu/unused/expired, không tự sinh module thanh toán | Q-07 |
| D-08 | Giờ mở cửa và người trực cảnh báo là ai?  **DEC-005 DRAFT; còn múi giờ/cách xử lý cuối ngày.** | Điều kiện cảnh báo không bán được và mức khẩn cấp | Q-08 |
| D-09 | Ai được đổi giá/công thức; cần hai người duyệt không?  **“không” chưa rõ nghĩa; không tạo DEC.** | Phân quyền và quy trình xuất bản catalogue | Q-09 |

## OPEN QUESTION — chi tiết nguồn chưa đủ để triển khai

| ID | Quyết định hoặc bất nhất cần giải | Ràng buộc liên quan | Q-* |
|---|---|---|---|
| D-10 | Chấp thuận stack A-03/A-04, phiên bản được hỗ trợ và cách đóng gói Hub?  **DEC-008 DRAFT; còn phiên bản/đóng gói.** | C-01, C-04; TECH_STACK | Q-24 |
| D-11 | Monorepo hay Hub repo riêng; agent nằm đâu, ai sở hữu contract? | C-03, C-12; PROJECT_STRUCTURE | Q-25 |
| D-12 | machine_id trên dây là MID hay UUID; ánh xạ sang khóa thiết bị thế nào? | C-05 | Q-12 |
| D-13 | Kết hợp mTLS/Ed25519, ký snapshot, chống replay và vòng đời khóa thế nào? | C-04, C-08, C-20, C-24 | Q-15, Q-26 |
| D-14 | Cửa sổ an toàn là hết unused hay còn chờ 24 giờ sau nhãn cuối? Ngăn issue/claim đồng thời thế nào?  **DEC-006 DRAFT; còn mã nguyên liệu/xóa mềm/nguyên tử.** | C-17; nguồn có hai cách diễn đạt khác nhau | Q-11 |
| D-15 | Định dạng cursor, overlap, phân trang cùng timestamp, ACK một phần, chống bản cũ ghi đè vé mới? | C-10, C-11 | Q-14 |
| D-16 | Danh sách/thứ tự migration và cách so min_schema; phục hồi migration DDL dở dang? | C-12, C-26 | Q-23, Q-15 |
| D-17 | mysqldump chứa note nhưng note không được gom Hub: gói backup được gửi chứa gì? N, dung lượng, quyền đọc và mục tiêu phục hồi? | C-20, C-27 | Q-16 |
| D-18 | Xử lý xung đột drink/SKU/glass khi nhận máy cũ; giữ công thức cho vé còn hiệu lực khi lọc món khỏi snapshot? | C-13, C-16, C-17 | Q-13, Q-18 |
| D-19 | Version khi rollback catalogue là version cũ hay bản mới; lỗi sync_menu sau commit phục hồi thế nào? | C-07, C-09, C-28 | Q-18, Q-22 |
| D-20 | Long-poll hay WebSocket; endpoint lệnh/ACK, timeout, batch, retry và lưu kết quả lệnh để chống lặp?  **Long-poll có DEC-008 DRAFT; các phần khác vẫn mở.** | C-11, C-22 | Q-20, Q-15 (M-01) |
| D-21 | Cổng sức khỏe và thời gian giữ mỗi vòng; chính sách chọn lại release cũ đã ký? | C-24, C-28 | Q-20, Q-19 |
| D-22 | API máy chỉ loopback hay token; hủy sau khi đã rót xử lý vé/tồn thế nào? | C-19, C-23 | Q-19, Q-20 |
| D-23 | “Chưa từng quét” đo thế nào khi vé claim rồi hủy lại unused; heartbeat bổ sung dữ liệu nào để đủ 17 cảnh báo? | C-29 | Q-17, Q-23 |
| D-24 | Boot offline sau mất điện lấy giờ tin cậy ở đâu; backup/restore máy mới MID mới xử lý vé và khóa cũ thế nào?  **DEC-007 DRAFT chỉ điều kiện boot, nguồn ô Q-22; mapping Q-21 chờ xác nhận, phần còn lại vẫn mở.** | C-05, C-17, C-27, C-29 | Q-21, Q-16 |
| D-25 | Nguồn nói 7 file runtime nhưng nêu 8 đường dẫn; phần nào của machine.py là mã, phần nào là profile? Pha 00 chưa có Hub nhưng MID do Hub cấp ở pha 01? | C-05, C-25; cần đối chiếu repo máy | Q-10, Q-21 |

**OPEN QUESTION —** Nguồn vừa cho Hub nhiều lệnh vừa mô tả thiệt hại Hub bị chiếm quyền chủ yếu là đổi menu/giá. Cần xác nhận phạm vi quyền thực tế khi chốt D-09/D-21/D-22: chữ ký release không tự ngăn lạm dụng lệnh hợp lệ hoặc quay về mã cũ đã ký. Theo dõi tại Q-19.

**Quy trình ghi quyết định —** Quyết định được ghi tại [06_decisions.md](06_decisions.md) dưới ID `DEC-*`, trả lời `Q-*` và ghi kèm `D-*`, `C-*`, `A-*` bị ảnh hưởng. Các dòng `D-*`, `C-*`, `A-*` trong file này không bị xóa hay đổi nhãn im lặng; khi có quyết định, ghi `DEC-*` tại dòng liên quan. Hiện chưa có mục nào được duyệt.
