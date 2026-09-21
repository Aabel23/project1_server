# Kiểm tra consistency sau câu trả lời OWNER

Ngày ghi: 17/09/2026. Chỉ rà soát tài liệu; không viết code hoặc xác nhận implementation.

**Kết quả review lại:** đã sửa các sai lệch biên tập nêu ở §Review lại toàn bộ documentation bên dưới. Chưa thể kết luận thiết kế không còn contradiction: các xung đột/khoảng trống phụ thuộc OWNER vẫn OPEN. Các mục phía trên phần review lại ghi nhận đợt apply trước đó.

## Nguồn và giới hạn

Đã đọc toàn bộ DECISION_QUESTIONNAIRE.md, 06_decisions.md, OPEN_QUESTIONS.md và các specification trong docs/. File docs/ARCHITECTURE_CONSISTENCY_REVIEW.md không tồn tại lúc bắt đầu; bản review có sẵn là [ARCHITECTURE_REVIEW.md](../ARCHITECTURE_REVIEW.md), đã đọc đầy đủ. File này là báo cáo mới, không phải bản review đầu vào bị thay thế. HTML và bản review cũ giữ vai trò nguồn lịch sử; quyết định mới chỉ lấy từ ô OWNER.

## DEC và tình trạng Q

Tạo DEC-001..DEC-009, tất cả DRAFT; không có ACCEPTED, REJECTED hay DEFERRED. Giữ nguyên quy ước: PARTIAL/DECIDED của Q đòi DEC ACCEPTED. Vì vậy Q-01..Q-31 vẫn OPEN về phê duyệt; sổ trạng thái đã thêm mức độ câu trả lời và DEC tương ứng, không giả vờ đóng Q.

| DEC (DRAFT) | Q | Nội dung OWNER đã trả lời |
|---|---|---|
| DEC-001 | Q-01 | Thực đơn chung cả đội; override chưa được xác nhận |
| DEC-002 | Q-04 | Chấp nhận mất khóa QR; đủ câu trả lời lựa chọn |
| DEC-003 | Q-05 | Không vé liên máy; đủ câu trả lời lựa chọn |
| DEC-004 | Q-07 | Thu tiền lúc in nhãn; mô hình báo cáo chưa chốt |
| DEC-005 | Q-08 | 08:00–22:00 mỗi ngày, quản lý nhận, không trực ngoài giờ, ngoài giờ xử lý trong ngày |
| DEC-006 | Q-11 | Pin recipe tại tạo ticket; không đổi recipe ticket hiện hữu |
| DEC-007 | Q-21 | Không nhận order khi boot offline chưa sync clock; nguồn nằm ở ô Q-22 |
| DEC-008 | Q-24 | Danh sách baseline công nghệ OWNER nêu, không mở rộng sang mọi giả định hạ tầng |
| DEC-009 | Q-27 | MID nguyên dương 1–999999, không tái dùng cả khi thay thế |

Q chưa có quyết định rõ để tạo DEC: Q-02, Q-03, Q-06, Q-09, Q-10, Q-12, Q-13, Q-14, Q-15, Q-16, Q-17, Q-18, Q-19, Q-20, Q-22, Q-23, Q-25, Q-26, Q-28, Q-29, Q-30, Q-31. Q-09 có câu trả lời mơ hồ; Q-22 có câu trả lời khác chủ đề. M-01..M-06 vẫn mở, không tự chọn ranh giới.

## Đối chiếu các tài liệu bị ảnh hưởng

