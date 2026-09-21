# Architecture Consistency Review

> Bản review lịch sử ngày 16/09/2026. Cập nhật sau câu trả lời OWNER ngày 17/09/2026 tại [docs/ARCHITECTURE_CONSISTENCY_REVIEW.md](docs/ARCHITECTURE_CONSISTENCY_REVIEW.md); không dùng các trạng thái cũ dưới đây thay sổ OPEN_QUESTIONS hiện hành.

> Đối tượng đọc: người viết Hub, người viết agent, và người sẽ chốt các quyết định còn mở.
>
> Nguồn gốc: [Kien_Truc_Doi_May.html](Kien_Truc_Doi_May.html) — đề xuất thiết kế bản 3, 10/09/2026, đọc theo `version1.0 @ ce17f05`.
> Tài liệu được review: 9 file trong [docs/](docs/).
> Ngày review: 16/09/2026.

## 1. Phạm vi và giới hạn của bản review này

Đây là **review tính nhất quán tài liệu**, không phải code audit. Trong workspace chỉ có file HTML và thư mục `docs/`; **không có mã nguồn ứng dụng** (`version1.0 @ ce17f05`) để đối chiếu. Vì vậy mọi phát biểu dạng "mã nguồn hiện làm X" trong cả HTML lẫn MD đều **chưa được kiểm chứng** ở đây, và bản review này không xác nhận chúng.

Bản review tuân thủ bốn giới hạn được yêu cầu:

- Không viết code.
- Không thay đổi kiến trúc.
- Không tự suy diễn yêu cầu chưa có trong tài liệu.
- **Không tự ý giải quyết OPEN QUESTION.** Mọi chỗ thiếu thông tin được ghi thành OPEN QUESTION mới, không được điền giả định.

Quy ước ID dùng trong tài liệu này, chọn khác với ID đang có để không va chạm: `MR-` missing requirement, `CT-` contradiction, `SR-` security risk, `DO-` data ownership, `PR-` protocol, `FO-` failure/offline, `DP-` deployment, `NQ-` new open question, `RD-` recommended decision. ID có sẵn trong bộ tài liệu (`REQ-`, `C-`, `D-`, `Q-`) được trích dẫn nguyên trạng.

## 2. Kết luận tổng thể

Bộ MD bao phủ nguồn ở mức cao và trung thực. Các bảng có số lượng phần tử cố định đều khớp chính xác: 25 dòng quyền sở hữu, 18 hàng ma trận suy giảm, 17 cảnh báo, 12 lệnh, 4 gói tin, 9 câu hỏi nghiệp vụ, 5 lỗi chặn, 6 bước vòng đời. Các giá trị số (24 / 12 / 16 / 10 / 9999 g / 24 giờ / 5 giây / 36 giờ / 7 bản / 3 bản / 110%) nhất quán giữa các file.

**Không phát hiện vi phạm trực tiếp nào** đối với 12 invariant được nêu trong yêu cầu review. Phần lớn mâu thuẫn còn lại là mâu thuẫn **có sẵn trong HTML gốc**, và bộ MD đã bắt đúng hầu hết chúng thành Q-10, Q-11, Q-16, Q-19, Q-21, Q-23.

Những gì bản review này bổ sung:

| Nhóm | Số phát hiện mới | Nặng nhất |
|---|---|---|
| Missing Requirements | 6 | MR-01 mất toàn bộ mục "Đã cân nhắc và loại bỏ" |
| Contradictions | 3 mới + 5 xác nhận | CT-01 nhãn REQUIREMENT đặt lên một khuyến nghị có 3 phương án |
| Security Risks | 3 | SR-01 invariant "Hub không giữ private key" đang bị hiểu rộng hơn nguồn |
| Data Ownership | 2 | DO-01 `audit_log` có hai bên cùng ghi, chưa có quy tắc tách khóa |
| Protocol | 2 | PR-01 miền giá trị MID sau khi Hub cấp phát |
| Failure/Offline | 2 | FO-01 xung đột giữa "luôn bán offline" và "đồng bộ giờ trước khi nhận đơn" |
| Deployment | 2 | DP-01 mất cột "Rủi ro cho tiệm" của lộ trình |
| OPEN QUESTION mới | 7 | NQ-01 ai giữ khóa ký snapshot |

## 3. Kiểm tra 12 invariant bắt buộc

| # | Invariant | Trạng thái | Nơi được giữ | Ghi chú |
|---|---|---|---|---|
| 1 | Hub không nằm trên critical path của bán/pha | **Giữ đúng** | REQ-01, C-01, ARCHITECTURE §Thành phần, ma trận suy giảm hàng "Mất mạng/Hub" | Ma trận cho Bán/Pha/In/Quản trị = Có khi mất Hub. Nhất quán cả 5 file. |
| 2 | `order_ticket` là local source of truth | **Giữ đúng** | C-02, DATABASE_SPEC bảng quyền sở hữu, ARCHITECTURE §Luồng sự kiện | `claim()` là UPDATE nguyên tử tại máy, "không phân xử từ xa" được giữ nguyên. Hub chỉ upsert bản sao theo `(machine_id, serial)`. |
| 3 | Delivery at-least-once và idempotent | **Giữ đúng, còn khoảng trống đã ghi nhận** | REQ-06, C-11, API_PROTOCOL §2, DATABASE_SPEC §Nguyên tử | Khóa idempotency cho `error`/`audit` và chống bản cũ ghi đè vé mới vẫn đang mở tại Q-14/D-15. Đây là khoảng trống của nguồn, đã được ghi đúng chứ không bị bỏ sót. |
| 4 | Cursor chỉ advance sau HTTP 200 | **Giữ đúng** | C-11, API_PROTOCOL §2, ARCHITECTURE §Luồng sự kiện, DATABASE_SPEC §Nguyên tử | Cả bốn chỗ đều thêm điều kiện thứ hai của nguồn: ACK phải trả đúng `cursor_to` Hub đã ghi, không chỉ cần mã 200. |
| 5 | MID không bao giờ reuse | **Giữ đúng** | REQ-02, C-05, DATABASE_SPEC §Định danh, DEPLOYMENT §Vòng đời | Gồm cả trường hợp thanh lý: MID cũ không cấp lại, lịch sử giữ nguyên. |
| 6 | `ingredient_id` 1–24 không renumber/reuse | **Giữ đúng** | REQ-07, C-13, C-15, ARCHITECTURE §Năng lực | Giữ cả ba vế của nguồn: không đánh số lại, không tái dùng mã đã ngừng, gộp thì gộp tên chứ không gộp mã. |
| 7 | Customer note không sync như normal data | **Giữ đúng ở telemetry; mâu thuẫn với backup đã được ghi nhận** | REQ-17, C-20, API_PROTOCOL §2, SECURITY_SPEC §Dữ liệu riêng tư | `mysqldump` toàn bộ DB chứa `note` — mâu thuẫn này có trong nguồn, đã được bắt đúng thành Q-16/D-17 và **chưa được giải**. Xem CT-04. |
| 8 | Hub không có private signing key | **Giữ đúng theo nghĩa hẹp của nguồn** | C-24, SECURITY_SPEC bảng khóa, TECH_STACK §Ràng buộc | Nguồn chỉ nói về **khóa ký bản phát hành**. Chữ ký snapshot là một khóa khác và nguồn chưa nói ai giữ. Xem SR-01 và NQ-01 — đây là chỗ dễ hiểu sai nhất trong 12 invariant. |
| 9 | Máy phải verify signed release trước khi chạy | **Giữ đúng** | REQ-15, C-24, API_PROTOCOL lệnh `apply-release`, SECURITY_SPEC §Release | Giữ đúng thứ tự: xác minh **trước** khi chạy installer/migration/mã tải về, khóa công khai cài sẵn từ lúc lắp. |
| 10 | Timestamp qua boundary dùng UTC ISO-8601 | **Giữ đúng** | C-12, API_PROTOCOL §Quy tắc chung | Giữ cả vế thứ hai: máy khai timezone để Hub dựng lại ngày kinh doanh địa phương, và cảnh báo cột `DATETIME` cục bộ không mang timezone. |
| 11 | Máy tiếp tục hoạt động khi Hub unavailable | **Giữ đúng; có một xung đột nội tại đã ghi nhận** | REQ-01, C-01, ma trận suy giảm | Xung đột với điều kiện "đồng bộ giờ trước khi nhận đơn" khi máy boot offline sau mất điện. Đã ghi ở Q-21; xem FO-01. |
| 12 | Máy thay thế có MID mới | **Giữ đúng** | C-05, DEPLOYMENT §Vòng đời và §Thời gian, sao lưu | Giữ cả hệ quả: lịch sử cũ vẫn gắn MID cũ, không tự kích hoạt vé của máy cũ, khóa QR không khôi phục. |

