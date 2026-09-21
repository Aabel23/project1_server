# Các câu hỏi và quyết định còn mở

> Nguồn: [Kiến trúc đội máy FlexMix](../Kien_Truc_Doi_May.html), đề xuất bản 3 ngày 10/09/2026, tham chiếu `version1.0 @ ce17f05`. Tài liệu này được tách từ HTML; chưa đối chiếu mã nguồn ứng dụng và không xác nhận chức năng đã triển khai. “Yêu cầu” là mục tiêu trong đề xuất, “hiện trạng” là mô tả của nguồn, “đề xuất bổ sung” cần được duyệt. Các điểm chưa chốt nằm trong [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

**File này là sổ theo dõi chuẩn cho mọi câu hỏi chưa được quyết định.** Quyết định cuối cùng, sau khi chủ sở hữu xác nhận, được ghi tại [06_decisions.md](06_decisions.md). Danh sách `D-*` trong [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) được giữ nguyên để truy nguyên và được ánh xạ sang `Q-*` ở §Mapping bên dưới. Bản review liên quan: [ARCHITECTURE_REVIEW.md](../ARCHITECTURE_REVIEW.md).

Tất cả mục dưới đây chưa có DEC ACCEPTED; 9 câu có DRAFT, phân biệt trong sổ trạng thái. Chín câu đầu là quyết định được nguồn hỏi trực tiếp; Q-10..Q-23 là mâu thuẫn/khoảng trống tìm thấy khi tách đặc tả; Q-24..Q-31 là câu hỏi đã tồn tại ở nơi khác trong bộ tài liệu nhưng trước đây chưa có `Q-*`. Nội dung câu hỏi gốc được giữ để truy nguyên; cập nhật câu trả lời nằm trong sổ trạng thái.

**Đợt 17/09/2026:** giữ quy ước trạng thái trong [06_decisions.md](06_decisions.md): chưa đóng Q nào vì tất cả DEC mới là DRAFT. Q-04/Q-05 đủ câu trả lời lựa chọn; các Q có DRAFT khác còn phần cần làm rõ. Không có DEFERRED. Mô tả nguồn dưới đây phải đọc cùng cập nhật trong sổ trạng thái.

## Quyết định nghiệp vụ từ nguồn

| ID | Cần quyết định | Hướng nguồn khuyến nghị/giả định | Cần chốt trước |
|---|---|---|---|
| Q-01 | Một menu chung hay riêng mỗi điểm? | Danh mục chung, ghi đè giá/trạng thái theo điểm, lọc theo năng lực máy | Schema Hub/pha 03 |
| Q-02 | Bao nhiêu máy, phân bố ở đâu? | Đội nhỏ gần nhau có thể dừng pha 04; phân tán cần pha 06 đầy đủ | Sizing/lộ trình |
| Q-03 | GPIO và nguyên liệu từng khe có giống nhau? | Nếu khác, capability là thành phần lõi | Profile/pha 03 |
| Q-04 | Chấp nhận mất khóa QR hay ký gửi? | Chấp nhận mất; có thể in cất két ngoại tuyến; Hub giữ khóa làm tăng rủi ro | Cài đặt/phục hồi |
| Q-05 | Đặt ở máy này, lấy ở máy khác có cần không? | Không trong thiết kế hiện tại; nếu có cần thiết kế vé/QR liên máy riêng | Chốt phạm vi |
| Q-06 | Hub đặt ở đâu, ai vận hành? | VM và MySQL 8 | Hạ tầng Hub |
| Q-07 | Thu tiền lúc in nhãn hay lúc giao ly? | Báo cáo hiện tại chỉ tính vé đã pha xong | Định nghĩa doanh thu/dashboard |
| Q-08 | Giờ mở cửa từng điểm và ai trực cảnh báo? | Chưa có người trực thì không gắn nhãn gọi ngay | Pha 02 |
| Q-09 | Ai đổi giá/công thức từ xa, có cần hai người duyệt? | Nguồn gợi ý bước duyệt thứ hai | Phân quyền/phát hành danh mục |

## Mâu thuẫn và khoảng trống cần giải quyết

### Q-10 — “Bảy file runtime” nhưng có tám đường dẫn

Mục lỗi chặn liệt kê hai file hiệu chuẩn, hai file cấu hình và bốn file trạng thái. `machine.py` còn là module cần tách cấu hình, không nhất thiết phải bỏ toàn bộ khỏi git. Cần kiểm `git ls-files` trên repository ứng dụng, xác định file runtime thật và layout thay thế. Workspace hiện tại chỉ có HTML nên chưa kiểm chứng được tuyên bố nguồn.

### Q-11 — Cửa sổ yên tĩnh và tính nguyên tử với nhận vé

**Cập nhật review:** pin recipe có DEC-006 DRAFT. C-17 về mã nguyên liệu không bị bãi bỏ. Cần làm rõ recipe đã ghim ảnh hưởng thế nào tới threshold/in_stock dẫn xuất, capability, assets và dữ liệu được giữ sau rollback/xóa mềm; không tự quyết cách lưu hoặc tính lại. Liên quan Q-18/Q-23.

Nguồn vừa nói “không còn vé chưa quét hoặc 24 giờ sau nhãn cuối, lấy mốc đến sau”, vừa nói “không còn unused và máy rảnh, chậm nhất 24 giờ”. Hai quy tắc khác nhau; máy liên tục phát hành vé có thể không bao giờ đạt cửa sổ. Cần định nghĩa vé còn hiệu lực, điều kiện runner/in_progress, cách chặn issue/claim chạy đồng thời, lịch tạm dừng phát hành và phạm vi món bị ảnh hưởng. Xóa mềm và rollback công thức cũng phải theo quy tắc đã chốt.

### Q-12 — MID, UUID và machine_id

Nguồn có cả MID số và UUID thiết bị nhưng dùng `machine_id` trên dây/khóa báo cáo. Chọn biểu diễn chuẩn, ánh xạ credential sang máy, duy nhất MID khi cấp đồng thời và xử lý đăng ký lại/thay thẻ. Không để request tự khai ID của máy khác.

### Q-13 — SKU và nhận danh mục của máy hiện hữu

Ánh xạ ingredient được giải rõ, còn xung đột drink/glass/SKU chưa đủ. Máy sau có cùng ID nhưng món khác phải xử lý thế nào mà vé đang lưu hành vẫn đúng? Quy tắc cấp ID “từ max hiện có” phải nhường quy tắc vùng 1–24 và weight ≥100; cũng cần chốt cách xử lý các mã weight cũ đang chiếm vùng thấp.

### Q-14 — Cursor, thứ tự cập nhật và retention

Cần chốt overlap bao lâu, tie-breaker khi cùng `updated_at`, commit đến muộn, clock nhảy lùi, batch lỗi một phần, lưu cursor bền vững, và chống payload cũ ghi đè vé mới. Khóa dedup audit/error, tần suất gửi, retry/backoff và thời hạn giữ dữ liệu chưa ACK đều thiếu. “Giao ít nhất một lần” chưa tự chứng minh không bỏ sót với cursor thời gian.

### Q-15 — Contract và mật mã trên dây

> Riêng câu "ai giữ khóa ký snapshot" được theo dõi tách tại Q-26. Nội dung dưới đây giữ nguyên.

Chốt version/kiểu trường, schema danh mục và rows, ánh xạ `min_schema` sang migration, đường nhận lệnh/ACK, upload backup/assets/diagnostics, vị trí snapshot tồn/khe. Chốt mTLS kết hợp ký Ed25519 ra sao, canonical bytes, thuật toán snapshot signature, key ID, chống replay, cấp/đổi/thu hồi khóa và chứng thư. Không nhầm khóa snapshot với khóa release ngoại tuyến.

### Q-16 — Backup đầy đủ đối nghịch “note không lên Hub”

> Câu này đã bao gồm mã hóa, ACL và quyền đọc gói backup. Mục NQ-06 của bản review trùng với câu này, không tạo `Q-*` riêng.

`mysqldump` toàn bộ DB có thể chứa note mà telemetry cố loại bỏ. Cần phân biệt backup phục hồi tại chỗ với dữ liệu được gửi Hub, phạm vi diagnostics, mã hóa/ACL/retention và bí mật phải loại bỏ. Giữ bao nhiêu bản N ở Hub, ai có quyền đọc, RPO/RTO bao nhiêu? Restore máy mới MID mới xử lý lịch sử/vé/tài khoản và hiệu chuẩn phần cứng mới thế nào?

### Q-17 — “Chưa từng quét” không đồng nghĩa unused + expired

Vé đã claim rồi hủy hoặc phục hồi mất điện có thể trở về unused. Cần dấu mốc lần quét đầu hoặc lịch sử chuyển trạng thái nếu muốn đo đúng. Chốt mẫu số theo ngày, loại vé còn trong 24 giờ, xử lý in lại, timezone, thất bại do thiếu hàng và pha lỗi. Có cần thanh toán/hoàn tiền/giữ chỗ tồn kho không? Nếu chưa, dashboard phải nói đúng đó là thống kê vé.

### Q-18 — Rollback catalogue và version

Quay về snapshot cũ là ghim version cũ hay phát hành một version mới chứa nội dung cũ? `have`, lịch sử áp, min_schema, asset cache và giới hạn N phải thống nhất. Nếu snapshot mới bỏ món không còn pha được nhưng còn vé của món đó, giữ dữ liệu công thức/tombstone ra sao? Không thể coi thiếu trong snapshot là quyền xóa tùy ý.

### Q-19 — Bán kính thiệt hại của Hub và chốt phần cứng

Chữ ký release chặn mã chưa ký nhưng không chặn downgrade về bản cũ đã ký, giá/công thức gây hại hoặc restart liên tục lúc rảnh. Có cần phiên bản tối thiểu, thu hồi release, giới hạn tham số công thức và phân quyền từng lệnh? Chọn loopback-only hay token cho API cục bộ; chốt quyền OS của agent và đường relay cancel. Câu “Hub chỉ đổi được menu và giá” trong nguồn chưa bao trùm toàn bộ quyền Hub được cấp.

### Q-20 — Cổng sức khỏe, lệnh lặp và lỗi giữa chừng

Chốt chu kỳ beat/poll, timeout lệnh, trạng thái ACK và lưu command ID để không in lại khi mất ACK. Giới hạn diagnostics, thời gian theo dõi mỗi vòng, bộ health check, ngưỡng tự rollback, và xử lý crash giữa side effect và commit kết quả. Khi đổi màn hình từ xa, ai xác nhận trong 20 giây? Khi timeout/hủy sau khi đã rót, hoàn vé và trừ tồn thế nào để tránh pha thêm miễn phí?

### Q-21 — Trình tự lỗi chặn và đồng bộ thời gian

**Cập nhật review:** DEC-007 trích ô Q-22; mapping sang Q-21 là đề nghị biên tập, chưa được OWNER xác nhận. Điều kiện clock không xác định Hub là nguồn giờ, không cho phép thêm phụ thuộc Hub khi bán.

MID qua Hub thuộc pha 01 dù pha 00 mang tên sửa đủ năm lỗi chặn và nói chưa có Hub. Chốt cổng nào thật sự phải hoàn tất trước máy thứ hai. `time-sync.target` cần được kiểm chứng với cấu hình boot thực tế; mất Internet sau mất điện thì cho phép bán ở điều kiện nào, RTC có bắt buộc không? Không thể vừa hứa luôn bán offline từ lúc boot vừa chưa có nguồn giờ tin cậy.

### Q-22 — Tính nguyên tử sau commit và phạm vi audit

> Riêng chủ sở hữu và cách tách khóa của `audit_log` được theo dõi tách tại Q-30. Nội dung dưới đây giữ nguyên.

Nếu DB đã commit mà `sync_menu` thất bại thì không thể gọi rollback transaction cũ. Cần retry/recovery, ghi version nguyên tử và chẩn đoán menu cũ. Khi runtime chuyển khỏi cây mã, các file `current_recipe`/QR/index được nối vào release thế nào? Audit tại máy chưa bao phủ thao tác đổi giá tại Hub; cần audit phía Hub, quy tắc lọc bí mật và giữ lịch sử.

### Q-23 — Schema vật lý và dữ liệu để tính cảnh báo

Chốt DDL Hub, default/backfill `published` và `updated_at`, index, FK, kiểu tiền, schema migration ordering và phục hồi DDL dở dang. Beat nguồn chưa ghi rõ trạng thái MySQL, thời gian không tương tác, thời điểm bật test; cần đủ dữ liệu cho 17 cảnh báo. “Schema tụt lại” được xếp tuần này nhưng snapshot bị chặn có thể cần mức cao hơn theo nghiệp vụ. Số thứ tự câu hỏi giờ mở cửa trong bảng cảnh báo nguồn bị lệch (thực tế là câu 08); dùng Q-08 trong bộ này.

### Q-24 — Chấp thuận stack Hub

Trước đây chỉ có ở D-10 và TECH_STACK.md. Có chấp thuận baseline trong A-03/A-04 (Python, FastAPI, MySQL giữ hàng đợi, long-poll, UI render phía server, assets trên volume) không? Phiên bản cụ thể của Python, MySQL, thư viện và cách đóng gói Hub là gì? Câu này tách khỏi Q-06: Q-06 hỏi Hub đặt ở đâu và ai vận hành, Q-24 hỏi dựng Hub bằng gì.

### Q-25 — Tổ chức repository và quyền sở hữu contract

Trước đây chỉ có ở D-11 và PROJECT_STRUCTURE.md. Monorepo hay repo Hub riêng? Agent nằm ở repo nào? Ai sở hữu và quản lý phiên bản bốn gói tin, và contract được đưa sang repo agent thế nào?

### Q-26 — Ai giữ khóa ký snapshot

Nguồn đặt trường `signature` trong gói bản chụp và yêu cầu agent kiểm chữ ký, nhưng không nói ai ký và bằng khóa nào. Nguồn chỉ phát biểu "Hub không giữ khóa ký" cho **khóa ký bản phát hành**. Invariant đó có áp cho khóa ký snapshot không? Đã được hỏi dạng ngắn tại TECH_STACK.md ("khóa ký snapshot thuộc ai?") và nằm trong phạm vi Q-15/D-13. Nguồn: review SR-01, NQ-01.

### Q-27 — Miền giá trị MID khi Hub cấp phát

Miền 1–999999 trong nguồn là miền của câu hỏi nhập tay trong `install.sh`, cơ chế mà lỗi chặn số 2 yêu cầu bỏ. Nguồn không nêu miền giá trị của MID khi Hub cấp phát, và không nói định dạng payload QR có giới hạn miền đó hay không. Liên quan Q-12/D-12. Nguồn: review PR-01, NQ-02.

### Q-28 — Từ chối món đã rút và cảnh báo "tỉ lệ pha hỏng"

Nguồn yêu cầu món bị rút khỏi thực đơn được trả lời bằng lời từ chối lịch sự và không ghi vào nhật ký sự cố. Nguồn không nói lần từ chối đó có được tính vào mẫu số của cảnh báo "tỉ lệ pha hỏng > 10% trong 20 đơn gần nhất" hay không, và cảnh báo đó tính từ nguồn dữ liệu nào. Nguồn: review MR-04, NQ-03.

### Q-29 — Tiền kiểm cho nguyên liệu PUMP thiếu khai `gpio`

Nguồn nêu hiện trạng: nguyên liệu PUMP chưa khai cột `gpio` làm `export_data.py` ném `ValueError` khi quét, sau khi khách đã trả tiền. Việc 00b ② của nguồn ghi "mọi nguyên liệu PUMP đều có khe". Nguồn không nói "có khe" có bao gồm "đã khai `gpio`" hay không, và kiểm này chạy ở trình soạn, ở Hub, hay cả hai. Nguồn: review MR-03, NQ-04.

### Q-30 — Chủ sở hữu `audit_log` và tách khóa giữa máy với Hub

Bảng sở hữu của nguồn ghi nhật ký thao tác là "Máy ghi, Hub gộp". Bộ tài liệu đề xuất bổ sung audit cho thao tác tại Hub (Q-22). Nếu có audit phía Hub: dùng chung bảng hay tách bảng; khóa và cột nguồn gốc tách thế nào để không có hai bên cùng ghi một dòng; bản nào là bằng chứng khi bản ở máy và bản ở Hub lệch nhau; audit tại Hub có được bảo vệ khỏi người chiếm quyền Hub không? Liên quan Q-14 (khóa dedup audit). Nguồn: review DO-01, SR-03, NQ-05.

### Q-31 — Hiệu lực của danh sách "Đã cân nhắc và loại bỏ"

Nguồn liệt kê 10 hướng đã cân nhắc và loại bỏ, nay chép tại ARCHITECTURE.md §Hướng đã cân nhắc và loại bỏ. Chúng là ràng buộc cho các bản thiết kế sau, hay chỉ là ghi chép lý do của bản 3? Nguồn: review MR-01, NQ-07.

## Quyết định còn chờ xác nhận hoặc trả lời phần thiếu

Các chủ đề dưới đây **không được tự quyết** trong tài liệu hay trong triển khai. Mỗi chủ đề chỉ ra câu hỏi đang theo dõi.

| Chủ đề | Q-* | D-* |
|---|---|---|
| Cửa sổ yên tĩnh | Q-11 (và A-06 trong ARCHITECTURE_DECISIONS.md) | D-14 |
| Khóa QR riêng máy | Q-04 | D-04 |
| Ý nghĩa doanh thu | Q-07, Q-17 | D-07, D-23 |
| Vị trí Hub và stack | Q-06, Q-24 | D-06, D-10 |
| Boot offline và đồng bộ thời gian | Q-21 | D-24 |
| Khóa ký snapshot | Q-26 (trong phạm vi Q-15) | D-13 |
| Mã hóa và quyền truy cập backup | Q-16 | D-17 |
| Chủ sở hữu audit | Q-30 (liên quan Q-22) | — |
| Miền cấp phát MID | Q-27 (liên quan Q-12) | Không có D riêng; D-12 chỉ liên quan Q-12 |
| Vé liên máy | Q-05 | D-05 |

## Mapping

Quy ước cột "Loại":

- **Trùng**: cùng một câu hỏi.
- **D ⊂ Q**: câu `D-*` nằm trong phạm vi rộng hơn của `Q-*`.
- **Tách**: một `D-*` gộp hai câu hỏi, mỗi nửa thuộc một `Q-*`.

Mapping chỉ được ghi khi đối chiếu trực tiếp được từ văn bản hai file. Trường hợp không chắc chắn được liệt kê riêng ở cuối và vẫn là câu hỏi mở.

### Sổ trạng thái Q-* ↔ D-*

| Q-* | Chủ đề | D-* | Loại | Trạng thái phê duyệt | DEC-* | Mức độ câu trả lời / phần còn thiếu |
|---|---|---|---|---|---|---|
| Q-01 | Menu chung hay theo điểm | D-01 | Trùng | OPEN | DEC-001 (DRAFT) | Chốt thực đơn chung; chưa xác nhận override giá/trạng thái theo điểm, không duyệt toàn bộ A-01. |
| Q-02 | Số máy, địa bàn | D-02 | Trùng | OPEN | — | OWNER chưa trả lời. |
| Q-03 | Đi dây giống nhau | D-03 | Trùng | OPEN | — | OWNER chưa trả lời. |
| Q-04 | Khóa QR | D-04 | Trùng | OPEN | DEC-002 (DRAFT) | Đủ câu trả lời lựa chọn mất khóa hay ký gửi. Backup tổng thể vẫn mở tại Q-16. |
| Q-05 | Vé liên máy | D-05 | Trùng | OPEN | DEC-003 (DRAFT) | Đủ câu trả lời về phạm vi vé liên máy. |
| Q-06 | Hub đặt ở đâu, ai vận hành | D-06 | Trùng phần vị trí; xem mapping chưa chắc chắn M-06 | OPEN | — | OWNER chưa trả lời. |
| Q-07 | Thu tiền lúc nào | D-07 | Trùng | OPEN | DEC-004 (DRAFT) | Chốt thời điểm thu tiền; chưa xác nhận mô hình báo cáo thay thế. Không tự thêm schema thanh toán, hoàn tiền hoặc reservation; Q-17 vẫn mở. |
| Q-08 | Giờ mở cửa, người trực | D-08 | Trùng | OPEN | DEC-005 (DRAFT) | Chốt 08:00–22:00 mỗi ngày, quản lý cửa hàng nhận cảnh báo, không trực ngoài giờ, ngoài giờ xử lý trong ngày. Múi giờ và cách xử lý cuối ngày chưa rõ; không tự đổi thành ngày làm việc kế tiếp hoặc đặt SLA. |
| Q-09 | Ai đổi giá/công thức từ xa | D-09 | Trùng | OPEN | — | OWNER chỉ ghi “không”; chưa rõ phủ định quyền đổi từ xa hay hai người duyệt. Không suy diễn, không tạo DEC. |
| Q-10 | Bảy file runtime nhưng tám đường dẫn | D-25 (nửa đầu) | Tách | OPEN | — | Chưa có kết quả xác minh/xác nhận tài liệu. |
| Q-11 | Cửa sổ yên tĩnh | D-14 | D ⊂ Q | OPEN | DEC-006 (DRAFT) | Chốt ghim recipe tại thời điểm tạo ticket, không đổi recipe ticket đang tồn tại. Chưa chốt xóa mềm, mã nguyên liệu, lưu trữ/migration, nguyên tử issue/claim, và publish tại Hub so với apply tại máy offline. |
| Q-12 | MID, UUID, `machine_id` | D-12 | D ⊂ Q | OPEN | — | OWNER ghi “Chưa quyết định”; không tự chuyển DEFERRED. |
| Q-13 | SKU khi nhận máy cũ | D-18 (nửa đầu) | Tách | OPEN | — | OWNER ghi “Chưa quyết định”; không tự chuyển DEFERRED. |
| Q-14 | Cursor, thứ tự, retention | D-15 | D ⊂ Q; xem M-01 | OPEN | — | OWNER ghi “Chưa quyết định”; không tự chuyển DEFERRED. |
| Q-15 | Contract và mật mã | D-13; D-16 (phần so `min_schema`); D-20 (phần endpoint lệnh/ACK) | D ⊂ Q, Tách | OPEN | — | OWNER ghi “Chưa quyết định”; không tự chuyển DEFERRED. |
| Q-16 | Backup và `note` | D-17; D-24 (nửa sau) | D ⊂ Q, Tách | OPEN | — | OWNER ghi “Chưa quyết định”; không tự chuyển DEFERRED. |
| Q-17 | Đo "chưa từng quét" | D-23 (nửa đầu) | Tách | OPEN | — | OWNER chưa trả lời. |
| Q-18 | Rollback catalogue | D-19 (nửa đầu); D-18 (nửa sau) | Tách | OPEN | — | OWNER ghi “Chưa quyết định”; không tự chuyển DEFERRED. |
| Q-19 | Bán kính thiệt hại của Hub | D-21 (nửa sau); D-22 (nửa đầu); OPEN QUESTION không đánh số cuối ARCHITECTURE_DECISIONS.md | Tách | OPEN | — | OWNER ghi “Chưa quyết định”; không tự chuyển DEFERRED. |
| Q-20 | Cổng sức khỏe, lệnh lặp | D-20; D-21 (nửa đầu); D-22 (nửa sau) | Tách; xem M-01 | OPEN | — | OWNER ghi “Chưa quyết định”; không tự chuyển DEFERRED. |
| Q-21 | Trình tự lỗi chặn, thời gian | D-24 (nửa đầu); D-25 (nửa sau) | Tách | OPEN | DEC-007 (DRAFT) | Nội dung trả lời điều kiện boot Q-21 nhưng nằm trong ô Q-22; giữ vị trí nguồn và chờ OWNER xác nhận mapping khi duyệt DRAFT. Q-22 chưa có đáp án sync_menu. RTC, tiêu chí sync clock và trình tự pha 00/01 vẫn mở. |
| Q-22 | Nguyên tử sau commit, audit | D-19 (nửa sau) | Tách | OPEN | — | Ô này trả lời boot offline: DEC-007 cho nội dung Q-21, mapping chờ xác nhận. Chưa trả lời sync_menu/audit. |
| Q-23 | Schema vật lý, dữ liệu cảnh báo | D-16 (thứ tự migration, DDL dở dang); D-23 (nửa sau) | Tách | OPEN | — | OWNER ghi “Chưa quyết định”; không tự chuyển DEFERRED. |
| Q-24 | Stack Hub | D-10 | Trùng | OPEN | DEC-008 (DRAFT) | Chốt đúng danh sách OWNER nêu, gồm MySQL container cho development. Chưa chốt phiên bản cụ thể ngoài dòng MySQL 8, đóng gói, VM, worker, hàng đợi MySQL, volume assets hay repo. Không suy rộng thành duyệt toàn bộ A-02/A-03/A-04. |
| Q-25 | Repository, contract | D-11 | Trùng | OPEN | — | OWNER chưa trả lời. |
| Q-26 | Khóa ký snapshot | trong phạm vi D-13 | D ⊂ Q | OPEN | — | OWNER ghi “Chưa quyết định”; không tự chuyển DEFERRED. |
| Q-27 | Miền MID | — | Không có D | OPEN | DEC-009 (DRAFT) | Chốt MID nguyên dương 1–999999, không tái sử dụng kể cả decommission/thay thế. Chưa xác nhận giới hạn bit/payload QR; chưa trả lời quan hệ định danh Q-12. |
| Q-28 | Từ chối món đã rút và cảnh báo | — | Không có D | OPEN | — | OWNER chưa trả lời. |
| Q-29 | Tiền kiểm `gpio` | — | Không có D | OPEN | — | OWNER chưa trả lời. |
| Q-30 | Chủ sở hữu audit | — | Không có D | OPEN | — | OWNER ghi “Chưa quyết định”; không tự chuyển DEFERRED. |
| Q-31 | Hiệu lực hướng bị loại | — | Không có D | OPEN | — | Chưa có kết quả xác minh/xác nhận tài liệu. |


### D-* → Q-*

| D-* | Q-* |
|---|---|
| D-01..D-09 | Q-01..Q-09, cùng số |
| D-10 | Q-24 |
| D-11 | Q-25 |
| D-12 | Q-12 |
| D-13 | Q-15; phần khóa ký snapshot tại Q-26 |
| D-14 | Q-11 |
| D-15 | Q-14 |
| D-16 | Q-23 (thứ tự, DDL dở dang) + Q-15 (so `min_schema`) |
| D-17 | Q-16 |
| D-18 | Q-13 (xung đột drink/SKU/glass) + Q-18 (giữ công thức cho vé khi món bị lọc) |
| D-19 | Q-18 (version khi rollback) + Q-22 (`sync_menu` lỗi sau commit) |
| D-20 | Q-20 (lưu kết quả lệnh, timeout) + Q-15 (endpoint lệnh/ACK); "batch, retry" xem M-01 |
| D-21 | Q-20 (cổng sức khỏe, thời gian giữ vòng) + Q-19 (chọn lại release cũ đã ký) |
| D-22 | Q-19 (loopback hay token) + Q-20 (hủy sau khi đã rót) |
| D-23 | Q-17 (đo chưa từng quét) + Q-23 (dữ liệu heartbeat cho 17 cảnh báo) |
| D-24 | Q-21 (giờ khi boot offline) + Q-16 (restore máy mới MID mới) |
| D-25 | Q-10 (số file runtime, `machine.py`) + Q-21 (pha 00 và MID ở pha 01) |

### Mục của bản review → Q-*

| Review | Q-* | Ghi chú |
|---|---|---|
| NQ-01 | Q-26 | |
| NQ-02 | Q-27 | |
| NQ-03 | Q-28 | |
| NQ-04 | Q-29 | |
| NQ-05 | Q-30 | |
| NQ-06 | Q-16; phần bán kính thiệt hại thuộc Q-19 | Không tạo Q mới: Q-16 đã hỏi mã hóa, ACL, quyền đọc |
| NQ-07 | Q-31 | |
| CT-01 | Q-11 | Sửa nhãn: A-06 trong ARCHITECTURE_DECISIONS.md |
| PR-02 | Q-12 | Q-12 đã có "Không để request tự khai ID của máy khác" |
| FO-01 | Q-21 | |
| FO-02 | Q-20 | Q-20 đã có câu hỏi hủy sau khi đã rót |
| SR-03 | Q-30 | |

### Câu hỏi cục bộ trong TECH_STACK.md và PROJECT_STRUCTURE.md

| Vị trí | Câu hỏi | Q-* |
|---|---|---|
| TECH_STACK OQ1 | Quy mô, tốc độ events, số người vận hành, nơi đặt Hub | Q-02, Q-06; phần còn lại xem M-02 |
| TECH_STACK OQ2 | Chấp thuận Python/FastAPI/MySQL, UI render server | Q-24 |
| TECH_STACK OQ3 | Long-poll có DEC-008 DRAFT; còn chu kỳ, timeout, batch | Q-15, Q-20; "batch" xem M-01 |
| TECH_STACK OQ4 | mTLS và Ed25519; khóa ký snapshot thuộc ai | Q-15; Q-26 |
| TECH_STACK OQ5 | Dung lượng/retention assets và backup; `note` trong gói gửi Hub | Q-16; phần assets xem M-03 |
| TECH_STACK OQ6 | Phiên bản Python, MySQL, thư viện | Q-24 |
| PROJECT_STRUCTURE OQ1 | Repo Hub riêng hay monorepo | Q-25 |
| PROJECT_STRUCTURE OQ2 | Repo máy ở đâu, đóng gói, test | Xem M-04 |
| PROJECT_STRUCTURE OQ3 | Ai quản lý version contract | Q-25 |
| PROJECT_STRUCTURE OQ4 | UI render server, systemd/Nginx | Q-24 |
| PROJECT_STRUCTURE OQ5 | Module nào chịu trách nhiệm bảng/transaction | Xem M-05 |

### Mapping chưa chắc chắn — vẫn là OPEN QUESTION

Các mục dưới đây **không được đoán**. Chủ sở hữu tài liệu cần xác nhận câu hỏi thuộc `Q-*` nào hay cần `Q-*` riêng.

| ID | Vấn đề mapping |
|---|---|
| M-01 | D-20 có "batch, retry" nằm cùng câu với lệnh/ACK. Văn bản không cho biết đó là batch/retry của **lệnh** (Q-20) hay của **lô sự kiện** (Q-14, vốn có "retry/backoff"). |
| M-02 | TECH_STACK OQ1 hỏi "tốc độ events" và "số người vận hành". Q-02 chỉ hỏi số máy và địa bàn; không `Q-*` nào hỏi trực tiếp hai ý này. |
| M-03 | TECH_STACK OQ5 hỏi dung lượng/retention **assets**. Q-16 chỉ nói về backup; không `Q-*` nào hỏi retention assets. |
| M-04 | PROJECT_STRUCTURE OQ2 hỏi repo máy ở đâu, đóng gói và test hiện có. D-11/Q-25 có "agent nằm đâu" nhưng không hỏi về repo máy nói chung. |
| M-05 | PROJECT_STRUCTURE OQ5 hỏi module nào chịu trách nhiệm bảng/transaction sau khi chốt MID/UUID, menu và wire schema. Không `Q-*` hay `D-*` nào tương ứng. |
| M-06 | Q-06 hỏi thêm "ai vận hành Hub", D-06 không có ý này. D-06 hỏi "có đồng ý VM/MySQL 8 không", ý này cũng giao với D-10/Q-24. Ranh giới giữa Q-06 và Q-24 cần được xác nhận. |

## Cách ghi quyết định

Khi có câu trả lời:

1. Ghi quyết định vào [06_decisions.md](06_decisions.md) theo template ở đó.
2. Cập nhật cột "Trạng thái" và "DEC-*" của `Q-*` trong §Sổ trạng thái. **Không xóa** nội dung câu hỏi.
3. Cập nhật các đặc tả và ID bị ảnh hưởng mà quyết định liệt kê.

Giữ lại lý do quyết định để không biến khuyến nghị chưa duyệt thành hiện trạng đã triển khai.