- Menu chung thống nhất trong ARCHITECTURE, DATABASE_SPEC, API_PROTOCOL, MASTER_REQUIREMENTS và A-01; không duyệt ngầm override.
- Chấp nhận mất QR thống nhất trong SECURITY_SPEC, DEPLOYMENT, DATABASE_SPEC và C-20; ký gửi không được ghi là lựa chọn đang chọn.
- Không vé liên máy giữ thẩm quyền order_ticket tại máy (C-02).
- Thu tiền lúc in nhãn được tách khỏi thống kê used/completed_at; không tự tạo payment/refund/reservation.
- Giờ và người nhận cảnh báo thống nhất; bảng ngưỡng nguồn không hứa trực ngoài giờ.
- Pin recipe thay khuyến nghị chờ yên tĩnh cho công thức tại REQ-09, A-06, luồng snapshot/API, dữ liệu và pha 04; xóa mềm/mã nguyên liệu vẫn mở.
- Điều kiện boot được ghi ở REQ-01, C-01/C-29, API, SECURITY và DEPLOYMENT; ma trận suy giảm giữ nhãn hiện trạng nguồn, không ghi như bảo đảm bán vô điều kiện.
- Stack và long-poll thống nhất ở TECH_STACK, PROJECT_STRUCTURE, API, DEPLOYMENT và A-02/A-03/A-04. Chỉ công nghệ OWNER liệt kê có DRAFT.
- Miền MID thống nhất ở REQ-02, C-05, DATABASE_SPEC, API, SECURITY và DEPLOYMENT; không suy ra machine_id là MID.
- Sửa tham chiếu nhầm A-06→A-01 tại câu hỏi menu trong questionnaire; giữ nguyên các ô OWNER.

## Contradiction và khoảng trống còn lại

| Chủ đề | Phần chưa thể kết luận | Theo dõi |
|---|---|---|
| Q-09 | “không” không rõ phủ định quyền đổi từ xa hay hai người duyệt | Q-09 OPEN, không DEC |
| Sai vị trí trả lời | Boot nằm dưới Q-22; mapping DEC-007→Q-21 chờ xác nhận; sync_menu chưa có đáp án | Q-21, Q-22 |
| Pin recipe và offline | OWNER nói sau publish; chưa định nghĩa ticket tại máy chưa nhận version đó, cách giữ recipe, nguyên tử và migration | Q-11, Q-18, Q-23 |
| Cửa sổ yên tĩnh | Hai cách diễn đạt nguồn chưa thống nhất cho mã nguyên liệu; xóa mềm chưa được trả lời | Q-11 |
| Cảnh báo ngoài giờ | Không trực nhưng “xử lý trong ngày”; chưa rõ mốc cuối ngày, múi giờ, SLA | Q-08 |
| Báo cáo tiền | Thu lúc in nhưng báo cáo nguồn dùng used/completed_at; chưa có mô hình thay thế | Q-07, Q-17 |
| Backup và note | Dump đầy đủ có note, trong khi telemetry loại note; mã hóa/ACL/retention vẫn chưa quyết | Q-16 |
| Phạm vi quyền Hub | Chữ ký release không chặn lạm dụng lệnh hợp lệ/downgrade; khóa snapshot và audit chưa chốt | Q-19, Q-26, Q-30 |
| Pha 00/01 | Pha 00 chưa Hub nhưng điều kiện MID đòi Hub ở pha 01 | Q-21 |
| Runtime | Nguồn nói bảy file nhưng liệt kê tám đường dẫn; không có repo ứng dụng để xác minh | Q-10 |
| Sau commit / hủy sau rót | Chưa có recovery sync_menu; trả unused sau khi rót chưa giải tồn kho/quyền pha | Q-22, Q-20 |

Các khoảng trống identity, collision SKU, cursor/ACK, cryptography, physical DDL/heartbeat, rollback, snapshot signing, GPIO và mẫu số cảnh báo vẫn giữ OPEN theo sổ; không tự tạo lời giải.

## File thay đổi

Đã sửa: 06_decisions.md, OPEN_QUESTIONS.md, DECISION_QUESTIONNAIRE.md, ARCHITECTURE.md, ARCHITECTURE_DECISIONS.md, MASTER_REQUIREMENTS.md, DATABASE_SPEC.md, API_PROTOCOL.md, SECURITY_SPEC.md, DEPLOYMENT.md, TECH_STACK.md, PROJECT_STRUCTURE.md (đều dưới docs/), cùng ARCHITECTURE_REVIEW.md ở thư mục gốc (chỉ thêm chỉ dẫn bản lịch sử). Tạo mới docs/ARCHITECTURE_CONSISTENCY_REVIEW.md.

