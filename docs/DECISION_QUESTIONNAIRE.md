# Decision Questionnaire — Biểu mẫu để OWNER trả lời

> **File này lưu câu hỏi và câu trả lời OWNER.** Các phần phương án/bối cảnh phản ánh thời điểm lập biểu mẫu trước khi ghi DEC; cập nhật hiện hành xem §6 và OPEN_QUESTIONS. Không có phương án nào bị chọn thay OWNER. Khuyến nghị của tác giả nguồn (khi có) được trích nguyên văn và ghi rõ là khuyến nghị, không phải lựa chọn đã chốt.
>
> **Cách dùng:** OWNER điền câu trả lời vào ô "Trả lời của OWNER" dưới mỗi câu hỏi thuộc nhóm 1 (hoặc nhóm 2 khi đã sẵn sàng). Sau đó, người ghi chép chuyển câu trả lời sang [06_decisions.md](06_decisions.md) theo `Q-*`, dùng template `DEC-NNN` đã có ở đó. File này **không tạo `DEC-*`** và không tự cập nhật trạng thái tại [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) — việc đó làm thủ công sau khi quyết định được xác nhận.
>
> Nguồn: [Kien_Truc_Doi_May.html](../Kien_Truc_Doi_May.html), bản 3. Sổ câu hỏi chuẩn: [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md). Ràng buộc/giả định: [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md). Review: [ARCHITECTURE_REVIEW.md](../ARCHITECTURE_REVIEW.md).
>
> **NQ-\* đã được gộp vào Q-\*, không còn tồn tại độc lập.** Bản review dùng ID tạm `NQ-01`..`NQ-07`; khi ghi vào OPEN_QUESTIONS.md chúng được cấp số chính thức: NQ-01→Q-26, NQ-02→Q-27, NQ-03→Q-28, NQ-04→Q-29, NQ-05→Q-30, NQ-06→Q-16 (không tạo Q riêng), NQ-07→Q-31. Bảng phân loại dưới đây dùng số `Q-*` chính thức; không có mục NQ-\* nào bị bỏ sót.
>
> `M-01`..`M-06` (vấn đề mapping Q↔D chưa chắc chắn, tại OPEN_QUESTIONS.md §Mapping chưa chắc chắn) không phải câu hỏi nghiệp vụ cần OWNER quyết định — đó là việc đối chiếu văn bản giữa hai file nội bộ. Không xếp vào ba nhóm dưới đây; xem ghi chú ở §4.

## 0. Tổng quan phân loại

| Nhóm | Số câu | Ý nghĩa |
|---|---|---|
| 1. MUST DECIDE BEFORE IMPLEMENTATION | 22 | Chặn trực tiếp việc viết schema, API contract, auth, sync, offline behavior, ownership, security, backup, hoặc machine registration |
| 2. CAN DECIDE LATER | 7 | Không chặn việc viết các hợp đồng/schema cốt lõi; ảnh hưởng đến sizing, vận hành, hoặc tinh chỉnh sau khi hệ thống đã chạy |
| 3. DOCUMENTATION / NO OWNER DECISION NEEDED | 2 | Cần xác minh mã nguồn hoặc là quyết định về cách dùng tài liệu, không phải lựa chọn kiến trúc/nghiệp vụ |

**Nhóm 1 — MUST DECIDE:** Q-01, Q-04, Q-05, Q-07, Q-08, Q-09, Q-11, Q-12, Q-13, Q-14, Q-15, Q-16, Q-18, Q-19, Q-20, Q-21, Q-22, Q-23, Q-24, Q-26, Q-27, Q-30

**Nhóm 2 — CAN DECIDE LATER:** Q-02, Q-03, Q-06, Q-17, Q-25, Q-28, Q-29

**Nhóm 3 — DOCUMENTATION:** Q-10, Q-31

Thứ tự trình bày trong nhóm 1 theo số Q, không theo mức ưu tiên — mọi câu trong nhóm 1 đều chặn implementation theo cách nào đó; mức độ khẩn cấp tương đối được ghi ở cột "Pha implementation bị block" của từng câu.

---

## 1. MUST DECIDE BEFORE IMPLEMENTATION

### Q-01 — Một thực đơn chung cả đội, hay mỗi điểm bán một thực đơn?

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Nguồn tự nhận đây là câu hỏi "thay đổi mô hình dữ liệu của Hub nhiều hơn mọi thứ khác". Nó quyết định catalogue của Hub là một cây dữ liệu chung với override theo điểm, hay là N cây độc lập theo từng điểm bán. |
| Phần hệ thống bị ảnh hưởng | Database schema (Hub): bảng `drink`/`recipe`/`category` và cách `store_setting` override; API contract: nội dung khối danh mục trong gói Bản chụp (`GET /v1/state`); data ownership: phạm vi ghi của Hub theo điểm bán so với theo đội |
| Phương án đã có trong tài liệu | Chỉ có **một giả định** của tác giả (A-01 trong ARCHITECTURE_DECISIONS.md; A-06 là khuyến nghị cửa sổ yên tĩnh): "một danh mục chung, ghi đè giá và trạng thái bán theo từng điểm, và tập món pha được thì tự tính từ bản đồ khe cắm". Tài liệu không mô tả phương án "mỗi điểm một thực đơn" như một thiết kế đầy đủ. |
| Trade-off tài liệu gốc nêu | Không có so sánh ưu/nhược giữa hai phương án. Nguồn chỉ nói phương án được giả định "thay đổi mô hình dữ liệu của Hub nhiều hơn mọi thứ khác" — tức là chi phí thay đổi cao nếu chọn sai, nhưng không định lượng. |
| Pha implementation bị block | Pha 03 (dựng danh mục chuẩn và schema đối chiếu); ảnh hưởng ngược tới thiết kế bảng của pha 01/02 nếu schema Hub đã bắt đầu dựng sớm |
| Quyết định tối thiểu cần OWNER cung cấp | Chọn: (a) một danh mục chung cho toàn đội với override theo điểm, hay (b) mỗi điểm bán một danh mục độc lập, hay (c) mô hình khác — nếu (c), mô tả ngắn gọn mô hình đó |

**Trả lời của OWNER:**
- Một thực đơn chung cho cho cả đội
---

### Q-04 — Khóa QR: chấp nhận mất, hay ký gửi?

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Quyết định này đổi ranh giới tin cậy của toàn hệ thống: nếu Hub giữ khóa QR của máy, một Hub bị chiếm quyền sẽ lộ khóa của cả đội, khác hẳn thiết kế "Hub bị chiếm quyền chỉ đổi được menu và giá". |
| Phần hệ thống bị ảnh hưởng | Security: ranh giới tin cậy Hub↔máy; database schema: có cần bảng lưu khóa ký gửi ở Hub hay không; machine registration: quy trình lắp đặt (pha 01/02) có bước "in khóa cất két" hay không |
| Phương án đã có trong tài liệu | Ba lựa chọn, nguyên văn từ SECURITY_SPEC.md/nguồn: (a) **Chấp nhận mất** — "đơn giản nhất, an toàn nhất. Mất tối đa một ngày vé của một tiệm." Nguồn ghi là khuyến nghị. (b) **Ký gửi khóa ở Hub** — "khôi phục được, nhưng Hub bị chiếm quyền là lộ khóa của cả đội." (c) **Ký gửi ngoại tuyến** — "in khóa ra giấy lúc cài đặt, cất két. `install.sh` đã in nó ra màn hình kèm cảnh báo — chỉ cần biến việc cất giữ thành thủ tục bắt buộc." |
| Trade-off tài liệu gốc nêu | (a) đơn giản/an toàn nhất nhưng mất toàn bộ vé chưa quét khi mất thẻ nhớ; (b) khôi phục được nhưng "biến ô 'Hub bị chiếm quyền' ở bảng trên từ vàng thành đỏ"; (c) giữ được khả năng khôi phục mà không tăng bán kính thiệt hại của Hub, nhưng cần thủ tục vật lý (két sắt) do con người thực hiện đúng mỗi lần lắp máy |
| Pha implementation bị block | Pha 01 (lắp đặt/cấp phát) — quy trình `install.sh` và cách xử lý khóa lúc cài cần biết trước khi viết cài đặt |
| Quyết định tối thiểu cần OWNER cung cấp | Chọn (a), (b), (c), hoặc phương án khác chưa có trong tài liệu |