**Kết luận mục này:** không invariant nào bị mất, hiểu sai hoặc bị một file MD nói ngược lại. Hai chỗ cần chú ý khi đọc là invariant #8 (phạm vi hẹp hơn cách nói tắt) và #11 (xung đột với yêu cầu đồng hồ).

## 4. Bao phủ nguồn HTML → MD

| Mục trong HTML | Bao phủ | Nơi nhận |
|---|---|---|
| Mở đầu, thông số máy (Pi 5, 10+16, 1 ly, vé 24 giờ, khóa 64 hex) | Đủ | MASTER_REQUIREMENTS §Mục tiêu |
| "Bản 3 đổi gì" (nhật ký thay đổi so với bản 2) | **Không chuyển** | Có chủ đích và chấp nhận được: đây là phần meta. Nhưng nó chứa lý do vì sao các con số đổi (3→5 lỗi chặn, 17→25 dòng sở hữu, 10→17 cảnh báo); xem MR-06. |
| Một nguyên tắc (Hub ngoài đường bán) | Đủ | REQ-01, C-01 |
| Năm lỗi chặn | Đủ | MASTER_REQUIREMENTS §Năm điều kiện tiên quyết, DEPLOYMENT pha 00 |
| Sơ đồ ranh giới | Đủ | ARCHITECTURE §Thành phần, API_PROTOCOL |
| Năng lực của một máy (24/12/16/10/9999) | Gần đủ | ARCHITECTURE §Năng lực; thiếu một tình huống hỏng cụ thể — MR-03 |
| Vùng tên nguyên liệu, nhãn đang lưu hành | Đủ | REQ-07, C-13, DATABASE_SPEC §Định danh |
| Tiền, vé, và tồn kho | Đủ | REQ-10, REQ-11, REQ-12, Q-07, Q-17 |
| Nhận một máy đang chạy vào đội | Đủ | ARCHITECTURE §Nhận máy hiện hữu, DEPLOYMENT pha 03 |
| Ai làm chủ cái gì (25 dòng) | Đủ, khớp từng dòng | DATABASE_SPEC §Quyền sở hữu — đếm được đúng 25 dòng |
| Hai luồng, cố ý khác hình dạng | Đủ | ARCHITECTURE §Luồng xuống/§Luồng lên, C-08..C-11 |
| Hợp đồng dữ liệu trên dây (4 gói) | Đủ | API_PROTOCOL §1–§4 |
| Tình huống: cái gì còn chạy khi cái gì hỏng (18 hàng) | Đủ, khớp từng ô | ARCHITECTURE §Ma trận suy giảm — đối chiếu 18 hàng × 5 cột, không lệch ô nào |
| Tin cậy: định danh, bí mật, không khôi phục được | Đủ | SECURITY_SPEC toàn bộ |
| Mặt phẳng điều khiển (12 lệnh) | Đủ | API_PROTOCOL §4 — đủ 12 lệnh kèm chốt chặn |
| Giám sát (17 cảnh báo) | Đủ | DEPLOYMENT §Danh mục 17 cảnh báo — đủ 17 dòng, đúng ngưỡng và mức |
| Nhật ký thao tác và ghi chú khách | Đủ | REQ-20, C-20, SECURITY_SPEC §Audit |
| Vòng đời máy (6 bước) | Đủ | DEPLOYMENT §Vòng đời máy |
| Vận hành, đưa phần mềm xuống tiệm | Đủ | DEPLOYMENT §Quy trình phát hành |
| Lộ trình (00, 00b, 01–06) | **Thiếu một cột** | DEPLOYMENT §Lộ trình — mất cột "Rủi ro cho tiệm"; xem MR-02/DP-01 |
| Đã cân nhắc và loại bỏ (10 mục) | **Không chuyển** | Không có mục tương ứng trong bất kỳ file nào; xem MR-01 |
| Những điều chỉ bạn quyết được (9 câu) | Đủ | Q-01..Q-09, D-01..D-09 |

## 5. Missing Requirements

### MR-01 — Mất toàn bộ mục "Đã cân nhắc và loại bỏ" (mức: Cao)

HTML có 10 hướng bị loại bỏ kèm lý do: máy làm replica MySQL, database trên mây với máy là client mỏng, đánh số lại nguyên liệu toàn đội, một `QRPROTO_KEY` dùng chung, cho `:8080` nghe trên LAN, agent làm thread thứ tư trong `main.py`, gom hiệu chuẩn bơm về trung tâm, đẩy ghi chú khách lên Hub, để Hub tự dựng và tự ký bản phát hành, đánh số lại `ingredient_id` cho gọn vùng 1–24.

Bộ MD giữ được **kết quả** của 6–7 trong số đó dưới dạng ràng buộc khẳng định (ARCHITECTURE §Thành phần, C-30, C-13, C-15, C-20, C-24), nhưng **không giữ lý do loại bỏ** và không có chỗ nào liệt kê chúng như một tập hợp.

Hệ quả: lý do "replication là được ăn cả ngã về không trên schema mà cả hai bên đều ghi, và biến một lần đứt mạng thành một lần mất dữ liệu" không còn ở đâu. Người triển khai sau này có thể đề xuất lại đúng các hướng đã bị loại mà không biết chúng đã được cân nhắc, vì tài liệu chỉ nói "không làm X" chứ không nói "đã cân nhắc X và loại vì Y".