## Kiểm tra

Đối chiếu nguyên văn 9 câu trả lời trong DEC với ô nguồn; giữ nguyên 22 ô OWNER của questionnaire. Kiểm tra ID DEC duy nhất, toàn bộ 9 trạng thái là DRAFT, 31 Q đều được giữ và có trạng thái phê duyệt phù hợp; liên kết file Markdown nội bộ tồn tại. Không có thay đổi code, schema chạy được hoặc quyết định ACCEPTED. Không chạy test ứng dụng vì chỉ sửa tài liệu và workspace không có mã ứng dụng.


## Review lại toàn bộ documentation — 17/09/2026

### Kết luận theo sáu tiêu chí

| Tiêu chí | Kết quả review |
|---|---|
| Không tự suy diễn decision | 9/9 phần “Quyết định — nguyên văn OWNER” khớp ô nguồn. Không thêm DEC, phương án, ngày quyết định, lý do hay ACCEPTED. **Ngoại lệ về truy nguyên:** mapping DEC-007→Q-21 là đề nghị của người ghi, không phải phát biểu OWNER; đã làm rõ, chưa coi mapping được xác nhận. |
| Không contradiction giữa file | Đã sửa các điểm diễn đạt/truy nguyên không nhất quán được liệt kê bên dưới. Các mâu thuẫn nguồn và thiết kế chưa đủ thông tin vẫn tồn tại, không thể tự đóng bằng biên tập. |
| DEC truy về Q | 8 DEC trỏ đúng ô cùng Q. DEC-007 giữ nguồn thật Q-22, đề nghị phân loại nội dung về Q-21 và không trả lời sync_menu. Sổ Q và sổ DEC đối chiếu được cả hai vị trí. |
| Architecture invariants | Không phát hiện quyết định OWNER nào cho phép phá các bất biến dưới đây. Đã khôi phục nhắc C-17 tại các đoạn bị rút gọn. Cơ chế để thực hiện các bất biến vẫn có câu hỏi mở; không xác nhận chúng đã được triển khai. |
| Security assumptions | Không có thay đổi bảo mật ngoài lựa chọn mất khóa QR do OWNER trả lời; không gửi QR key/khóa release lên Hub. Chọn Nginx/long-poll không chốt mTLS/Ed25519, proxy trust, snapshot key, ACL hay quyền từ xa. |
| OPEN QUESTION rõ | Giữ 31 Q OPEN về phê duyệt theo quy ước ACCEPTED; 9 Q có DRAFT với mức độ trả lời riêng; M-01..M-06 còn mở. Không biến “Chưa quyết định” hoặc CAN DECIDE LATER thành DEFERRED/giải pháp tạm đã duyệt. |

### Phát hiện đã sửa trong lượt review