**Trả lời của OWNER:**
-Chấp nhận mất

---

### Q-05 — Có bao giờ khách đặt ở máy này rồi lấy ở máy khác không?

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Nếu có, thẩm quyền vé phải chuyển lên Hub — mâu thuẫn trực tiếp với bất biến "order_ticket là thẩm quyền tại máy, không phân xử từ xa" (C-02) đang là nền tảng của toàn bộ thiết kế hiện tại. Đây là câu hỏi phạm vi phải chốt trước khi thiết kế bất kỳ phần nào của mô hình vé. |
| Phần hệ thống bị ảnh hưởng | Data ownership: chủ sở hữu `order_ticket` và cơ chế `claim()`; API contract: có cần thêm gói tin liên máy; authentication: QR có cần "chế độ liên máy" |
| Phương án đã có trong tài liệu | Nguồn chỉ nói: "Không trong thiết kế hiện tại; nếu có, thẩm quyền về vé phải chuyển lên Hub và QR cần chế độ liên máy — việc lớn, thiết kế riêng." Không có thiết kế cụ thể nào cho nhánh "có". |
| Trade-off tài liệu gốc nêu | Nguồn chỉ cảnh báo một hệ quả phụ nếu chọn "có": "mỗi máy chỉ pha được một ly một lúc, nên 'đặt chỗ trước ở máy rảnh nhất' là  một bài toán khác nữa" — tức là chọn "có" còn kéo theo một bài toán con chưa được giải, không phải một thiết kế trọn vẹn. |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho nhánh "có" — chỉ nói cần "thiết kế riêng" |
| Pha implementation bị block | Trước pha 01 — vì câu trả lời "có" sẽ thay đổi bất biến C-02 mà mọi pha sau đều dựa vào |
| Quyết định tối thiểu cần OWNER cung cấp | Có/không cho phép đặt ở máy này lấy ở máy khác. Nếu có: xác nhận đây là hạng mục thiết kế riêng, ngoài phạm vi bộ tài liệu hiện tại |

**Trả lời của OWNER:**
-Không
---

### Q-07 — Khách trả tiền lúc nào: lúc in nhãn, hay lúc nhận ly?

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Quyết định này định nghĩa "doanh thu" nghĩa là gì trong dashboard của Hub, và quyết định "vé phát hành nhưng chưa quét" là chỉ dấu thất thoát tiền hay chỉ là chỉ dấu thiết bị hỏng. |
| Phần hệ thống bị ảnh hưởng | Reporting/database schema: định nghĩa của báo cáo doanh thu; monitoring: ý nghĩa của cảnh báo "vé phát hành nhưng chưa từng quét" (liên quan Q-17); có thể kéo theo yêu cầu mới về giữ chỗ tồn kho hoặc theo dõi thanh toán nếu chọn "lúc in nhãn" |
| Phương án đã có trong tài liệu | Nguồn không liệt kê hai phương án đầy đủ, chỉ nêu hệ quả của mỗi nhánh: "Nếu tiệm thu tiền lúc in nhãn thì mọi nhãn khách bỏ đi là tiền đã thu mà không sổ nào ghi. Nếu thu lúc nhận ly thì con số hiện tại đã đúng, và 'vé phát hành nhưng chưa quét' chỉ là chỉ dấu thiết bị hỏng chứ không phải chỉ dấu thất thoát." |
| Trade-off tài liệu gốc nêu | "Hai câu trả lời dẫn tới hai bảng điều khiển khác nhau." Không có phân tích chi phí kỹ thuật giữa hai nhánh. |
| Pha implementation bị block | Không nằm trong lộ trình 00–06 của nguồn theo tên riêng; ảnh hưởng trực tiếp module `reporting/` (PROJECT_STRUCTURE.md) và mọi dashboard doanh thu — cần chốt trước khi viết `reporting/` |
| Quyết định tối thiểu cần OWNER cung cấp | Chọn: thu tiền lúc in nhãn, hay lúc giao ly, hay thời điểm khác — và xác nhận báo cáo "doanh thu" hiện tại (đếm vé `used`) có phản ánh đúng lựa chọn đó không |

**Trả lời của OWNER:**
- Lúc in nhãn
---

### Q-08 — Giờ mở cửa của mỗi điểm bán, và ai trực khi có cảnh báo?

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Cảnh báo "không bán được gì trong giờ mở cửa" — theo nguồn là "cảnh báo đáng giá nhất trong danh sách" — không tồn tại được nếu Hub không biết giờ mở cửa của từng điểm. Ngoài ra còn một câu hỏi tổ chức chưa trả lời: cảnh báo gọi ngay lúc 21 giờ chủ nhật thì gọi ai. |
| Phần hệ thống bị ảnh hưởng | Database schema: bảng điểm bán (`store_setting`/registry) cần trường giờ mở cửa; monitoring: điều kiện tính cảnh báo và mức độ khẩn cấp (gọi ngay/trong ngày) |
| Phương án đã có trong tài liệu | Không có phương án kỹ thuật để lựa chọn; chỉ có một quy tắc phòng hờ nếu câu hỏi tổ chức chưa có lời giải: "Nếu chưa có người trực thì nguồn yêu cầu hạ mọi thứ xuống 'trong ngày' và nói thật điều đó, thay vì để một mức khẩn cấp mà không ai nhận." |
| Trade-off tài liệu gốc nêu | Không nêu trade-off giữa các phương án; chỉ nêu hậu quả nếu bỏ qua câu hỏi (cảnh báo gọi ngay vô chủ, không ai xử lý). |
| Pha implementation bị block | Pha 02 (agent chỉ đọc, đủ 17 cảnh báo — giờ mở cửa là điều kiện của cổng hoàn thành pha này theo DEPLOYMENT.md) |
| Quyết định tối thiểu cần OWNER cung cấp | Giờ mở cửa của từng điểm bán (hoặc quy tắc suy ra giờ mở cửa); tên/vai trò người trực khi có cảnh báo "gọi ngay"; nếu chưa có người trực, xác nhận hạ toàn bộ cảnh báo xuống mức "trong ngày" |

**Trả lời của OWNER:**
- Giờ mở cửa: 08:00–22:00 mỗi ngày.
- Người nhận cảnh báo: quản lý cửa hàng.
- Ngoài giờ có người trực: không.
- Cảnh báo ngoài giờ: xử lý trong ngày.
---