### MR-02 — Mất cột "Rủi ro cho tiệm" của lộ trình (mức: Trung bình)

Bảng lộ trình trong HTML có cột rủi ro cho từng pha: 00 = "Không, và gỡ được hai rủi ro đang tồn tại"; 00b = "Thấp, mỗi việc lùi được riêng"; 01 = "Không"; 02 = "Gần như không, agent chỉ đọc"; 03 = "Không"; 04 = "Có thật, bản chụp sai là đổi thực đơn"; 05 = "Bị khóa ngoài, luôn giữ `auth.py --set-password` chạy được tại máy"; 06 = "Cao nhất, bắt buộc có vòng máy thử".

[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) chỉ có cột "Cổng hoàn thành". Grep toàn bộ `docs/` không thấy chữ "Rủi ro" ở đâu. Nội dung rủi ro của pha 05 và 06 có được nhắc rải rác trong văn xuôi, nhưng mức rủi ro của từng pha — thứ giải thích **vì sao thứ tự pha là như vậy** và pha nào được phép làm song song — thì không còn truy nguyên được.

### MR-03 — Thiếu một dạng hỏng cụ thể mà tiền kiểm phải bắt (mức: Trung bình)

HTML nêu ba dạng hỏng cùng một họ, phát hiện quá muộn:

1. Topping có `ingredient_id` > 24 → `qrproto` ném lỗi lúc in nhãn.
2. Món có 13 lựa chọn → không mã hóa nổi payload.
3. **Nguyên liệu PUMP chưa khai cột `gpio` → `export_data.py` ném `ValueError` khi quét, tức là sau khi khách đã trả tiền.**

REQ-08, C-16 và ARCHITECTURE §Năng lực bao phủ (1) và (2) bằng các giới hạn số (≤24, ≤12, ≤10 PUMP, ≤16 MANUAL). Trường hợp (3) — **nguyên liệu có khe nhưng thiếu khai báo `gpio`** — không xuất hiện trong bất kỳ file nào. Nó khác hai trường hợp kia: không phải vượt giới hạn số lượng mà là thiếu dữ liệu cấu hình, và nó nổ ở thời điểm tệ nhất trong cả ba (sau khi thu tiền, lúc quét).

Mục 00b ② trong HTML gốc có ghi "mọi nguyên liệu PUMP đều có khe". Khi chuyển sang MD, [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) pha 00b rút gọn thành "tiền kiểm món" và bỏ mất vế này. Nguồn cũng không nói rõ "có khe" có bao gồm "đã khai `gpio`" hay không, nên chưa thể coi đây là cùng một việc. Xem NQ-04.

### MR-04 — Không có quy tắc "từ chối lịch sự không được ghi vào `error_log`" (mức: Trung bình)

HTML nói rõ món bị xóa sai **hai lần**: sai thứ nhất là làm hỏng nhãn đang lưu hành (đã bao phủ qua REQ-09, `deleted_at` vào cửa sổ yên tĩnh); sai thứ hai là câu từ chối "SKU 0007 không có công thức nào trong database" được `record_error()` ghi vào `error_log` **như một sự cố máy**, và vì thế kéo cảnh báo "tỉ lệ pha hỏng" của Hub lên.

Bộ MD giữ vế tích cực ("từ chối món rút lịch sự" — DEPLOYMENT pha 00b) nhưng **không giữ vế cấm**: không ghi vào `error_log`, và không tính vào mẫu số của cảnh báo "tỉ lệ pha hỏng > 10% trong 20 đơn gần nhất". Hàng cảnh báo "Pha hỏng" trong DEPLOYMENT không nhắc loại trừ này.

### MR-05 — Bộ tài liệu bị tách thành hai cụm không liên kết (mức: Trung bình)

Bảng "Quy ước và tài liệu liên quan" trong [docs/MASTER_REQUIREMENTS.md](docs/MASTER_REQUIREMENTS.md) liệt kê 6 tài liệu: ARCHITECTURE, DATABASE_SPEC, API_PROTOCOL, SECURITY_SPEC, DEPLOYMENT, OPEN_QUESTIONS. Nó **không nhắc** ARCHITECTURE_DECISIONS.md, TECH_STACK.md, PROJECT_STRUCTURE.md.

Ba file bị bỏ ngoài chính là nơi chứa bảng C-01..C-30 (ràng buộc kiến trúc) và D-01..D-25 (quyết định cần chốt). Người đọc đi từ tài liệu tổng thể sẽ không tìm thấy chúng, và ngược lại ARCHITECTURE_DECISIONS.md không trỏ về MASTER_REQUIREMENTS. Hai cụm tài liệu mô tả cùng một hệ thống bằng hai hệ ID khác nhau mà không có đường nối — xem thêm CT-02.

### MR-06 — Không giữ lý do vì sao các con số của bản 3 khác bản 2 (mức: Thấp)

Mục "Bản 3 đổi gì" giải thích từng thay đổi so với bản 2 và vì sao: vì sao lỗi chặn từ 3 lên 5, vì sao lỗi chặn số 1 rộng gấp ba, vì sao `threshold_gram` bị xếp nhầm nhóm ở bản 2, vì sao bảng quyền sở hữu từ 17 lên 25 dòng. Bộ MD giữ **kết quả** đúng ở mọi chỗ (đặc biệt `threshold_gram` = Dẫn xuất đã đúng theo bản 3) nhưng không giữ ghi chú "đây là chỗ bản 2 sai". Nếu sau này có người tìm được bản 2, không có gì trong bộ MD nói bản 2 đã bị sửa ở những điểm nào.

## 6. Contradictions

### CT-01 — Nhãn REQUIREMENT đặt lên một khuyến nghị có ba phương án (mức: Cao)

Đây là mâu thuẫn **giữa các file MD với nhau**, không có trong nguồn.

Nguồn phân biệt hai thứ khác nhau:

- **Mã nguyên liệu**: "Cửa sổ yên tĩnh" là một dòng trong bảng **Quy tắc** ("Không đánh số lại / Không tái dùng / Gộp thì gộp tên / Cửa sổ yên tĩnh"). Đây là luật.
- **Công thức**: nguồn nêu **ba phương án** (Chấp nhận / Ghim công thức vào vé / Áp lúc yên tĩnh) kèm đánh đổi, rồi nói "tôi khuyên cách thứ ba". Đây là khuyến nghị.

[docs/ARCHITECTURE_DECISIONS.md](docs/ARCHITECTURE_DECISIONS.md) gộp cả hai vào **C-17**, và mọi dòng C-* trong file đó mang nhãn **REQUIREMENT**. Kết quả: phương án được khuyến nghị cho công thức bị nâng thành ràng buộc đã chốt, đúng thứ mà quy ước nhãn của chính file đó dành cho ASSUMPTION ("giả định/khuyến nghị chưa duyệt").