| ID | Mức | Bằng chứng trước sửa | Sửa tài liệu, không chọn giải pháp |
|---|---|---|---|
| RV-01 | Trung bình | DEC-001 gọi giả định menu là A-06, trong khi questionnaire đã sửa thành A-01 | Sửa phần bối cảnh DEC-001 về A-01, không sửa lời OWNER |
| RV-02 | Trung bình | §1 sổ DEC nói cứ trả lời một phần là PARTIAL; §2 đòi ACCEPTED. Bảng sổ DEC còn dòng trống cắt header khỏi dữ liệu | Thống nhất PARTIAL cần ACCEPTED; sửa bảng Markdown |
| RV-03 | Cao | REQ-05/C-09 nói lỗi giữ menu cũ không giới hạn, nhưng API/ARCHITECTURE nói không rollback được sau commit | Ghi rõ transaction dữ liệu nguyên tử, lỗi trước commit rollback; Q-22 vẫn giữ recovery sau commit. Không tự chọn retry/version ledger |
| RV-04 | Cao | Các đoạn mới về pin recipe thay toàn bộ đoạn cũ và chỉ nói mã nguyên liệu “còn mở”, làm mờ C-17 | Khôi phục ràng buộc cửa sổ yên tĩnh cho mã nguyên liệu tại các spec; chỉ điều kiện chính xác còn mở, không cho phép pin recipe bỏ ràng buộc đó |
| RV-05 | Cao | Một số nơi nói nội dung “thuộc Q-21” mà không nhắc mapping chưa xác nhận | Ghi rõ mapping biên tập đề nghị tại DEC-007 và nơi diễn giải. Giữ nguyên nguồn ô Q-22; không coi Q-21/Q-22 được đóng |
| RV-06 | Trung bình | TECH_STACK còn gọi long-poll/MySQL 8 chỉ là đề xuất; PROJECT_STRUCTURE nói “ý nghĩa doanh thu đã chốt” | Đồng bộ nhãn DRAFT công nghệ; reporting chỉ chốt thời điểm thu, mô hình báo cáo còn mở |
| RV-07 | Trung bình | Nhãn REQUIREMENT mTLS/Ed25519 dễ bị đọc thành OWNER đã chọn cả hai; vài chỗ viết tắt “khóa ký” | Phân biệt ràng buộc nguồn với Q-15 chưa trả lời; ghi rõ khóa ký release, không tự quyết snapshot key hoặc proxy trust |
| RV-08 | Trung bình | Bảng chủ đề gán Q-27 vào D-12, trái sổ mapping “Không có D”; phần CAN DECIDE LATER dễ bị coi là được hoãn các tiêu chí hoàn thành | Q-27 không có D riêng, D-12 chỉ liên quan identity Q-12; phân loại biểu mẫu không phải quyết định hoãn hoặc duyệt giải pháp tạm |
| RV-09 | Thấp | Index tài liệu chỉ trỏ review cũ; cây docs thiếu questionnaire và review mới | Bổ sung liên kết và cây tài liệu hiện hành |

### Kiểm tra architecture invariants

| Invariant | Đối chiếu và kết quả |
|---|---|
| Hub ngoài đường bán/pha | C-01, REQ-01, ARCHITECTURE: giữ. Điều kiện clock cục bộ của DEC-007 không chỉ định Hub là nguồn giờ. Publish/apply recipe offline vẫn OPEN Q-11. |
| Vé là thẩm quyền tại máy | C-02, DATABASE_SPEC, DEC-003: giữ; Hub chỉ nhận bản sao, không thêm vé liên máy. |
| Một chủ ghi cho mỗi cột | C-06, bảng ownership: giữ. Recipe catalogue của Hub khác recipe ghim trong ticket máy; chưa tự chọn schema. Audit phía Hub còn OPEN Q-30. |
| Agent tách backend; chỉ gọi ra | C-03/C-04, ARCHITECTURE, API: giữ; không mở dịch vụ lên LAN hoặc đưa agent vào thread backend. |
| At-least-once và idempotency | C-10/C-11, API §2: giữ mục tiêu; Q-14 còn thiếu cursor, thứ tự, dedup và retention. Không tuyên bố tính đúng đã được chứng minh. |
| Cursor chỉ tiến sau 200 + ACK khớp | C-11, API §2, DATABASE_SPEC: giữ cả hai điều kiện, không chỉ HTTP 200. |
| MID không tái sử dụng, máy thay thế MID mới | C-05, REQ-02, DEC-009, DEPLOYMENT: giữ; miền mới lấy trực tiếp OWNER, identity và QR vẫn OPEN. |
| Mã nguyên liệu không đổi nghĩa/tái cấp | C-13/C-15/C-17, REQ-07/09: giữ; pin recipe không cho phép đổi mã hay bỏ cửa sổ yên tĩnh. |
| Note không vào telemetry; khóa QR ở máy | C-20, API §2, SECURITY_SPEC: giữ. Backup/diagnostics chưa có policy đầy đủ Q-16, không coi dump là ngoại lệ đã duyệt. |
| Release ký ngoài Hub, verify trước thực thi | C-24, REQ-15, SECURITY_SPEC, DEPLOYMENT: giữ; khóa snapshot không bị suy ra cùng chính sách. |
| Hardware test và chốt bận/rảnh tại máy | C-22/C-23, API commands, SECURITY_SPEC: giữ; không thêm quyền Hub vượt chốt, không chọn cách xác thực API cục bộ. |
| UTC ISO-8601 qua dây | C-12, API: giữ; giờ mở cửa OWNER không tự tạo timezone mặc định. |
| Máy tiếp tục hoạt động khi mất Hub | REQ-01, ma trận nguồn, DEC-007: giữ khi phụ thuộc cục bộ đáp ứng; boot offline chưa sync clock không được coi là bán được vô điều kiện. |
| Transaction, migration và recovery riêng | C-09/C-26, API, DATABASE_SPEC: giữ nguyên tử dữ liệu, không hứa rollback DDL hoặc transaction đã commit; Q-22/Q-23 vẫn mở. |