### Q-09 — Ai được đổi giá/công thức từ xa, và có cần hai người duyệt không?

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Đây là quyết định phân quyền cốt lõi cho vai "người vận hành đội" mới ở Hub — vai này có tự mình đổi giá của cả 30 máy được không. Nguồn cảnh báo: "Một lần gõ nhầm số 0 ở Hub lan ra cả đội trong một phút." |
| Phần hệ thống bị ảnh hưởng | Authentication/authorization: ma trận quyền cho vai vận hành đội; API contract: có cần bước duyệt thứ hai trước khi một snapshot đổi giá được phát hành; data ownership: quyền ghi `drink`/`recipe`/`store_setting` từ Hub |
| Phương án đã có trong tài liệu | Nguồn khuyến nghị "một bước duyệt thứ hai" cho thay đổi chạm vào giá và công thức, nhưng không mô tả cơ chế duyệt cụ thể (ai được là người duyệt thứ hai, quy trình duyệt) — đây là khuyến nghị định hướng, không phải thiết kế đầy đủ. |
| Trade-off tài liệu gốc nêu | "Một lần gõ nhầm số 0 ở Hub lan ra cả đội trong một phút, và lùi bản danh mục sửa được — nhưng chỉ sau khi có người nhận ra." Nguồn không so sánh chi phí vận hành của việc thêm bước duyệt hai người (chậm thao tác) so với lợi ích (giảm rủi ro). |
| Pha implementation bị block | Pha 04 (ai được phát hành snapshot đổi giá/công thức) và pha 05 (phân quyền, vai vận hành đội) |
| Quyết định tối thiểu cần OWNER cung cấp | Danh sách vai/người được đổi giá và công thức từ xa; có bắt buộc hai người duyệt cho thay đổi giá/công thức hay không, và nếu có thì ai là người duyệt thứ hai |

**Trả lời của OWNER:**
- không
---

### Q-11 — Cửa sổ yên tĩnh: điều kiện chính xác để áp thay đổi công thức, mã nguyên liệu, xóa mềm

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Nguồn tự mâu thuẫn: một chỗ nói "không còn vé nào chưa quét **hoặc** 24 giờ sau nhãn cuối, lấy mốc đến sau" (áp cho mã nguyên liệu — đây là quy tắc, không phải khuyến nghị); chỗ khác nói "không còn `unused` **và** máy đang rảnh, chậm nhất 24 giờ" (áp cho công thức — đây là 1 trong 3 phương án được khuyến nghị). Máy liên tục phát hành vé có thể không bao giờ đạt điều kiện thứ hai. |
| Phần hệ thống bị ảnh hưởng | Synchronization: logic áp snapshot xuống máy (luồng đi xuống, bước 3 tại ARCHITECTURE.md); data ownership: bảo vệ vé đang lưu hành (REQ-09); có thể cần cột mới trên `order_ticket` tùy phương án chọn |
| Phương án đã có trong tài liệu | Với **công thức**, nguồn nêu ba phương án đầy đủ: (a) **Chấp nhận** — rẻ nhất, là hành vi hiện tại; hỏng khi có người sửa công thức lúc đông khách. (b) **Ghim công thức vào vé** — đúng nhất, nhưng phải lưu công thức đã biên dịch vào `order_ticket` — cột mới lớn, migration nặng. (c) **Áp lúc yên tĩnh** — không cần đổi schema; chậm nhất 24 giờ vì vé tự hết hạn; nguồn ghi "tôi khuyên cách thứ ba" — đây là khuyến nghị, chưa duyệt. Với **mã nguyên liệu**, quy tắc cửa sổ yên tĩnh (mốc đến sau giữa hết vé chưa quét và 24 giờ) được nguồn phát biểu như một luật, không phải một trong nhiều lựa chọn. |
| Trade-off tài liệu gốc nêu | Xem ba phương án ở trên: (a) rẻ/dễ hỏng, (b) đúng/tốn schema, (c) không tốn schema/chậm nhất 24 giờ. Nguồn không nói quy tắc "hoặc...lấy mốc đến sau" của mã nguyên liệu có áp dụng được cho công thức hay không. |
| Pha implementation bị block | Pha 04 ("công thức và mã nguyên liệu đi sau, qua cửa sổ yên tĩnh" — DEPLOYMENT.md) |
| Quyết định tối thiểu cần OWNER cung cấp | (1) Xác nhận phương án cho thay đổi công thức: (a), (b), hay (c). (2) Xác nhận `drink.deleted_at` đi theo cùng quy tắc với công thức hay với mã nguyên liệu. (3) Điều kiện chính xác: "hết vé chưa quét HOẶC 24 giờ" hay "hết vé unused VÀ máy rảnh" — hay một quy tắc khác |

**Trả lời của OWNER:**
Trả lời của OWNER:

Chọn phương án pin recipe vào ticket.

Recipe của ticket được cố định tại thời điểm tạo ticket.
Recipe mới chỉ áp dụng cho các ticket được tạo sau khi version mới được publish.
Không thay đổi recipe của ticket đang tồn tại.

---

### Q-12 — MID, UUID và `machine_id` trên dây

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Nguồn có cả MID số (do Hub cấp) và UUID thiết bị (trong `fleet.env`), và dùng `machine_id` làm khóa trên dây (`(machine_id, serial)`) và trong mọi gói tin, nhưng không nói `machine_id` chính là MID hay UUID, hay quan hệ giữa chúng là gì. |
| Phần hệ thống bị ảnh hưởng | Database schema: khóa chính của đăng ký máy, khóa `(machine_id, serial)` của vé, khóa `(machine_id, error_id)` của lỗi; API contract: trường `machine_id` trong cả bốn gói tin; machine registration: cấp phát lúc lắp máy; authentication: ánh xạ credential (khóa Ed25519 thiết bị) sang máy |
| Phương án đã có trong tài liệu | Không có. Nguồn chỉ đưa ra một ràng buộc: "Không để request tự khai ID của máy khác" — tức là `machine_id` trên dây phải được đối chiếu với danh tính đã xác thực (khóa Ed25519), nhưng không nói bản thân trường đó là MID hay UUID. |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho việc chọn MID số hay UUID thiết bị làm `machine_id` chuẩn trên dây |
| Pha implementation bị block | Pha 01 (registry, `fleet.env`, MID Hub cấp) — mọi gói tin từ pha 02 trở đi dùng `machine_id` |
| Quyết định tối thiểu cần OWNER cung cấp | Chọn: `machine_id` trên dây là MID số, là UUID thiết bị, hay là một giá trị khác; quy tắc ánh xạ giữa MID, UUID và khóa Ed25519 |

**Trả lời của OWNER:**

- MID là định danh nghiệp vụ do Hub cấp cho Machine.
- MID là duy nhất trong toàn fleet, không tái sử dụng sau khi Machine bị decommission.
- UUID là định danh kỹ thuật duy nhất của instance/device và không dùng thay cho MID.
- machine_id trong database/API tham chiếu tới Machine record của Hub; không tự sinh một identity khác với MID/UUID.
- Credential/key của Machine được gắn với Machine identity cụ thể.
- Khi thay Machine, Machine mới phải được provision với identity và credential mới; không kế thừa identity/credential của Machine cũ.
- Không dùng MID làm secret hoặc credential.
---

### Q-13 — Xung đột ID drink/glass/SKU khi nhận một máy đang chạy vào đội

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Nguồn giải quyết rõ cho `ingredient` (ánh xạ theo máy, không đổi mã cũ) nhưng không giải quyết tương đương cho `drink`/`glass`/SKU. Máy sau có thể có cùng ID với danh mục chuẩn nhưng là món khác — vé đang lưu hành của máy đó phải vẫn đúng. |
| Phần hệ thống bị ảnh hưởng | Data ownership: quy trình đối chiếu danh mục (pha 03); database schema: cấp ID cho `drink`/`glass` khi nhận máy hiện hữu; machine registration: bước đối chiếu có người duyệt |
| Phương án đã có trong tài liệu | Nguồn có quy tắc cho **máy đầu tiên**: "Hub nhận nguyên trạng — mọi id giữ nguyên... Từ đó Hub cấp id mới bắt đầu từ số lớn nhất đang có." Với **máy sau**: "so khớp theo tên, không theo id... Hub dựng một bảng đối chiếu và dừng lại: một người phải xem từng dòng." Nhưng không có quy tắc cho trường hợp hai máy có cùng ID số nhưng là hai món khác nhau về nội dung. |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho xung đột ID cụ thể này (khác món, trùng số) |
| Pha implementation bị block | Pha 03 (đối chiếu danh mục có người duyệt) |
| Quyết định tối thiểu cần OWNER cung cấp | Quy tắc xử lý khi máy được nhận vào đội có `drink_id`/`glass_id` trùng số với danh mục chuẩn nhưng khác nội dung món; cách giữ đúng vé đang lưu hành của máy đó trong lúc đối chiếu |