Trong khi đó [docs/MASTER_REQUIREMENTS.md](docs/MASTER_REQUIREMENTS.md) REQ-09 thận trọng hơn: "quy tắc chính xác cần chốt Q-11", và [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) Q-11 coi cơ chế này là chưa giải. Cùng một nội dung, hai mức chắc chắn khác nhau ở ba file.

Lưu ý: chính ARCHITECTURE_DECISIONS.md có D-14 chỉ ra C-17 còn mơ hồ, nên file tự biết điều này ở mức nào đó — nhưng nhãn REQUIREMENT vẫn đứng nguyên và người đọc lướt bảng C-* sẽ không thấy D-14.

### CT-02 — Hai sổ theo dõi OPEN QUESTION song song, có nguy cơ lệch nhau (mức: Cao)

Cùng một tập câu hỏi đang được theo dõi ở hai nơi, bằng hai hệ ID:

| Nội dung | OPEN_QUESTIONS.md | ARCHITECTURE_DECISIONS.md |
|---|---|---|
| 9 câu hỏi nghiệp vụ của nguồn | Q-01..Q-09 | D-01..D-09 |
| Bảy file runtime nhưng tám đường dẫn | Q-10 | D-25 (gộp thêm việc khác) |
| Cửa sổ yên tĩnh | Q-11 | D-14 |
| MID / UUID / `machine_id` | Q-12 | D-12 |
| Xung đột SKU khi nhận máy cũ | Q-13 | D-18 |
| Cursor, thứ tự, retention | Q-14 | D-15 |
| Contract và mật mã trên dây | Q-15 | D-13 |
| Backup đầy đủ đối nghịch "note không lên Hub" | Q-16 | D-17 |
| "Chưa từng quét" đo thế nào | Q-17 | D-23 (gộp thêm heartbeat) |
| Rollback catalogue và version | Q-18 | D-19 (gộp thêm `sync_menu`) |
| Bán kính thiệt hại của Hub | Q-19 | D-21, D-22 (tách đôi) |
| Cổng sức khỏe, lệnh lặp | Q-20 | D-20, D-21 |
| Trình tự lỗi chặn, đồng bộ thời gian | Q-21 | D-24, D-25 |
| Nguyên tử sau commit, phạm vi audit | Q-22 | D-19 |
| Schema vật lý, dữ liệu cho cảnh báo | Q-23 | D-16, D-23 |

Ánh xạ **không phải một–một**: có chỗ một Q tương ứng hai D, có chỗ một D gộp hai Q. Không file nào công bố bảng ánh xạ này. Khi một câu được trả lời, người cập nhật phải nhớ sửa cả hai sổ với hai cách chia khác nhau — đây là cơ chế sinh mâu thuẫn trong tương lai, chứ chưa phải mâu thuẫn hôm nay.

Ghi chú: hai sổ hiện **chưa nói ngược nhau** ở nội dung nào mà bản review này kiểm được.

### CT-03 — Bao phủ không đều giữa REQ-* và C-* (mức: Thấp)

MASTER_REQUIREMENTS có REQ-01..REQ-20; ARCHITECTURE_DECISIONS có C-01..C-30. Hai danh sách phủ cùng một nguồn nhưng không tham chiếu chéo nhau: không REQ nào trỏ tới C, không C nào trỏ tới REQ. Có nội dung chỉ nằm ở một bên (ví dụ C-30 "không dùng replication" không có REQ tương ứng; REQ-18 "giám sát khả năng bán" chỉ khớp một phần với C-29). Hệ quả thực tế: không thể trả lời câu "yêu cầu này đã được ràng buộc kiến trúc nào bảo vệ" bằng cách tra bảng.

### Bốn mâu thuẫn của nguồn — xác nhận đã được bắt đúng

Bản review kiểm lại độc lập và xác nhận bốn mâu thuẫn sau **có thật trong HTML gốc** và **đã được bộ MD ghi nhận đúng**, không cần mở lại:

| Mâu thuẫn trong nguồn | Xác nhận | Đã ghi ở |
|---|---|---|
| Nói "bảy file runtime" nhưng liệt kê **tám** đường dẫn (2 hiệu chuẩn + 2 cấu hình + 4 trạng thái) | Đếm lại: đúng 8 | Q-10, D-25, ghi chú cuối §Năm điều kiện tiên quyết |
| Cửa sổ yên tĩnh có **hai** cách phát biểu: "hết vé chưa quét **hoặc** 24 giờ sau nhãn cuối, lấy mốc đến sau" và "hết vé unused **và** máy đang rảnh" | Đúng, hai điều kiện khác nhau; vế "máy đang rảnh" chỉ có ở cách thứ hai | Q-11, D-14 |
| `mysqldump` toàn bộ DB mang theo `note`, trong khi `note` bị cấm lên Hub | Đúng; nguồn không giải quyết | Q-16, D-17, SECURITY_SPEC §Dữ liệu riêng tư |
| Bảng cảnh báo trỏ "xem **câu hỏi 07**" cho giờ mở cửa, nhưng giờ mở cửa là **câu 08** (câu 07 là "khách trả tiền lúc nào") | Đúng, nguồn đánh số lệch | Q-23 đã ghi và chuẩn hóa dùng Q-08 |

Mâu thuẫn thứ năm — pha 00 tuyên bố "chưa có Hub" nhưng một trong năm lỗi chặn là "Hub cấp MID" (nằm ở pha 01) — cũng đã được ghi tại DEPLOYMENT §Lộ trình và Q-21/D-25. Xem thêm DP-02.

## 7. Security Risks

### SR-01 — Invariant "Hub không có private signing key" đang bị phát biểu rộng hơn nguồn (mức: Cao)

Nguồn chỉ khẳng định một điều rất cụ thể: **bản phát hành** phải được ký bằng một khóa cất ngoại tuyến mà **Hub không giữ**, và khóa công khai tương ứng nằm sẵn trên máy. Lý lẽ đi kèm cũng hẹp đúng như vậy: "Hub chỉ được quyền gọi tên một bản, không được quyền tạo ra một bản."

Nhưng gói **Bản chụp** trong hợp đồng dữ liệu lại có trường `signature`, và bản chụp được Hub sinh ra theo từng máy, theo từng truy vấn `GET /v1/state?have=`. Nguồn **không nói ai ký bản chụp và bằng khóa nào**.

Nếu ai đó áp dụng invariant theo cách nói tắt "Hub không có private key" cho cả chữ ký snapshot, sẽ có hai kết cục sai: hoặc bỏ luôn chữ ký snapshot (mất một lớp toàn vẹn), hoặc dùng khóa ký release ngoại tuyến để ký từng bản chụp (không khả thi trong vận hành, và kéo khóa ngoại tuyến lên online — phá đúng invariant cần bảo vệ).