### Security assumptions được giữ nguyên

- Không chọn loopback-only hay token thay OWNER (Q-19); không diễn giải “không” ở Q-09 thành bỏ duyệt hai người hoặc mở quyền đổi giá/công thức.
- Không chọn canonical bytes, nonce, replay window, mTLS termination, thuật toán chữ ký hoặc vòng đời credential (Q-12/Q-15/Q-26).
- Không chọn mã hóa/ACL/download/restore/retention backup hoặc cho phép đưa note lên Hub (Q-16).
- Không chọn chủ ghi audit Hub/Machine, bảng chung/tách, source field hay tính toàn vẹn bằng chứng (Q-30).
- Không coi chữ ký release đã ngăn downgrade/lạm dụng lệnh hợp lệ (Q-19/Q-20).
- Giữ tài khoản theo điểm, hash PBKDF2 và hiệu lực thu hồi theo lần sync; không hứa thu hồi tức thì khi offline (C-21).

### Phần còn mở sau review

Các mục trong §Contradiction và khoảng trống còn lại vẫn hiệu lực. Bổ sung tại Q-11: recipe cũ đã ghim có thể khác catalogue mới dùng để tính threshold/in_stock/capability; chưa có quy tắc giữ assets/công thức qua rollback/xóa mềm. Đây là khoảng trống thiết kế cần giải cùng Q-18/Q-23, không phải lựa chọn lưu recipe do người review tự thêm.

Không kết luận “không còn contradiction” hoặc “sẵn sàng implementation”: Q-09 mơ hồ, mapping Q-21/Q-22 chưa xác nhận, Q-11 publish/apply/cửa sổ yên tĩnh chưa đầy đủ, Q-16 backup/note và Q-21 pha 00/01 vẫn chưa giải. Những mâu thuẫn này có chủ đề theo dõi rõ, không bị che bằng nhãn DRAFT.

### Phạm vi thay đổi và kiểm tra cuối

Chỉ sửa 13 file Markdown trong docs/: 06_decisions.md, API_PROTOCOL.md, ARCHITECTURE.md, ARCHITECTURE_CONSISTENCY_REVIEW.md, ARCHITECTURE_DECISIONS.md, DATABASE_SPEC.md, DECISION_QUESTIONNAIRE.md, DEPLOYMENT.md, MASTER_REQUIREMENTS.md, OPEN_QUESTIONS.md, PROJECT_STRUCTURE.md, SECURITY_SPEC.md, TECH_STACK.md. Không sửa HTML, bản review lịch sử ở gốc hoặc file code.

Kiểm tra cuối: 22 ô OWNER nguyên vẹn so với đầu lượt review; 9 trích dẫn DEC khớp chính xác ô nguồn, 9 ID duy nhất và DRAFT; 31 Q/30 C/20 REQ/6 A/25 D vẫn đủ; đường dẫn Markdown nội bộ tồn tại. Đây là kiểm tra tài liệu, không phải kiểm thử ứng dụng hoặc chứng minh cơ chế bảo mật đã hoạt động.