**Trả lời của OWNER:**
-Chưa quyết định.
Khi onboarding máy hiện có, cần xác định quy tắc
xử lý collision giữa drink_id, glass_id và SKU/ID
của máy với dữ liệu hiện có trên Hub.

---

### Q-14 — Cursor, thứ tự cập nhật và retention của lô sự kiện

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | "Giao ít nhất một lần" chưa tự chứng minh không bỏ sót khi dùng cursor thời gian (`updated_at`) thay vì cursor tuần tự (`error_id`). Cần chốt cách tránh bỏ sót dòng khi có ghi trễ, cách xử lý batch lỗi một phần, và thời hạn giữ dữ liệu chưa được Hub xác nhận. |
| Phần hệ thống bị ảnh hưởng | Synchronization: toàn bộ cơ chế `POST /v1/events`; database (máy): retention của `order_ticket`/`error_log`/`audit_log` chưa gửi; API contract: ngữ nghĩa của `cursor_from`/`cursor_to` |
| Phương án đã có trong tài liệu | Không có phương án cụ thể. Nguồn chỉ nêu yêu cầu tính chất: cursor chỉ tiến sau HTTP 200 và đúng `cursor_to` đã ghi; Hub upsert theo `(machine_id, serial)` nên ghi lặp vô hại. Không có cơ chế overlap/tie-breaker/backoff nào được mô tả. |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho: độ dài overlap khi đọc theo `updated_at`, tie-breaker khi nhiều dòng cùng timestamp, batch lỗi một phần, khóa dedup cho `error`/`audit`, retry/backoff, thời hạn giữ dữ liệu chưa ACK |
| Pha implementation bị block | Pha 02 (agent gửi beat/vé/lỗi/tồn/khe theo cursor) |
| Quyết định tối thiểu cần OWNER cung cấp | Độ dài cửa sổ overlap cho đọc theo `updated_at`; chính sách khi một lô sự kiện lỗi một phần (toàn lô hay từng dòng); thời hạn tối thiểu giữ dữ liệu tại máy trước khi được phép dọn dù đã gửi |

**Trả lời của OWNER:**
-Chưa quyết định.

Cần chốt quy tắc cursor, ACK, duplicate/Idempotency,
partial batch, thứ tự event, retry/backoff và retention
trước khi triển khai event sync.

---

### Q-15 — Contract và mật mã trên dây (không gồm phần khóa ký snapshot — xem Q-26)

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Nguồn mô tả đồng thời "HTTPS qua Tailscale, mTLS" (trong sơ đồ ranh giới) và "Ed25519 ký mọi request" (trong mục Tin cậy), nhưng không mô tả hai cơ chế này phối hợp thế nào: verify ở đâu, canonical bytes là gì, có chống replay không. |
| Phần hệ thống bị ảnh hưởng | API contract: toàn bộ bốn gói tin (Bản chụp, Lô sự kiện, Nhịp tim, Lệnh/ACK) đều phụ thuộc lớp xác thực này; authentication: cách Hub xác nhận một request đến từ đúng máy đã đăng ký; deployment: có dùng Nginx terminate mTLS hay không (nếu có, ứng dụng chỉ tin metadata do proxy chuyển) |
| Phương án đã có trong tài liệu | Không có. TECH_STACK.md chỉ đề xuất Nginx làm reverse proxy có xác minh chứng thư client như một khả năng kỹ thuật, không phải phương án đã chốt cho việc phối hợp mTLS/Ed25519. |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho: cách kết hợp mTLS và chữ ký Ed25519 (một lớp hay cả hai lớp đều bắt buộc), canonicalization của dữ liệu được ký, chống phát lại (replay), quy trình cấp/xoay/thu hồi chứng thư và khóa thiết bị |
| Pha implementation bị block | Pha 01 (fleet.env, cặp khóa Ed25519 thiết bị) và pha 02 (agent bắt đầu gửi request thật) |
| Quyết định tối thiểu cần OWNER cung cấp | mTLS và chữ ký Ed25519 có bắt buộc cả hai hay chỉ một; nếu terminate mTLS tại reverse proxy, ứng dụng Hub có được phép tin metadata do proxy chuyển hay phải tự verify; cơ chế tối thiểu chống replay (ví dụ cửa sổ thời gian cộng nonce, hay cơ chế khác) |

**Trả lời của OWNER:**
Trả lời của OWNER:

- Machine chủ động mở kết nối tới Hub; Hub không yêu cầu Machine mở inbound connection.
- Traffic Hub ↔ Machine sử dụng HTTPS.
- Tailscale được sử dụng để tạo private network và giới hạn đường truy cập bảo trì.
- API bảo trì trên Machine chỉ được expose qua loopback/Tailscale theo ACL được quy định; không expose backend qua Wi-Fi/LAN của tiệm.
- mTLS/Ed25519 được sử dụng cho machine authentication/integrity theo security specification.
- Không sử dụng MID làm credential.
- Request cần có cơ chế chống replay.
- Credential của Machine phải có cơ chế revoke khi decommission.
- Release signing key và snapshot signing key là hai phạm vi riêng; Hub không giữ release private signing key.

---

### Q-16 — Mã hóa, ACL và nội dung gói backup gửi lên Hub

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | `mysqldump` toàn bộ database tại máy chứa `order_ticket.note` (dữ liệu khách tự gõ), trong khi quy tắc telemetry của nguồn nói `note` không bao giờ được gửi lên Hub qua đường sự kiện thường lệ. Nguồn tự nhận: "nguồn chưa giải quyết mâu thuẫn này." |
| Phần hệ thống bị ảnh hưởng | Backup: nội dung gói backup gửi lên Hub; security: mã hóa, ACL, quyền đọc gói backup tại Hub; data ownership: `note` có nằm trong gói backup được phép gửi hay phải lọc ra trước khi gửi |
| Phương án đã có trong tài liệu | Nguồn tách hai bước: (1) sao lưu tại chỗ hằng đêm ra ổ khác — `mysqldump --single-transaction` cộng hiệu chuẩn và profile, giữ 7 bản — không cần chờ Hub, không có tùy chọn khác được nêu. (2) "Khi có agent: đẩy gói đêm đó lên Hub, Hub giữ N bản mỗi máy và cảnh báo khi bản mới nhất quá 36 giờ" — nhưng không nói gói đẩy lên có được lọc `note` hay gửi nguyên trạng. |
| Trade-off tài liệu gốc nêu | Không có trade-off giữa các phương án lọc, vì nguồn không đưa ra phương án lọc nào — chỉ nêu sự tồn tại của mâu thuẫn. |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho: gói gửi Hub có lọc `note`/hash tài khoản hay không, mã hóa gói ở đâu (tại máy hay tại Hub), ai tại Hub được đọc gói backup của một tiệm, N bản giữ ở Hub, RPO/RTO |
| Pha implementation bị block | Pha 02 (agent bắt đầu đẩy "beat/vé/lỗi/tồn/khe/backup" lên Hub theo DEPLOYMENT.md) |
| Quyết định tối thiểu cần OWNER cung cấp | Gói backup gửi lên Hub có được lọc `note` và các trường nhạy cảm khác hay không; nếu không lọc, xác nhận rủi ro này được chấp nhận và ai được đọc gói; N bản giữ tại Hub cho mỗi máy |