[docs/SECURITY_SPEC.md](docs/SECURITY_SPEC.md) đã cảnh báo đúng hướng ("Không đồng nhất chữ ký release với chữ ký snapshot chưa được đặc tả", và tách thành hai dòng trong bảng khóa), nhưng chưa phát biểu thẳng rằng invariant chỉ có phạm vi **khóa ký release**. Xem NQ-01.

### SR-02 — Gói backup gửi lên Hub chưa có chính sách, trong khi nó là gói nhạy cảm nhất (mức: Cao)

`mysqldump` toàn bộ `beveragepos` mang theo: `order_ticket.note` (dữ liệu khách tự gõ), toàn bộ lịch sử bán hàng, tồn kho, `error_log`, và bản sao hash/salt PBKDF2 của `admin_user`. Nguồn yêu cầu đẩy gói đêm lên Hub và Hub giữ N bản mỗi máy.

Bộ MD đã ghi nhận mâu thuẫn với "note không lên Hub" (Q-16/D-17) nhưng ba câu hỏi bảo mật đi kèm vẫn mở và **chưa được liệt kê thành rủi ro**: mã hóa gói backup ở đâu (tại máy trước khi gửi, hay tại Hub), ai trong tổ chức được đọc gói backup của một tiệm, và Hub bị chiếm quyền thì bán kính thiệt hại có bao gồm N bản dump của cả đội hay không.

Điểm cần nói rõ: hash tài khoản vốn đã nằm ở Hub vì Hub làm chủ `admin_user`, nên đó không phải phần mới. Phần mới là `note` và dữ liệu vận hành chi tiết của từng tiệm. Nếu Hub giữ dump đầy đủ của cả đội, thì câu "Hub bị chiếm quyền chỉ đổi được thực đơn và giá" **không còn đủ** — kẻ chiếm quyền còn đọc được ghi chú khách của mọi tiệm, kể cả khi không chạy được bơm nào. Đây là một mở rộng bán kính thiệt hại mà mục "Hub bị chiếm quyền" của nguồn chưa tính tới.

### SR-03 — Audit là bằng chứng điều tra, nhưng chưa có ràng buộc toàn vẹn (mức: Trung bình)

SECURITY_SPEC §Audit và xử lý sự cố đặt `audit_log` vào đúng vai trò điều tra: khi nghi Hub bị chiếm quyền thì "đối chiếu release, snapshot và audit trước khi nối lại". Nhưng `audit_log` được máy ghi rồi đẩy lên Hub theo cùng đường như `error_log`, và Hub cũng tự ghi audit của thao tác tại Hub (xem DO-01).

Chưa có gì trong bộ tài liệu nói về: audit tại Hub có bị sửa được bởi chính người chiếm quyền Hub không, bản audit tại máy có được giữ độc lập đủ lâu để đối chiếu không, và khi hai bản lệch nhau thì bản nào là bằng chứng. Nguồn cũng không nói. Đây là khoảng trống, không phải mâu thuẫn — nhưng nó nằm đúng trên đường dùng của kịch bản Hub bị chiếm quyền.

## 8. Data Ownership Issues

### DO-01 — `audit_log` là dòng duy nhất trong bảng sở hữu có hai bên cùng ghi (mức: Cao)

Nguồn mở đầu mục quyền sở hữu bằng đúng cảnh báo này: "Gần như mọi hỏng hóc trong hệ nhiều máy đều đến từ hai bên cùng tin mình làm chủ một dòng... Một dòng không có chủ là một dòng hai bên cùng ghi."

Dòng `audit_log` trong [docs/DATABASE_SPEC.md](docs/DATABASE_SPEC.md) ghi chủ sở hữu là "**Máy; Hub ghi thao tác tại Hub**" — hai chủ trên một dòng. Trong nguồn, dòng tương ứng là "Nhật ký thao tác (bảng mới) — **Máy ghi, Hub gộp** — ↑ nối thêm", tức là nguồn mô tả một chiều duy nhất. Việc Hub cũng cần ghi audit cho thao tác tại Hub là **đề xuất bổ sung của bộ MD**, hợp lý về nghiệp vụ (nếu không thì "ai đổi giá ở Hub" không có ai trả lời), nhưng nó tạo ra đúng tình huống mà nguyên tắc sở hữu cấm.

DATABASE_SPEC đã ghi nhận một nửa vấn đề ("khóa audit cần định nghĩa một ID ổn định"), nhưng chưa có quy tắc **tách miền khóa** giữa dòng do máy sinh và dòng do Hub sinh, cũng chưa có cột nguồn gốc. Không có quy tắc đó thì hai bên cùng upsert vào một bảng với một không gian ID.

### DO-02 — Trạng thái "không pha được ở đây" không có chỗ trong bảng sở hữu (mức: Trung bình)

Nguồn mô tả **ba trạng thái phải nói khác nhau trên màn hình**, kèm cột "nhân viên làm gì":

| Trạng thái | Ai đặt | Nhân viên làm gì |
|---|---|---|
| không pha được ở đây | Hub tính từ bản đồ khe cắm | Không làm gì được, phải đổi cách đi dây |
| `drink.available` | Nhân viên tại quầy | Bật lại khi muốn bán |
| `drink.in_stock` | Trigger MySQL | Châm thêm nguyên liệu |

Bảng sở hữu trong DATABASE_SPEC có `published`, `available`, `in_stock` nhưng **không có dòng cho trạng thái thứ nhất**, vì theo thiết kế món đó bị lọc khỏi bản chụp chứ không được gửi xuống. Điều đó đúng về cơ chế, nhưng làm mất hai thứ: (a) đây là bốn khái niệm chứ không phải ba (`published` = "thuộc thực đơn điểm bán này" khác với "máy này có khe để pha"), và (b) cột "nhân viên làm gì" — thứ quyết định màn hình phải hiển thị gì — không còn ở đâu trong bộ MD.

ARCHITECTURE §Năng lực có giữ cơ chế lọc, nên đây là thiếu ở mức mô tả sản phẩm chứ không phải sai kiến trúc.

## 9. Protocol Issues

### PR-01 — Miền giá trị của MID sau khi chuyển sang Hub cấp phát (mức: Trung bình)

[docs/DATABASE_SPEC.md](docs/DATABASE_SPEC.md) §Định danh viết: "MID do Hub cấp, **miền nhập hiện trạng 1–999999**, duy nhất và không tái sử dụng."

Con số 1–999999 trong nguồn đến từ câu hỏi của `install.sh` ở chế độ **nhập tay** — đúng cái chế độ mà lỗi chặn số 2 yêu cầu bỏ đi. Nguồn không nói miền này có được giữ sau khi Hub cấp phát hay không. Vì MID nằm bên trong phần mã hóa của payload QR và được đối chiếu lúc quét, miền giá trị của nó là một ràng buộc giao thức thật, không phải chi tiết giao diện.

Câu hỏi chưa ai trả lời: Hub cấp MID trong miền nào, và miền đó có bị giới hạn bởi định dạng payload QR hiện có không. Xem NQ-02. Không tự chốt ở đây.

### PR-02 — `machine_id` trên dây chưa buộc với khóa xác thực (mức: Trung bình)