**Trả lời của OWNER:**
Chưa quyết định.

Cần chốt:
- Backup có mã hóa hay không và mã hóa ở đâu.
- Ai có quyền truy cập/download/restore backup.
- Backup có chứa order_ticket.note hay không.
- Chính sách retention và bảo vệ backup trên Hub.

---

### Q-18 — Rollback catalogue: version cũ hay bản mới chứa nội dung cũ?

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | "Quay về snapshot cũ" có hai cách hiểu khác nhau về mặt kỹ thuật: ghim lại đúng `version` cũ (rủi ro: Hub có thể lập tức đẩy lại bản mới hơn mà máy vừa từ chối), hay phát hành một `version` mới có nội dung giống bản cũ (rủi ro: `have`/lịch sử áp/`min_schema`/asset cache phải được thiết kế lại cho tình huống này). |
| Phần hệ thống bị ảnh hưởng | Synchronization: ngữ nghĩa của `version` trong gói Bản chụp; API contract: tham số `have` khi máy hỏi lại sau rollback; database: lịch sử áp snapshot, giới hạn N bản giữ |
| Phương án đã có trong tài liệu | Không có phương án kỹ thuật đầy đủ. Nguồn chỉ nêu yêu cầu: "Hub giữ N bản chụp gần nhất và 'quay về 847' là một lệnh, vì thực đơn sai gây thiệt hại nhanh hơn mã sai", và chỉ rollback tới "bản máy từng áp thành công". |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho câu hỏi "ghim version cũ hay phát hành version mới chứa nội dung cũ", và chưa nói cách giữ dữ liệu công thức/tombstone khi một snapshot mới lọc bỏ món mà vé cũ vẫn còn hiệu lực |
| Pha implementation bị block | Pha 04 (snapshot, ghim máy, rollback catalogue) |
| Quyết định tối thiểu cần OWNER cung cấp | Rollback catalogue là ghim lại version cũ, hay phát hành version mới với nội dung cũ; giới hạn N bản snapshot giữ lại tại Hub |

**Trả lời của OWNER:**
Chưa quyết định.

Cần chốt chiến lược rollback catalogue và số lượng
snapshot/version tối thiểu cần giữ để hỗ trợ rollback.
---

### Q-19 — Bán kính thiệt hại của Hub và chốt phần cứng: loopback hay token?

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Chữ ký release chặn mã chưa ký, nhưng không chặn Hub chọn lại một bản cũ đã ký, không chặn giá/công thức gây hại, và không chặn restart liên tục lúc máy rảnh. Câu "Hub chỉ đổi được menu và giá" trong nguồn chưa bao trùm toàn bộ quyền Hub thực tế được cấp. |
| Phần hệ thống bị ảnh hưởng | Security: toàn bộ mô hình quyền của Hub và giới hạn API cục bộ tại máy; authentication: các endpoint `ticket/print/start/relay/test` hiện chưa có xác thực trong ranh giới tailnet |
| Phương án đã có trong tài liệu | Với API cục bộ, nguồn nêu hai lựa chọn: "buộc các endpoint này chỉ nghe loopback... hoặc bắt chúng mang một token của máy." Với việc release cũ đã ký bị chọn lại, và giới hạn tham số công thức/phân quyền từng lệnh, nguồn không đưa cơ chế cụ thể. |
| Trade-off tài liệu gốc nêu | Nguồn không so sánh chi phí giữa loopback-only và token; chỉ nói "trước pha 06" phải chọn một trong hai vì "Thêm Hub là thêm người và thêm máy vào đúng cái vòng tròn đó — Hub, VM của nó, laptop của người vận hành." |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho: phiên bản tối thiểu bắt buộc, cơ chế thu hồi một release đã ký, giới hạn tham số công thức, phân quyền theo từng lệnh |
| Pha implementation bị block | Phải chốt trước pha 06 theo nguồn ("trước pha 06 phải chọn"), nhưng ảnh hưởng thiết kế API cục bộ có thể bắt đầu sớm hơn (pha 01/02) |
| Quyết định tối thiểu cần OWNER cung cấp | Chọn loopback-only hay token riêng của máy cho các endpoint `ticket/print/start/relay/test`; có cần cơ chế thu hồi release đã ký hay giới hạn phiên bản tối thiểu hay không |

**Trả lời của OWNER:**

Chưa quyết định.

Cần chốt:
- Giới hạn quyền của Hub khi Hub bị compromise.
- Cơ chế bảo vệ API trên Machine.
- Chính sách revoke/giới hạn release cũ đã ký.

---

### Q-20 — Cổng sức khỏe, lệnh lặp và xử lý lỗi giữa chừng

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Yêu cầu nguồn là "giao lặp an toàn" cho mọi lệnh, nhưng không có cơ chế lưu trạng thái lệnh bền vững để retry không lặp lại tác dụng phụ (ví dụ in lại vé, hủy đơn) khi crash xảy ra giữa lúc thực thi và lúc ghi kết quả. |
| Phần hệ thống bị ảnh hưởng | API contract: envelope lệnh/ACK (`POST` hoặc kênh long-poll/WebSocket) trong gói Lệnh; database: có cần bảng lưu trạng thái thực thi lệnh; synchronization: rollout theo vòng (cổng sức khỏe, thời gian theo dõi) |
| Phương án đã có trong tài liệu | Không có phương án lưu trữ cụ thể. Nguồn chỉ nêu yêu cầu tính chất: lệnh có ID, ACK có `accepted/refused/done/failed`, và "đề xuất bổ sung: lưu command ID/trạng thái bền vững trước và sau thực thi" (chưa được duyệt, chỉ là đề xuất). |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho: chu kỳ beat/poll, timeout lệnh, bộ health check cụ thể cho rollout theo vòng, ngưỡng tự rollback, và cơ chế khôi phục khi crash giữa side effect và ghi kết quả |
| Pha implementation bị block | Pha 06 (lệnh, chẩn đoán, release theo vòng) — nhưng envelope lệnh cơ bản (id/kind/args/issued_by/issued_at/expires_at) đã được dùng từ các lệnh đơn giản hơn (`sync-now`) có thể sớm hơn |
| Quyết định tối thiểu cần OWNER cung cấp | Cơ chế lưu trạng thái lệnh tối thiểu để chống lặp tác dụng phụ (có bảng riêng hay dùng cơ chế khác); bộ tiêu chí health check tối thiểu và thời gian theo dõi mỗi vòng trước khi mở vòng tiếp theo |

**Trả lời của OWNER:**
Chưa quyết định.

Cần chốt durability, health/timeout, retry,
duplicate handling và crash recovery của command.
---