Đây là mở rộng của Q-12/D-12, nêu ở đây vì nó là vấn đề giao thức chứ không chỉ là vấn đề định danh.

Gói `POST /v1/events` mang `machine_id` **trong payload**. Nguồn không liệt kê `machine_id` trong nhịp tim hay trong ack lệnh, nên hai gói đó chưa rõ nhận diện máy bằng cách nào. Trong khi đó danh tính thật được chứng minh bằng mTLS và/hoặc chữ ký Ed25519 ở lớp vận chuyển. [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) Q-12 đã ghi đúng nguyên tắc ("Không để request tự khai ID của máy khác") nhưng quy tắc bắt buộc — Hub phải **bỏ qua** `machine_id` trong payload nếu nó không khớp danh tính đã xác thực, hoặc từ chối cả lô — chưa được viết thành yêu cầu ở API_PROTOCOL.

Vì Hub upsert vé theo `(machine_id, serial)`, một máy khai sai `machine_id` sẽ ghi đè vé của máy khác, và ghi đè đó là **idempotent và hợp lệ** dưới mắt của cơ chế chống trùng hiện có.

## 10. Failure/Offline Issues

### FO-01 — "Luôn bán được khi offline" và "đồng bộ giờ trước khi nhận đơn" không thể cùng đúng vô điều kiện (mức: Cao)

Nguồn đặt hai yêu cầu cạnh nhau:

- Nguyên tắc nền: máy cả tuần không liên lạc được với Hub thì **bị suy giảm, không hỏng**; mất mạng thì Bán/Pha/In/Quản trị đều "chạy".
- Lỗi chặn thứ ba: bắt buộc `systemd-timesyncd`, thêm `After=time-sync.target` và `Wants=time-sync.target` **trước khi nhận đơn**.

Máy Pi không có RTC. Mất điện qua đêm rồi bật lại trong lúc mạng tiệm cũng chưa lên: hoặc máy **chờ đồng hồ** và không bán (giữ đúng tính đúng đắn của vé 24 giờ, nhưng vi phạm lời hứa bán offline), hoặc máy **bán với đồng hồ sai** (giữ lời hứa, nhưng từ chối nhãn hợp lệ, chấp nhận nhãn hết hạn, và đẩy doanh thu sang nhầm ngày — vĩnh viễn, theo `sales_window()`).