### Q-21 — Trình tự lỗi chặn và đồng bộ thời gian khi boot offline

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Nguồn tự mâu thuẫn: nguyên tắc nền nói máy luôn bán được khi mất Hub/mất mạng, nhưng lỗi chặn thứ ba yêu cầu đồng bộ giờ **trước khi nhận đơn**. Pi không có RTC; nếu mất điện qua đêm và mạng chưa lên khi bật lại, không rõ máy nên chờ đồng hồ (từ chối bán) hay bán với đồng hồ sai (vi phạm các bất biến về thời gian: hạn vé 24 giờ, TS tươi mới, thứ tự `error_log`, hạn token 12 giờ). Nguồn tự viết: "Không thể vừa hứa luôn bán offline từ lúc boot vừa chưa có nguồn giờ tin cậy." |
| Phần hệ thống bị ảnh hưởng | Offline behavior: đường khởi động của `flexmix-backend.service`; synchronization: mốc thời gian mọi gói tin qua dây (UTC ISO-8601); database: `order_ticket` hạn 24 giờ, `error_log` thứ tự mili-giây |
| Phương án đã có trong tài liệu | Không có phương án phần mềm đầy đủ. Nguồn chỉ đề xuất: bắt buộc `systemd-timesyncd`, thêm `After=time-sync.target`/`Wants=time-sync.target` vào service (hiện chỉ có `After=network.target mysql.service`), và với "máy hay mất điện, một mô-đun RTC I2C gắn thêm là vài chục nghìn đồng" — đây là giảm nhẹ phần cứng, không giải quyết trường hợp không có RTC và không có mạng khi boot. |
| Trade-off tài liệu gốc nêu | Không có so sánh giữa "chờ đồng hồ, từ chối bán" và "bán với đồng hồ sai". Nguồn chỉ liệt kê hậu quả nếu đồng hồ sai: "máy vừa bật có thể từ chối một nhãn hoàn toàn hợp lệ vì tưởng nó đến từ tương lai, hoặc chấp nhận một nhãn đã quá hạn," và doanh thu "chuyển sang nhầm ngày, vĩnh viễn" theo `sales_window()`. |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho hành vi bán hàng khi máy boot mà chưa có nguồn giờ tin cậy (không RTC, chưa có mạng) |
| Pha implementation bị block | Pha 00 (năm lỗi chặn, trước khi nối máy thứ hai) — chặn đường khởi động của backend |
| Quyết định tối thiểu cần OWNER cung cấp | Khi boot mà chưa đồng bộ được giờ: máy có được phép bán hay phải chờ; nếu bán, mức độ chấp nhận rủi ro (vé hết hạn sai, thứ tự log sai, doanh thu lệch ngày) là gì; có bắt buộc lắp RTC cho mọi máy hay chỉ máy hay mất điện |

**Trả lời của OWNER:**

---

### Q-22 — Tính nguyên tử sau commit khi `sync_menu` thất bại

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Nếu DB đã commit dữ liệu danh mục mới nhưng `sync_menu` (bước dựng lại `menu-data.js` từ DB) thất bại, không thể rollback transaction đã commit. Cần cơ chế retry/recovery và cách ghi `version đã áp` sao cho không báo sai sau crash. |
| Phần hệ thống bị ảnh hưởng | Synchronization: bước 5–6 của luồng danh mục xuống (ARCHITECTURE.md); database: thời điểm và tính nguyên tử của việc ghi cột "version đã áp" |
| Phương án đã có trong tài liệu | Có một đề xuất bổ sung (chưa duyệt): "Ghi version đã áp trong cùng giao dịch dữ liệu là đề xuất bổ sung để tránh báo version sai sau crash" (DATABASE_SPEC.md). Không có cơ chế phục hồi cho trường hợp `sync_menu` thất bại sau khi transaction đã commit thành công. |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho: retry/recovery khi `sync_menu` lỗi sau commit, và chẩn đoán để phát hiện tình trạng "DB mới nhưng menu hiển thị cũ" |
| Pha implementation bị block | Pha 04 (áp snapshot trong transaction, chạy `sync_menu`) |
| Quyết định tối thiểu cần OWNER cung cấp | Cơ chế retry tối thiểu khi `sync_menu` lỗi sau commit (tự động thử lại, hay cần can thiệp thủ công); có chấp nhận đề xuất "ghi version đã áp trong cùng giao dịch" hay không |

**Trả lời của OWNER:**
Không cho phép Machine nhận order khi
khởi động offline và chưa sync được clock.
---

### Q-23 — Schema vật lý của Hub và dữ liệu cho 17 cảnh báo

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Nguồn chỉ mô tả mô hình logic (bảng, quan hệ) cho Hub, không có DDL. Nhịp tim (heartbeat) hiện tại chưa đủ trường để tính toàn bộ 17 cảnh báo (ví dụ: chưa ghi rõ trạng thái MySQL, thời gian không tương tác tại cổng chờ người, thời điểm bật test mode). |
| Phần hệ thống bị ảnh hưởng | Database schema: DDL đầy đủ của Hub (kiểu tiền, index, FK, default/backfill cho `published` và `updated_at`); API contract: trường bổ sung cần thêm vào gói Nhịp tim; monitoring: khả năng tính đủ 17 cảnh báo |
| Phương án đã có trong tài liệu | Không có DDL. DATABASE_SPEC.md chỉ liệt kê "Thành phần logic Hub cần lưu" ở mức nhóm dữ liệu (đăng ký máy, điểm bán, danh mục chuẩn, ánh xạ, trạng thái mong muốn, quan sát máy, vận hành) và các quan hệ logic (điểm bán có nhiều máy, máy có nhiều snapshot/lệnh/vé). |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho: DDL cụ thể (kiểu cột, index, FK), kiểu dữ liệu tiền tệ, thứ tự migration Hub, cách phục hồi khi DDL dở dang, và các trường heartbeat còn thiếu để tính đủ 17 cảnh báo |
| Pha implementation bị block | Pha 02 (đủ dữ liệu cho 17 cảnh báo) và pha 04 (DDL danh mục Hub) |
| Quyết định tối thiểu cần OWNER cung cấp | Xác nhận nhóm dữ liệu logic ở DATABASE_SPEC.md là đủ phạm vi trước khi dựng DDL chi tiết; danh sách trường heartbeat bổ sung cần thêm (trạng thái MySQL, thời gian không tương tác, thời điểm bật test) |

**Trả lời của OWNER:**
Trả lời của OWNER:

Hub có Machine Registry làm nguồn quản lý lifecycle của Machine.

Registry phải lưu tối thiểu:
- machine record
- MID
- UUID/device identity
- lifecycle status
- provisioning information
- decommission information
- timestamps cần thiết
- thông tin version/schema cần cho monitoring và compatibility

MID phải UNIQUE và không được reuse.

Machine bị decommission vẫn giữ lịch sử trong Hub;
không xóa record để tái sử dụng MID.
---

### Q-24 — Chấp thuận stack Hub (Python/FastAPI/MySQL...) và phiên bản cụ thể

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | TECH_STACK.md hiện toàn bộ là ASSUMPTION — không có dòng REQUIREMENT nào cho ngôn ngữ/framework Hub. Không có stack được duyệt thì không thể bắt đầu viết bất kỳ module Hub nào (registry, catalogue, sync, monitoring...). |
| Phần hệ thống bị ảnh hưởng | Toàn bộ implementation phía Hub: database access layer, API framework, migration tool, giao diện quản trị, tiến trình nền, triển khai (systemd/Nginx) |
| Phương án đã có trong tài liệu | TECH_STACK.md đề xuất **một** baseline duy nhất: Python; FastAPI + Pydantic + Uvicorn; MySQL 8; SQLAlchemy + PyMySQL; Alembic; giao diện Jinja2 render phía server; long-poll cho lệnh; Nginx làm reverse proxy; systemd quản lý tiến trình; pytest + MySQL container để test. Tài liệu tự ghi: "nguồn không có tên framework trong nguồn" — tức đây hoàn toàn là đề xuất, không phải trích từ HTML gốc. Không có phương án thay thế nào được liệt kê để so sánh. |
| Trade-off tài liệu gốc nêu | Không có. Tài liệu chỉ nêu căn cứ chọn từng thành phần (ví dụ: MySQL 8 để "thống nhất phương ngữ SQL cho cả dự án"), không so sánh với lựa chọn khác. |
| Pha implementation bị block | Toàn bộ implementation phía Hub, từ pha 01 trở đi (ngay khi bắt đầu dựng registry) |
| Quyết định tối thiểu cần OWNER cung cấp | Chấp thuận hay từ chối baseline A-03/A-04 trong ARCHITECTURE_DECISIONS.md; nếu từ chối, không cần đề xuất thay thế ở đây — chỉ cần xác nhận "chưa chấp thuận" để tài liệu không bị coi là đã chốt; phiên bản cụ thể của Python/MySQL/thư viện nếu chấp thuận baseline |

**Trả lời của OWNER:**
Đồng ý. Phê duyệt bộ Tech Stack được đề xuất
làm baseline cho Hub:

Python, FastAPI, Pydantic, Uvicorn,
MySQL 8, SQLAlchemy, PyMySQL, Alembic,
Jinja2, Long-poll, Nginx, systemd, pytest
và MySQL container cho development.

---

### Q-26 — Ai giữ khóa ký snapshot?

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Gói Bản chụp (`GET /v1/state`) có trường `signature`, và agent phải kiểm chữ ký trước khi áp. Nguồn chỉ phát biểu invariant "Hub không giữ khóa ký" cho **khóa ký bản phát hành** (release), không nói gì về khóa ký snapshot. Snapshot được Hub sinh động theo từng máy theo từng truy vấn, nên không thể dùng khóa ký release ngoại tuyến cho việc này. Nếu hiểu nhầm invariant áp dụng luôn cho snapshot, có thể dẫn tới bỏ chữ ký snapshot hoặc kéo khóa ngoại tuyến lên online — cả hai đều sai. |
| Phần hệ thống bị ảnh hưởng | Security: danh sách khóa và vòng đời của chúng (SECURITY_SPEC.md); API contract: cách tạo và xác minh trường `signature` trong gói Bản chụp |
| Phương án đã có trong tài liệu | Không có. Nguồn chỉ mô tả rõ khóa ký **release**: "Bản phát hành là một git tag ký bằng khóa riêng cất ngoại tuyến... Khóa công khai tương ứng nằm sẵn trên máy." Với snapshot, nguồn chỉ liệt kê trường `signature` mà không mô tả khóa. |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho việc ai giữ khóa ký snapshot, thuật toán ký, và vòng đời của khóa đó |
| Pha implementation bị block | Pha 04 (danh mục đi xuống, agent kiểm chữ ký snapshot trước khi áp) |
| Quyết định tối thiểu cần OWNER cung cấp | Hub có được giữ khóa ký snapshot hay không (khác với khóa ký release); nếu có, cơ chế bảo vệ khóa đó tại Hub là gì |

**Trả lời của OWNER:**
Chưa quyết định.

Cần xác định owner của snapshot signing private key,
thuật toán sử dụng, cách phân phối public key,
key rotation và cơ chế xử lý khi key bị compromise.

---

### Q-27 — Miền giá trị MID khi Hub cấp phát

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Nguồn chỉ nêu miền 1–999999 cho cơ chế **nhập tay** hiện tại của `install.sh` — chính cơ chế mà lỗi chặn số 2 yêu cầu bỏ đi (thay bằng Hub cấp phát). Nguồn không nói miền giá trị của MID khi Hub tự cấp phát, và không nói định dạng payload QR (nơi MID được mã hóa) có giới hạn miền này hay không. |
| Phần hệ thống bị ảnh hưởng | Database schema: kiểu cột MID tại Hub và tại máy; machine registration: logic cấp phát lúc đăng ký; có thể ảnh hưởng định dạng payload QR nếu MID được mã hóa với số bit cố định |
| Phương án đã có trong tài liệu | Không có. |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho miền giá trị MID khi Hub cấp phát, và chưa xác nhận định dạng payload QR có ràng buộc miền này hay không |
| Pha implementation bị block | Pha 01 (registry, MID Hub cấp) |
| Quyết định tối thiểu cần OWNER cung cấp | Miền giá trị hợp lệ cho MID do Hub cấp (ví dụ: có giữ nguyên 1–999999, mở rộng, hay đổi kiểu hoàn toàn); xác nhận định dạng payload QR có giới hạn số bit cho MID hay không |

**Trả lời của OWNER:**
MID là số nguyên dương trong khoảng 1–999999.

MID đã cấp không được tái sử dụng, kể cả khi machine
bị decommission hoặc thay thế.

---

### Q-30 — Chủ sở hữu `audit_log` khi có cả máy và Hub cùng ghi

| Trường | Nội dung |
|---|---|
| Vì sao cần quyết định | Nguồn mô tả nhật ký thao tác là một chiều: "Máy ghi, Hub gộp". Nhưng bộ tài liệu đề xuất bổ sung việc Hub cũng tự ghi audit cho thao tác thực hiện tại Hub (ví dụ: ai đổi giá tại Hub) — đây là đề xuất, không có trong nguồn. Nếu triển khai, hai bên cùng ghi vào một không gian dữ liệu audit, đúng tình huống mà chính nguyên tắc sở hữu của nguồn cảnh báo: "Một dòng không có chủ là một dòng hai bên cùng ghi." |
| Phần hệ thống bị ảnh hưởng | Data ownership: bảng `audit_log`; database schema: khóa và cột nguồn gốc để tách dòng do máy ghi với dòng do Hub ghi; security: audit là bằng chứng điều tra khi nghi Hub bị chiếm quyền — cần biết bản nào đáng tin nếu hai bên lệch nhau |
| Phương án đã có trong tài liệu | Không có phương án tách bảng/tách khóa. Nguồn chỉ mô tả chiều máy→Hub. |
| Nếu chưa có phương án | **Tài liệu chưa đưa ra phương án** cho: audit tại Hub có cần tồn tại hay không; nếu có, dùng chung bảng hay tách bảng; khóa/cột nguồn gốc để tránh hai bên cùng ghi một dòng; audit tại Hub có được bảo vệ khỏi chính người chiếm quyền Hub hay không |
| Pha implementation bị block | Pha 05 (tài khoản theo điểm, phân quyền, audit) |
| Quyết định tối thiểu cần OWNER cung cấp | Có cần audit riêng cho thao tác thực hiện tại Hub hay không; nếu có, xác nhận tách bảng hay tách khóa trong cùng bảng với audit do máy gửi lên |

**Trả lời của OWNER:**
Chưa quyết định.

Cần xác định ownership của audit_log:
- Hub ghi những loại audit nào?
- Machine ghi những loại audit nào?
- Có dùng chung một bảng hay tách riêng?
- Nếu dùng chung, cần field nào để xác định source/origin?
---

## 2. CAN DECIDE LATER

Nhóm dưới đây là phân loại của người soạn biểu mẫu trước khi OWNER trả lời, không phải OWNER đã cho phép hoãn hoặc đã duyệt giải pháp tạm. Các câu Q-17/Q-28/Q-29 chưa trả lời vẫn ngăn việc coi báo cáo/cảnh báo/tiền kiểm tương ứng là hoàn chỉnh; không dùng bảng này để vượt các cổng nghiệm thu trong MASTER_REQUIREMENTS/DEPLOYMENT.