Q-21 đã phát biểu chính xác điều này ("Không thể vừa hứa luôn bán offline từ lúc boot vừa chưa có nguồn giờ tin cậy") và **chưa được giải**. Bản review giữ nguyên trạng thái mở, chỉ nâng mức: đây là xung đột trực tiếp giữa hai invariant trong danh sách 12 (#10 và #11), nên nó cần được chốt trước khi bất kỳ ai viết đường khởi động của backend.

Ghi chú bổ sung mà bản review tìm thấy: ma trận suy giảm có riêng hàng "Đồng hồ sai sau mất điện" với Bán = "chạy" (Có). ARCHITECTURE.md nói rõ ma trận mô tả **hiện trạng**, nên hàng này đúng cho hôm nay. Nhưng sau khi sửa lỗi chặn thứ ba, không tài liệu nào nói hàng đó sẽ đổi thành gì. Người đọc ma trận như một hợp đồng — đúng như nguồn yêu cầu ("Bảng này là hợp đồng của thiết kế") — sẽ hiểu là máy vẫn bán với đồng hồ sai.

### FO-02 — Hủy đơn sau khi đã rót: chưa có đường xử lý vé và tồn kho (mức: Trung bình)

Nguồn thêm hạn giờ 10 phút cho cổng chờ người và lệnh `cancel-current-order`, cả hai đều "trả vé về `unused`". Nhưng cổng chờ người không chỉ có cổng đặt ly: nguồn liệt kê "cổng đặt ly, bước tay, bước thao tác". Vì `recipe_action` xếp chung một dãy `step_no` với bước bơm, bước tay **có thể** nằm sau một bước bơm. Nguồn không nói thứ tự này luôn xảy ra, nhưng cũng không loại trừ nó.

Trả vé về `unused` sau khi đã rót (nếu trường hợp này xảy ra) nghĩa là khách quét lại nhãn đó và được pha thêm một lần nữa, trong khi nguyên liệu lần một đã mất. Nguồn không nói trường hợp này xử lý thế nào; `consume_inventory` chỉ chạy khi hoàn tất và `charge_for_failed_order` chỉ chạy khi đơn hỏng.

Q-20/D-22 đã ghi câu hỏi này ("Khi timeout/hủy sau khi đã rót, hoàn vé và trừ tồn thế nào để tránh pha thêm miễn phí?") và REQ-13 cũng ghi "cần chốt xử lý nguyên liệu đã dùng". Bản review xác nhận đây là khoảng trống thật của nguồn, không phải lỗi transcription, và nó chạm vào invariant #2 (`order_ticket` là thẩm quyền tại máy) — quy tắc chuyển trạng thái phải được chốt tại máy chứ không ở Hub.

## 11. Deployment Issues

### DP-01 — Lộ trình mất tiêu chí rủi ro, nên cổng giữa các pha chỉ còn một nửa (mức: Trung bình)

Xem MR-02 cho phần thiếu. Hệ quả vận hành: bảng lộ trình hiện chỉ có "Cổng hoàn thành" (điều kiện để coi pha là xong) mà không có mức rủi ro (điều kiện để quyết định pha đó được làm khi nào, có cần vòng máy thử không, có lùi riêng được không). Nguồn dùng đúng cột rủi ro để biện minh cho hai quyết định: vì sao pha 06 phải để cuối, và vì sao pha 00/00b làm được ngay cả khi dự án đội máy bị hủy.

### DP-02 — Pha 00 và cấp phát MID: mâu thuẫn đã ghi nhận, chưa giải (mức: Trung bình)

Nguồn nói pha 00 là "sửa năm lỗi chặn — chưa có Hub, chưa có agent", nhưng lỗi chặn thứ hai có cách sửa là "Hub cấp MID lúc đăng ký máy, phase secrets hỏi Hub thay vì hỏi người", và việc đó nằm ở pha 01.

[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) đã nêu thẳng điểm này và trỏ về Q-21; [docs/MASTER_REQUIREMENTS.md](docs/MASTER_REQUIREMENTS.md) vẫn liệt kê nó là điều kiện tiên quyết số 2. Bản review xác nhận cả hai cách ghi đều trung thực với nguồn và mâu thuẫn nằm ở nguồn. Câu cần chốt — "trước khi nối máy thứ hai thì bắt buộc xong những gì" — vẫn mở, và không được giải ở đây.

## 12. OPEN QUESTIONS

### 12.1 Câu hỏi đã có trong bộ tài liệu — giữ nguyên trạng thái mở

Không câu nào dưới đây được bản review trả lời hay thu hẹp.

- **Nghiệp vụ, nguồn hỏi trực tiếp:** Q-01/D-01 menu chung hay theo điểm; Q-02/D-02 quy mô và địa bàn; Q-03/D-03 các máy có đi dây giống nhau; Q-04/D-04 khóa QR chấp nhận mất hay ký gửi; Q-05/D-05 có vé liên máy không; Q-06/D-06 Hub đặt ở đâu; Q-07/D-07 thu tiền lúc in nhãn hay lúc giao ly; Q-08/D-08 giờ mở cửa và ai trực cảnh báo; Q-09/D-09 ai đổi giá từ xa, có cần hai người duyệt.
- **Kỹ thuật, phát hiện khi tách đặc tả:** Q-10 số file runtime; Q-11/D-14 cửa sổ yên tĩnh; Q-12/D-12 MID/UUID/`machine_id`; Q-13/D-18 xung đột SKU; Q-14/D-15 cursor và retention; Q-15/D-13 contract và mật mã; Q-16/D-17 backup đối nghịch quy tắc `note`; Q-17/D-23 đo "chưa từng quét"; Q-18/D-19 rollback catalogue và version; Q-19/D-21/D-22 bán kính thiệt hại của Hub; Q-20 cổng sức khỏe và lệnh lặp; Q-21/D-24 trình tự lỗi chặn và đồng bộ thời gian; Q-22 nguyên tử sau commit và phạm vi audit; Q-23/D-16 schema vật lý và dữ liệu cho cảnh báo; D-10/D-11 stack và tổ chức repo.

### 12.2 OPEN QUESTION mới do bản review này phát hiện

| ID | Câu hỏi | Vì sao chưa trả lời được từ tài liệu | Chặn việc gì |
|---|---|---|---|
| **NQ-01** | Chữ ký của gói **Bản chụp** do ai ký và bằng khóa nào? Invariant "Hub không giữ khóa ký" có áp cho khóa này không, hay chỉ áp cho khóa ký bản phát hành? | Nguồn có trường `signature` trong gói bản chụp nhưng không nói chủ khóa; mục Tin cậy chỉ nói về khóa ký **bản phát hành** | SR-01, thiết kế xác thực gói bản chụp, phạm vi Q-15/D-13 |
| **NQ-02** | Hub cấp MID trong miền giá trị nào? Miền 1–999999 của lần nhập tay còn hiệu lực sau khi bỏ nhập tay không, và payload QR có ràng buộc miền này không? | Nguồn chỉ nêu 1–999999 như câu hỏi của `install.sh`; không nói miền của cơ chế cấp phát mới | PR-01, đăng ký máy ở pha 01, định dạng payload |
| **NQ-03** | Câu từ chối "món đã ngừng bán" có được ghi vào `error_log` không, và nó có vào mẫu số của cảnh báo "tỉ lệ pha hỏng" không? | Nguồn nói nó "không ghi vào nhật ký sự cố" nhưng không nói về mẫu số của cảnh báo; bộ MD chỉ giữ vế "từ chối lịch sự" | MR-04, định nghĩa cảnh báo Pha hỏng, việc 00b ⑤ |
| **NQ-04** | Tiền kiểm tính bán được có phải bắt cả trường hợp nguyên liệu PUMP thiếu khai `gpio` không, và bắt ở máy, ở Hub, hay cả hai? | Nguồn nêu hậu quả (`ValueError` lúc quét, sau khi khách trả tiền) nhưng không đưa nó vào danh sách điều kiện tiền kiểm | MR-03, REQ-08, tiền kiểm ở trình soạn và ở Hub |
| **NQ-05** | `audit_log` do máy ghi và audit do Hub ghi dùng chung bảng hay tách bảng? Nếu chung, khóa và cột nguồn gốc tách thế nào để không có hai bên cùng ghi một dòng? | Nguồn chỉ mô tả chiều "máy ghi, Hub gộp"; audit tại Hub là đề xuất bổ sung của bộ MD | DO-01, SR-03, thiết kế bảng audit |
| **NQ-06** | Gói backup gửi lên Hub có được mã hóa không, ai đọc được, và giữ ở Hub thì bán kính thiệt hại khi Hub bị chiếm quyền được phát biểu lại thế nào? | Q-16 hỏi về nội dung gói và retention nhưng không hỏi về mã hóa, quyền đọc, và ảnh hưởng tới ô "Hub bị chiếm quyền" | SR-02, chính sách backup ở pha 02 |
| **NQ-07** | Danh sách "Đã cân nhắc và loại bỏ" có hiệu lực ràng buộc không — tức là 10 hướng đó bị cấm về sau, hay chỉ là ghi chép lịch sử của bản 3? | Nguồn trình bày chúng như quyết định đã đưa ra, nhưng không nói chúng có phải ràng buộc cho các bản sau không | MR-01, cách ghi lại các hướng bị loại |

## 13. Recommended Decisions

**Phạm vi:** mọi mục dưới đây là khuyến nghị về **cách ghi chép và quy trình tài liệu**. Không mục nào chọn đáp án thay cho một OPEN QUESTION, không mục nào thay đổi kiến trúc, và không mục nào thêm yêu cầu mới vào hệ thống.

| ID | Khuyến nghị | Giải quyết |
|---|---|---|
| **RD-01** | Thêm một mục "Đã cân nhắc và loại bỏ" vào bộ MD, chép đủ 10 hướng kèm **lý do loại** của nguồn. Đặt ở ARCHITECTURE.md hoặc một phụ lục riêng, và trỏ chéo tới các C-* đang giữ kết quả. Kèm theo, chốt NQ-07 để biết mục này là ràng buộc hay ghi chép. | MR-01, NQ-07 |
| **RD-02** | Khôi phục cột "Rủi ro cho tiệm" vào bảng lộ trình trong DEPLOYMENT.md, nguyên văn năm mức của nguồn, đặt cạnh cột "Cổng hoàn thành". | MR-02, DP-01 |
| **RD-03** | Chọn **một** sổ theo dõi câu hỏi mở làm sổ chuẩn, sổ còn lại chỉ trỏ sang bằng ID. Nếu giữ cả hai thì bổ sung bảng ánh xạ Q-* ↔ D-* (bản nháp đã có ở CT-02) và một quy tắc: khi trả lời một câu, cập nhật cả hai trong cùng một lần sửa. | CT-02 |
| **RD-04** | Soát lại nhãn của C-17: tách phần **mã nguyên liệu** (nguồn phát biểu như luật) khỏi phần **công thức** (nguồn phát biểu như một trong ba phương án, có khuyến nghị). Đặt nhãn theo đúng quy ước mà chính ARCHITECTURE_DECISIONS.md đã định nghĩa, và trỏ tới D-14/Q-11 ngay tại dòng. | CT-01 |
| **RD-05** | Bổ sung ARCHITECTURE_DECISIONS.md, TECH_STACK.md, PROJECT_STRUCTURE.md vào bảng tài liệu liên quan của MASTER_REQUIREMENTS.md, và thêm đường trỏ ngược. Cân nhắc thêm cột "C-* liên quan" vào bảng REQ-*. | MR-05, CT-03 |
| **RD-06** | Phát biểu lại invariant khóa ký cho chính xác phạm vi: "Hub không giữ khóa ký **bản phát hành**", và ghi rõ chữ ký snapshot là một khóa khác chưa được đặc tả (NQ-01). Nên sửa ở SECURITY_SPEC bảng khóa và ở C-24 để cách nói tắt không lan ra. | SR-01, NQ-01 |
| **RD-07** | Ghi ba phát hiện thiếu vào đúng chỗ của chúng, dưới dạng câu hỏi chứ không phải câu trả lời: NQ-03 vào định nghĩa cảnh báo "Pha hỏng" trong DEPLOYMENT.md, NQ-04 vào danh sách tiền kiểm ở ARCHITECTURE.md §Năng lực, NQ-05 vào dòng `audit_log` của DATABASE_SPEC.md. | MR-03, MR-04, DO-01 |
| **RD-08** | Ghi rõ trong ARCHITECTURE.md §Ma trận suy giảm rằng hàng "Đồng hồ sai" đang giả định máy **vẫn bán**, và điều đó chưa nhất quán với yêu cầu đồng bộ giờ trước khi nhận đơn; trỏ tới Q-21. Không chọn hành vi nào ở bước ghi chép này. | FO-01 |
| **RD-09** | Gán cho mỗi câu hỏi mở một pha mà nó phải được chốt trước. Hiện chỉ ba câu có pha rõ trong cột "Cần chốt trước" của OPEN_QUESTIONS.md: Q-01 và Q-03 trước pha 03, Q-08 trước pha 02. Các câu còn lại, kể cả NQ-01..NQ-07, chưa có pha gắn kèm; người chốt câu hỏi nên điền cột này thay vì để bản review đoán. Riêng Q-21/FO-01 chạm đường khởi động của backend, nên cần được xếp lịch sớm. | Toàn bộ §12 |
| **RD-10** | Giữ nguyên hai điểm mạnh hiện có khi cập nhật: mọi file đều mở đầu bằng cùng một câu miễn trừ về trạng thái chưa kiểm chứng, và không file nào tuyên bố bất kỳ phần nào "đã triển khai" hay "đã kiểm chứng" (đã soát toàn bộ `docs/`, không có trường hợp nào). Đây là thứ giúp bản review này phân biệt được đâu là yêu cầu và đâu là đề xuất. | Chất lượng bộ tài liệu |

## 14. Những gì bản review này KHÔNG làm

- Không trả lời Q-01..Q-23, D-01..D-25, hay NQ-01..NQ-07.
- Không chọn phương án cho cửa sổ yên tĩnh, cho khóa QR, cho định nghĩa doanh thu, cho stack Hub, hay cho hành vi khi boot không có giờ tin cậy.
- Không kiểm chứng bất kỳ phát biểu nào về mã nguồn `version1.0 @ ce17f05`; không có mã đó trong workspace.
- Không sửa file nào trong `docs/`. Mọi khuyến nghị ở §13 là đề xuất, chờ người quyết định.

## 15. Trạng thái sau đợt chuẩn hóa tài liệu (16/09/2026)

Đợt chuẩn hóa chỉ sửa lỗi về liên kết, mapping, thông tin bị mất khi chuyển từ HTML, và phân loại requirement/khuyến nghị. Không OPEN QUESTION nào được trả lời.

| Phát hiện | Trạng thái |
|---|---|
| MR-01 | Đã sửa: ARCHITECTURE.md §Hướng đã cân nhắc và loại bỏ. Hiệu lực ràng buộc vẫn mở tại Q-31 |
| MR-02, DP-01 | Đã sửa: cột "Rủi ro cho tiệm" trong DEPLOYMENT.md |
| MR-03 | Đã khôi phục nội dung nguồn (ARCHITECTURE.md §Năng lực, DEPLOYMENT.md pha 00b ②). Phạm vi tiền kiểm vẫn mở tại Q-29 |
| MR-04 | Đã khôi phục vế "không ghi vào `error_log`" (DEPLOYMENT.md pha 00b ⑤). Quan hệ với cảnh báo vẫn mở tại Q-28 |
| MR-05, CT-03 | Đã sửa: liên kết giữa các tài liệu; bảng truy nguyên REQ-* ↔ C-* trong ARCHITECTURE_DECISIONS.md |
| MR-06 | Đã sửa: MASTER_REQUIREMENTS.md §Thay đổi của bản 3 so với bản 2 |
| CT-01 | Đã sửa phân loại: C-17 chỉ còn phần mã nguyên liệu; công thức và xóa mềm chuyển sang A-06 (ASSUMPTION). Q-11 vẫn mở |
| CT-02 | Đã sửa: OPEN_QUESTIONS.md là sổ chuẩn, có bảng mapping Q-* ↔ D-*; D-* giữ nguyên và có cột Q-* |
| DO-01 | Đã sửa phân loại: dòng `audit_log` trả về giá trị nguồn "Máy ghi, Hub gộp"; audit phía Hub ghi là đề xuất bổ sung. Chủ sở hữu vẫn mở tại Q-30 |
| DO-02 | Đã khôi phục bảng ba trạng thái món trong ARCHITECTURE.md |
| SR-01 | Đã ghi phạm vi invariant trong SECURITY_SPEC.md. Chủ khóa ký snapshot vẫn mở tại Q-26 |
| PR-01 | Đã làm rõ nguồn gốc miền 1–999999 trong DATABASE_SPEC.md. Miền cấp phát vẫn mở tại Q-27 |
| FO-01 | Đã ghi chú phạm vi hiện trạng của ma trận suy giảm. Hành vi vẫn mở tại Q-21 |
| SR-02, SR-03, PR-02, FO-02, DP-02 | Không sửa nội dung: đây là câu hỏi mở, theo dõi tại Q-16, Q-30, Q-12, Q-20, Q-21 |

**Đính chính hai nhận định của bản review này:**

- **NQ-06 trùng với Q-16.** §12.2 viết rằng Q-16 "không hỏi về mã hóa, quyền đọc". Nhận định đó sai: Q-16 đã hỏi "mã hóa/ACL/retention" và "ai có quyền đọc". NQ-06 không được tạo thành Q-* riêng. Phần bán kính thiệt hại khi Hub giữ dump thuộc Q-19.
- **NQ-01 đã được hỏi ở dạng ngắn** tại TECH_STACK.md ("khóa ký snapshot thuộc ai?") và nằm trong phạm vi Q-15. Nó vẫn được tách thành Q-26 để theo dõi riêng, vì chủ đề này nằm trong danh sách quyết định cần chủ sở hữu trả lời.

Ánh xạ NQ-* → Q-*: NQ-01 → Q-26, NQ-02 → Q-27, NQ-03 → Q-28, NQ-04 → Q-29, NQ-05 → Q-30, NQ-06 → Q-16 (+Q-19), NQ-07 → Q-31. Sổ theo dõi: [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md).