| Q-* | Câu hỏi | Vì sao có thể chốt sau | Phần bị ảnh hưởng khi chốt | Cần chốt trước |
|---|---|---|---|---|
| Q-02 | Bao nhiêu máy, phân bố ở đâu? | Chỉ ảnh hưởng sizing hạ tầng và mức độ cần thiết của pha 06; không đổi schema hay contract | Sizing VM, số worker, mức độ đầy đủ của pha 06 | Trước khi lập kế hoạch sizing/lộ trình chi tiết, không chặn pha 01–04 |
| Q-03 | Máy có cùng GPIO và nguyên liệu tại từng khe không? | Mô hình dữ liệu (bản đồ khe cắm theo từng máy) đã hỗ trợ trường hợp tổng quát dù các máy giống hay khác nhau; câu trả lời chỉ ảnh hưởng mức độ phức tạp thực tế cần xử lý | Khối lượng công việc đối chiếu ở pha 03; mức độ dùng capability filtering trong thực tế | Trước pha 03, không chặn thiết kế schema |
| Q-06 | Hub đặt ở đâu, ai vận hành? | Là quyết định hạ tầng/tổ chức, không đổi API contract hay database schema (đã tách riêng thành Q-24: dựng Hub bằng gì) | Vị trí VM, người chịu trách nhiệm vận hành, quy trình xử lý sự cố | Trước khi triển khai Hub thật, không chặn viết code |
| Q-17 | "Chưa từng quét" đo thế nào cho chính xác (vé claim rồi hủy quay lại `unused`)? | Chỉ số xấp xỉ `unused + expired` đã có sẵn trong nguồn và có thể dùng để lên cảnh báo ban đầu; việc đo chính xác hơn (cần dấu mốc lần quét đầu) là một cải tiến, không phải điều kiện để bắt đầu | Độ chính xác của một trong 17 cảnh báo; có thể cần thêm cột đánh dấu lịch sử chuyển trạng thái sau này | Khi cần độ chính xác cao hơn cho cảnh báo, không chặn pha 02 nếu dùng bản xấp xỉ trước |
| Q-25 | Monorepo hay Hub repo riêng; ai sở hữu contract? | Là quyết định tổ chức mã nguồn/quy trình làm việc, không đổi nội dung của bốn gói tin hay schema | Cấu trúc thư mục, quy trình versioning contract giữa hai repo | Trước khi thiết lập CI/CD chính thức, không chặn viết module riêng lẻ |
| Q-28 | Từ chối món đã rút có tính vào mẫu số cảnh báo "tỉ lệ pha hỏng" không? | Là một tinh chỉnh định nghĩa của một cảnh báo trong số 17 cảnh báo; có thể triển khai "không ghi vào `error_log`" trước (đã có trong pha 00b) và làm rõ mẫu số cảnh báo sau mà không cần đổi schema | Công thức tính cảnh báo "Pha hỏng" trong DEPLOYMENT.md | Trước khi cảnh báo "Pha hỏng" được coi là đã đúng hoàn toàn, không chặn việc ghi log ban đầu |
| Q-29 | Tiền kiểm cho nguyên liệu PUMP thiếu khai `gpio` chạy ở đâu (trình soạn, Hub, hay cả hai)? | Là một quy tắc validation bổ sung, không đổi cấu trúc schema hay API; có thể triển khai sau như một pre-check thêm vào luồng đã có (ARCHITECTURE.md §Năng lực) | Trình soạn công thức tại máy; bước tiền kiểm khi Hub phát hành snapshot | Trước khi coi tiền kiểm khả năng bán là hoàn chỉnh, không chặn việc phát hành snapshot cơ bản |

---

## 3. DOCUMENTATION / NO OWNER DECISION NEEDED

Hai mục này không phải lựa chọn kiến trúc hay nghiệp vụ của OWNER — chúng cần xác minh mã nguồn thực tế, hoặc là quyết định về cách dùng tài liệu.

| Q-* | Nội dung | Vì sao không cần OWNER quyết định ở đây | Việc cần làm |
|---|---|---|---|
| Q-10 | Nguồn nói "bảy file runtime" nhưng liệt kê tám đường dẫn; chưa rõ layout thay thế chính xác | Đây là việc đối chiếu với `git ls-files` trên repository ứng dụng thật (`version1.0 @ ce17f05`), không có trong workspace hiện tại. Không phải một lựa chọn thiết kế mà là một việc xác minh sự thật | Chạy `git ls-files` trên repo máy thật, xác nhận danh sách file runtime chính xác, cập nhật MASTER_REQUIREMENTS.md/DEPLOYMENT.md theo kết quả |
| Q-31 | Danh sách "Đã cân nhắc và loại bỏ" (10 hướng) có phải ràng buộc cho các bản thiết kế sau, hay chỉ là ghi chép lý do của bản 3? | Đây là câu hỏi về quy ước quản lý tài liệu (tài liệu này có tính bắt buộc hay chỉ tham khảo lịch sử), không phải một đánh đổi kỹ thuật hay nghiệp vụ cần OWNER cân nhắc trade-off | Xác nhận với người giữ tài liệu (có thể là OWNER, nhưng với vai trò biên tập viên tài liệu chứ không phải người quyết định kiến trúc) rằng ARCHITECTURE.md §Hướng đã cân nhắc và loại bỏ được coi là ràng buộc hay ghi chú lịch sử |

---

## 4. Ghi chú về M-01 .. M-06

Sáu mục `M-01`–`M-06` tại [OPEN_QUESTIONS.md §Mapping chưa chắc chắn](OPEN_QUESTIONS.md) là vấn đề **đối chiếu văn bản nội bộ** giữa OPEN_QUESTIONS.md, ARCHITECTURE_DECISIONS.md, TECH_STACK.md và PROJECT_STRUCTURE.md (ví dụ: một câu hỏi trong TECH_STACK.md có khớp với `Q-02` đã có hay cần một `Q-*` riêng). Đây không phải câu hỏi nghiệp vụ hay kiến trúc cần OWNER cân nhắc trade-off, nên không được xếp vào ba nhóm ở trên. Việc cần làm là người biên tập tài liệu xác nhận ranh giới giữa các `Q-*` liên quan, không phải OWNER chọn phương án kỹ thuật.

## 5. Sau khi OWNER trả lời

1. Với mỗi câu đã trả lời, tạo một mục `DEC-NNN` tại [06_decisions.md](06_decisions.md) theo template đã có ở đó, dùng đúng nội dung OWNER điền ở trên — không diễn giải thêm.
2. Cập nhật cột "Trạng thái" và "DEC-*" của `Q-*` tương ứng tại [OPEN_QUESTIONS.md §Sổ trạng thái Q-* ↔ D-*](OPEN_QUESTIONS.md). Không xóa nội dung câu hỏi gốc.
3. Cập nhật các đặc tả bị ảnh hưởng (cột "Phần hệ thống bị ảnh hưởng" ở mỗi câu trong file này chỉ ra nơi cần sửa).
4. File này (`DECISION_QUESTIONNAIRE.md`) có thể được đánh dấu đã xử lý cho câu đó, nhưng không xóa câu hỏi khỏi file — giữ lại để tham khảo lịch sử trả lời.


## 6. Ghi nhận xử lý câu trả lời — 17/09/2026

Giữ nguyên toàn bộ ô trả lời OWNER. Đã chuyển Q-01→DEC-001, Q-04→DEC-002, Q-05→DEC-003, Q-07→DEC-004, Q-08→DEC-005, Q-11→DEC-006, nội dung boot trong ô Q-22→DEC-007 (Q-21, mapping chờ OWNER xác nhận), Q-24→DEC-008, Q-27→DEC-009. Tất cả là DRAFT, chưa ACCEPTED.

Q-09 chỉ ghi “không” cho câu hỏi ghép, chưa đủ xác định lựa chọn, không tạo DEC. Ô Q-21 trống; không tự di chuyển câu trả lời ở Q-22 và không coi sync_menu đã có đáp án. Các câu “Chưa quyết định” giữ OPEN, không tự chuyển DEFERRED; nhóm CAN DECIDE LATER cũng không phải quyết định hoãn của OWNER.

Trạng thái phê duyệt và phần còn thiếu: [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md). Kết quả đối chiếu: [ARCHITECTURE_CONSISTENCY_REVIEW.md](ARCHITECTURE_CONSISTENCY_REVIEW.md). Đã sửa tham chiếu mô hình menu ở Q-01 từ A-06 thành A-01; không sửa câu trả lời.
