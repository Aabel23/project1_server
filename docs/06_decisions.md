# Nhật ký quyết định

> File này ghi câu trả lời OWNER dạng **DRAFT** và quyết định **ACCEPTED** sau khi văn bản được xác nhận. Câu hỏi chưa quyết định được theo dõi tại [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md). Ràng buộc và giả định rút từ nguồn nằm tại [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md). Nguồn kiến trúc: [Kien_Truc_Doi_May.html](../Kien_Truc_Doi_May.html), bản 3.
>
> **Đã ghi 9 DRAFT ngày 17/09/2026; chưa có ACCEPTED.** Ngày ghi không phải ngày OWNER quyết định. Cập nhật đặc tả theo DRAFT chưa là căn cứ triển khai.

## 1. Quy ước ID quyết định

- Dạng `DEC-NNN`, ba chữ số, cấp tuần tự từ `DEC-001`.
- Một ID đã cấp không bao giờ được cấp lại hay đổi nghĩa, kể cả khi quyết định bị bác bỏ hoặc bị thay thế.
- Mỗi quyết định phải trả lời **ít nhất một** câu `Q-*` trong [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md). `Q-*` là khóa truy nguyên chính.
- `D-*` trong ARCHITECTURE_DECISIONS.md chỉ được ghi kèm để truy nguyên, lấy theo bảng mapping trong OPEN_QUESTIONS.md. Không tạo quyết định chỉ trỏ tới `D-*` mà không có `Q-*`.
- Một quyết định có thể trả lời nhiều `Q-*`. Một `Q-*` có thể cần nhiều quyết định nếu chủ sở hữu trả lời từng phần; khi phần đã trả lời có DEC `ACCEPTED`, `Q-*` giữ trạng thái `PARTIAL`; nếu chỉ có DRAFT thì Q vẫn `OPEN`.
- Không đánh số lại `Q-*`, `D-*`, `C-*`, `A-*`, `REQ-*` khi ghi quyết định.

## 2. Quy ước trạng thái

### Trạng thái của một quyết định (`DEC-*`)

| Trạng thái | Nghĩa | Được dùng làm căn cứ triển khai? |
|---|---|---|
| `DRAFT` | Đã ghi lại câu trả lời nhưng chủ sở hữu chưa xác nhận văn bản | Không |
| `ACCEPTED` | Chủ sở hữu đã xác nhận; có ngày và người quyết định | Có |
| `REJECTED` | Phương án được xem xét và bị bác; câu hỏi vẫn còn mở | Không |
| `SUPERSEDED` | Đã bị thay bởi một `DEC-*` mới; ghi ID thay thế | Không, dùng quyết định thay thế |
| `DEFERRED` | Chủ sở hữu chủ động hoãn; ghi điều kiện hoặc mốc xem lại | Không |

### Trạng thái của một câu hỏi (`Q-*`, ghi tại OPEN_QUESTIONS.md)

| Trạng thái | Nghĩa |
|---|---|
| `OPEN` | Chưa có quyết định ACCEPTED; có thể có câu trả lời DRAFT |
| `PARTIAL` | Đã có `DEC-*` `ACCEPTED` cho một phần; phần còn lại ghi rõ |
| `DECIDED` | Mọi phần đã có `DEC-*` `ACCEPTED` |
| `DEFERRED` | Có `DEC-*` `DEFERRED`; câu hỏi chưa được trả lời |

Mức độ câu trả lời được ghi riêng ở OPEN_QUESTIONS: DRAFT đủ/một phần không làm Q thành DECIDED/PARTIAL. “Chưa quyết định” hoặc nhóm CAN DECIDE LATER không tự đồng nghĩa OWNER đã DEFERRED.

## 3. Quy trình ghi quyết định

1. Chủ sở hữu trả lời một hoặc nhiều `Q-*`.
2. Tạo mục `DEC-NNN` theo template ở §4 với trạng thái `DRAFT`, ghi **nguyên văn hoặc sát nghĩa** câu trả lời. Không bổ sung phần chủ sở hữu chưa nói.
3. Chủ sở hữu xác nhận văn bản, chuyển sang `ACCEPTED` và điền ngày, người quyết định.
4. Tại OPEN_QUESTIONS.md, cập nhật cột trạng thái và cột `DEC-*` của `Q-*` tương ứng. **Không xóa** nội dung câu hỏi.
5. Cập nhật các tài liệu và ID bị ảnh hưởng đã liệt kê trong quyết định. Nếu một `A-*` được chấp thuận hoặc bác, ghi `DEC-*` tại dòng đó thay vì đổi nhãn im lặng.
6. Nếu quyết định sinh câu hỏi mới, thêm `Q-*` mới vào OPEN_QUESTIONS.md; không ghi câu hỏi mới vào file này.

## 4. Template

```markdown
### DEC-NNN — <tiêu đề ngắn>

| Trường | Giá trị |
|---|---|
| Trạng thái | DRAFT / ACCEPTED / REJECTED / SUPERSEDED / DEFERRED |
| Trả lời câu hỏi | Q-xx (bắt buộc), ... |
| D-* truy nguyên | D-xx, ... hoặc "không có" |
| Ràng buộc/giả định liên quan | C-xx, A-xx, REQ-xx, ... |
| Ngày quyết định | YYYY-MM-DD |
| Người quyết định | <tên hoặc vai trò> |
| Người ghi | <tên hoặc vai trò> |
| Thay thế cho | DEC-xxx hoặc "không" |
| Bị thay bởi | DEC-xxx hoặc "không" |

**Câu hỏi.** Trích câu hỏi từ Q-xx.

**Phương án đã có trong tài liệu.** Liệt kê các phương án nguồn hoặc tài liệu đã nêu, kèm đánh đổi như tài liệu ghi. Không thêm phương án mới ở đây.

**Quyết định.** Câu trả lời của chủ sở hữu.

**Lý do.** Lý do do chủ sở hữu nêu. Để trống nếu không có, không tự điền.

**Phạm vi.** Phần nào của câu hỏi được trả lời; phần nào còn mở.

**Hệ quả cho tài liệu.** File và ID cần cập nhật.

**Câu hỏi phát sinh.** Q-* mới đã thêm vào OPEN_QUESTIONS.md, nếu có.
```

## 5. Sổ quyết định

| ID | Tiêu đề | Trả lời | Trạng thái | Ngày |
|---|---|---|---|---|
| DEC-001 | Thực đơn chung toàn đội | Q-01 | DRAFT | OWNER chưa cung cấp |
| DEC-002 | Chấp nhận mất khóa QR | Q-04 | DRAFT | OWNER chưa cung cấp |
| DEC-003 | Không có vé liên máy | Q-05 | DRAFT | OWNER chưa cung cấp |
| DEC-004 | Thu tiền lúc in nhãn | Q-07 | DRAFT | OWNER chưa cung cấp |
| DEC-005 | Giờ mở cửa và người nhận cảnh báo | Q-08 | DRAFT | OWNER chưa cung cấp |
| DEC-006 | Ghim recipe vào ticket | Q-11 | DRAFT | OWNER chưa cung cấp |
| DEC-007 | Không nhận order khi boot offline chưa sync clock | Q-21 | DRAFT | OWNER chưa cung cấp |
| DEC-008 | Baseline công nghệ Hub | Q-24 | DRAFT | OWNER chưa cung cấp |
| DEC-009 | MID 1–999999 và không tái sử dụng | Q-27 | DRAFT | OWNER chưa cung cấp |


### DEC-001 — Thực đơn chung toàn đội

| Trường | Giá trị |
|---|---|
| Trạng thái | DRAFT |
| Trả lời câu hỏi | Q-01 |
| D-* truy nguyên | D-01 |
| Ràng buộc/giả định liên quan | A-01, C-06 |
| Ngày quyết định | OWNER chưa cung cấp |
| Ngày ghi | 2026-09-17 |
| Người quyết định | OWNER (theo nhãn biểu mẫu; chưa có tên) |
| Người ghi | Codex — ghi chép tài liệu |
| Thay thế cho | Không |
| Bị thay bởi | Không |

**Câu hỏi.** Một thực đơn chung cả đội, hay mỗi điểm bán một thực đơn?

**Nguồn trả lời.** [DECISION_QUESTIONNAIRE.md](DECISION_QUESTIONNAIRE.md), ô Q-01.

**Phương án đã có trong tài liệu.** Chỉ có **một giả định** của tác giả (A-01 trong ARCHITECTURE_DECISIONS.md; A-06 là khuyến nghị cửa sổ yên tĩnh): "một danh mục chung, ghi đè giá và trạng thái bán theo từng điểm, và tập món pha được thì tự tính từ bản đồ khe cắm". Tài liệu không mô tả phương án "mỗi điểm một thực đơn" như một thiết kế đầy đủ.

**Quyết định — nguyên văn OWNER.**

> - Một thực đơn chung cho cho cả đội

**Lý do.** OWNER không nêu.

**Phạm vi.** Chốt thực đơn chung; chưa xác nhận override giá/trạng thái theo điểm, không duyệt toàn bộ A-01.

**Hệ quả cho tài liệu.** [ARCHITECTURE.md](ARCHITECTURE.md), [DATABASE_SPEC.md](DATABASE_SPEC.md), [API_PROTOCOL.md](API_PROTOCOL.md), [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md), [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md); [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md), Q-01.

**Câu hỏi phát sinh.** Không tạo Q mới; phần chưa trả lời giữ tại Q hiện hữu.


### DEC-002 — Chấp nhận mất khóa QR

| Trường | Giá trị |
|---|---|
| Trạng thái | DRAFT |
| Trả lời câu hỏi | Q-04 |
| D-* truy nguyên | D-04 |
| Ràng buộc/giả định liên quan | C-20, REQ-17 |
| Ngày quyết định | OWNER chưa cung cấp |
| Ngày ghi | 2026-09-17 |
| Người quyết định | OWNER (theo nhãn biểu mẫu; chưa có tên) |
| Người ghi | Codex — ghi chép tài liệu |
| Thay thế cho | Không |
| Bị thay bởi | Không |

**Câu hỏi.** Khóa QR: chấp nhận mất, hay ký gửi?

**Nguồn trả lời.** [DECISION_QUESTIONNAIRE.md](DECISION_QUESTIONNAIRE.md), ô Q-04.

**Phương án đã có trong tài liệu.** Ba lựa chọn, nguyên văn từ SECURITY_SPEC.md/nguồn: (a) **Chấp nhận mất** — "đơn giản nhất, an toàn nhất. Mất tối đa một ngày vé của một tiệm." Nguồn ghi là khuyến nghị. (b) **Ký gửi khóa ở Hub** — "khôi phục được, nhưng Hub bị chiếm quyền là lộ khóa của cả đội." (c) **Ký gửi ngoại tuyến** — "in khóa ra giấy lúc cài đặt, cất két. `install.sh` đã in nó ra màn hình kèm cảnh báo — chỉ cần biến việc cất giữ thành thủ tục bắt buộc."

**Quyết định — nguyên văn OWNER.**

> -Chấp nhận mất

**Lý do.** OWNER không nêu.

**Phạm vi.** Đủ câu trả lời lựa chọn mất khóa hay ký gửi. Backup tổng thể vẫn mở tại Q-16.

**Hệ quả cho tài liệu.** [SECURITY_SPEC.md](SECURITY_SPEC.md), [DEPLOYMENT.md](DEPLOYMENT.md), [DATABASE_SPEC.md](DATABASE_SPEC.md), [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md), [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md); [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md), Q-04.

**Câu hỏi phát sinh.** Không tạo Q mới; phần chưa trả lời giữ tại Q hiện hữu.


### DEC-003 — Không có vé liên máy

| Trường | Giá trị |
|---|---|
| Trạng thái | DRAFT |
| Trả lời câu hỏi | Q-05 |
| D-* truy nguyên | D-05 |
| Ràng buộc/giả định liên quan | C-02 |
| Ngày quyết định | OWNER chưa cung cấp |
| Ngày ghi | 2026-09-17 |
| Người quyết định | OWNER (theo nhãn biểu mẫu; chưa có tên) |
| Người ghi | Codex — ghi chép tài liệu |
| Thay thế cho | Không |
| Bị thay bởi | Không |

**Câu hỏi.** Có bao giờ khách đặt ở máy này rồi lấy ở máy khác không?

**Nguồn trả lời.** [DECISION_QUESTIONNAIRE.md](DECISION_QUESTIONNAIRE.md), ô Q-05.

**Phương án đã có trong tài liệu.** Nguồn chỉ nói: "Không trong thiết kế hiện tại; nếu có, thẩm quyền về vé phải chuyển lên Hub và QR cần chế độ liên máy — việc lớn, thiết kế riêng." Không có thiết kế cụ thể nào cho nhánh "có".

**Quyết định — nguyên văn OWNER.**

> -Không

**Lý do.** OWNER không nêu.

**Phạm vi.** Đủ câu trả lời về phạm vi vé liên máy.

**Hệ quả cho tài liệu.** [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DATABASE_SPEC.md](DATABASE_SPEC.md), [API_PROTOCOL.md](API_PROTOCOL.md), [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md); [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md), Q-05.

**Câu hỏi phát sinh.** Không tạo Q mới; phần chưa trả lời giữ tại Q hiện hữu.


### DEC-004 — Thu tiền lúc in nhãn

| Trường | Giá trị |
|---|---|
| Trạng thái | DRAFT |
| Trả lời câu hỏi | Q-07 |
| D-* truy nguyên | D-07 |
| Ràng buộc/giả định liên quan | REQ-12 |
| Ngày quyết định | OWNER chưa cung cấp |
| Ngày ghi | 2026-09-17 |
| Người quyết định | OWNER (theo nhãn biểu mẫu; chưa có tên) |
| Người ghi | Codex — ghi chép tài liệu |
| Thay thế cho | Không |
| Bị thay bởi | Không |

**Câu hỏi.** Khách trả tiền lúc nào: lúc in nhãn, hay lúc nhận ly?

**Nguồn trả lời.** [DECISION_QUESTIONNAIRE.md](DECISION_QUESTIONNAIRE.md), ô Q-07.

**Phương án đã có trong tài liệu.** Nguồn không liệt kê hai phương án đầy đủ, chỉ nêu hệ quả của mỗi nhánh: "Nếu tiệm thu tiền lúc in nhãn thì mọi nhãn khách bỏ đi là tiền đã thu mà không sổ nào ghi. Nếu thu lúc nhận ly thì con số hiện tại đã đúng, và 'vé phát hành nhưng chưa quét' chỉ là chỉ dấu thiết bị hỏng chứ không phải chỉ dấu thất thoát."

**Quyết định — nguyên văn OWNER.**

> - Lúc in nhãn

**Lý do.** OWNER không nêu.

**Phạm vi.** Chốt thời điểm thu tiền; chưa xác nhận mô hình báo cáo thay thế. Không tự thêm schema thanh toán, hoàn tiền hoặc reservation; Q-17 vẫn mở.

**Hệ quả cho tài liệu.** [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md), [DATABASE_SPEC.md](DATABASE_SPEC.md), [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md), [DEPLOYMENT.md](DEPLOYMENT.md), [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md); [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md), Q-07.

**Câu hỏi phát sinh.** Không tạo Q mới; phần chưa trả lời giữ tại Q hiện hữu.


### DEC-005 — Giờ mở cửa và người nhận cảnh báo

| Trường | Giá trị |
|---|---|
| Trạng thái | DRAFT |
| Trả lời câu hỏi | Q-08 |
| D-* truy nguyên | D-08 |
| Ràng buộc/giả định liên quan | C-29, REQ-18 |
| Ngày quyết định | OWNER chưa cung cấp |
| Ngày ghi | 2026-09-17 |
| Người quyết định | OWNER (theo nhãn biểu mẫu; chưa có tên) |
| Người ghi | Codex — ghi chép tài liệu |
| Thay thế cho | Không |
| Bị thay bởi | Không |

**Câu hỏi.** Giờ mở cửa của mỗi điểm bán, và ai trực khi có cảnh báo?

**Nguồn trả lời.** [DECISION_QUESTIONNAIRE.md](DECISION_QUESTIONNAIRE.md), ô Q-08.

**Phương án đã có trong tài liệu.** Không có phương án kỹ thuật để lựa chọn; chỉ có một quy tắc phòng hờ nếu câu hỏi tổ chức chưa có lời giải: "Nếu chưa có người trực thì nguồn yêu cầu hạ mọi thứ xuống 'trong ngày' và nói thật điều đó, thay vì để một mức khẩn cấp mà không ai nhận."

**Quyết định — nguyên văn OWNER.**

> - Giờ mở cửa: 08:00–22:00 mỗi ngày.
> - Người nhận cảnh báo: quản lý cửa hàng.
> - Ngoài giờ có người trực: không.
> - Cảnh báo ngoài giờ: xử lý trong ngày.

**Lý do.** OWNER không nêu.

**Phạm vi.** Chốt 08:00–22:00 mỗi ngày, quản lý cửa hàng nhận cảnh báo, không trực ngoài giờ, ngoài giờ xử lý trong ngày. Múi giờ và cách xử lý cuối ngày chưa rõ; không tự đổi thành ngày làm việc kế tiếp hoặc đặt SLA.

**Hệ quả cho tài liệu.** [DEPLOYMENT.md](DEPLOYMENT.md), [DATABASE_SPEC.md](DATABASE_SPEC.md), [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md), [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md); [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md), Q-08.

**Câu hỏi phát sinh.** Không tạo Q mới; phần chưa trả lời giữ tại Q hiện hữu.


### DEC-006 — Ghim recipe vào ticket

| Trường | Giá trị |
|---|---|
| Trạng thái | DRAFT |
| Trả lời câu hỏi | Q-11 |
| D-* truy nguyên | D-14 |
| Ràng buộc/giả định liên quan | A-06, C-17, REQ-09 |
| Ngày quyết định | OWNER chưa cung cấp |
| Ngày ghi | 2026-09-17 |
| Người quyết định | OWNER (theo nhãn biểu mẫu; chưa có tên) |
| Người ghi | Codex — ghi chép tài liệu |
| Thay thế cho | Không |
| Bị thay bởi | Không |

**Câu hỏi.** Cửa sổ yên tĩnh: điều kiện chính xác để áp thay đổi công thức, mã nguyên liệu, xóa mềm

**Nguồn trả lời.** [DECISION_QUESTIONNAIRE.md](DECISION_QUESTIONNAIRE.md), ô Q-11.

**Phương án đã có trong tài liệu.** Với **công thức**, nguồn nêu ba phương án đầy đủ: (a) **Chấp nhận** — rẻ nhất, là hành vi hiện tại; hỏng khi có người sửa công thức lúc đông khách. (b) **Ghim công thức vào vé** — đúng nhất, nhưng phải lưu công thức đã biên dịch vào `order_ticket` — cột mới lớn, migration nặng. (c) **Áp lúc yên tĩnh** — không cần đổi schema; chậm nhất 24 giờ vì vé tự hết hạn; nguồn ghi "tôi khuyên cách thứ ba" — đây là khuyến nghị, chưa duyệt. Với **mã nguyên liệu**, quy tắc cửa sổ yên tĩnh (mốc đến sau giữa hết vé chưa quét và 24 giờ) được nguồn phát biểu như một luật, không phải một trong nhiều lựa chọn.

**Quyết định — nguyên văn OWNER.**

> Trả lời của OWNER:
> 
> Chọn phương án pin recipe vào ticket.
> 
> Recipe của ticket được cố định tại thời điểm tạo ticket.
> Recipe mới chỉ áp dụng cho các ticket được tạo sau khi version mới được publish.
> Không thay đổi recipe của ticket đang tồn tại.

**Lý do.** OWNER không nêu.

**Phạm vi.** Chốt ghim recipe tại thời điểm tạo ticket, không đổi recipe ticket đang tồn tại. Chưa chốt xóa mềm, mã nguyên liệu, lưu trữ/migration, nguyên tử issue/claim, và publish tại Hub so với apply tại máy offline.

**Hệ quả cho tài liệu.** [ARCHITECTURE.md](ARCHITECTURE.md), [DATABASE_SPEC.md](DATABASE_SPEC.md), [API_PROTOCOL.md](API_PROTOCOL.md), [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md), [DEPLOYMENT.md](DEPLOYMENT.md), [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md); [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md), Q-11.

**Câu hỏi phát sinh.** Không tạo Q mới; phần chưa trả lời giữ tại Q hiện hữu.


### DEC-007 — Không nhận order khi boot offline chưa sync clock

| Trường | Giá trị |
|---|---|
| Trạng thái | DRAFT |
| Trả lời câu hỏi | Q-21 (mapping biên tập đề nghị, chưa được OWNER xác nhận) |
| Ô nguồn thực tế | Q-22; không trả lời nội dung sync_menu của Q-22 |
| D-* truy nguyên | D-24 (phần thời gian) |
| Ràng buộc/giả định liên quan | C-01, C-29, REQ-01 |
| Ngày quyết định | OWNER chưa cung cấp |
| Ngày ghi | 2026-09-17 |
| Người quyết định | OWNER (theo nhãn biểu mẫu; chưa có tên) |
| Người ghi | Codex — ghi chép tài liệu |
| Thay thế cho | Không |
| Bị thay bởi | Không |

**Câu hỏi.** Trình tự lỗi chặn và đồng bộ thời gian khi boot offline

**Nguồn trả lời.** [DECISION_QUESTIONNAIRE.md](DECISION_QUESTIONNAIRE.md), ô Q-22.

**Phương án đã có trong tài liệu.** Không có phương án phần mềm đầy đủ. Nguồn chỉ đề xuất: bắt buộc `systemd-timesyncd`, thêm `After=time-sync.target`/`Wants=time-sync.target` vào service (hiện chỉ có `After=network.target mysql.service`), và với "máy hay mất điện, một mô-đun RTC I2C gắn thêm là vài chục nghìn đồng" — đây là giảm nhẹ phần cứng, không giải quyết trường hợp không có RTC và không có mạng khi boot.

**Quyết định — nguyên văn OWNER.**

> Không cho phép Machine nhận order khi
> khởi động offline và chưa sync được clock.

**Lý do.** OWNER không nêu.

**Phạm vi.** Nội dung trả lời điều kiện boot Q-21 nhưng nằm trong ô Q-22; giữ vị trí nguồn và chờ OWNER xác nhận mapping khi duyệt DRAFT. Q-22 chưa có đáp án sync_menu. RTC, tiêu chí sync clock và trình tự pha 00/01 vẫn mở.

**Hệ quả cho tài liệu.** [ARCHITECTURE.md](ARCHITECTURE.md), [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md), [DEPLOYMENT.md](DEPLOYMENT.md), [SECURITY_SPEC.md](SECURITY_SPEC.md), [API_PROTOCOL.md](API_PROTOCOL.md), [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md); [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md), Q-21.

**Câu hỏi phát sinh.** Không tạo Q mới; phần chưa trả lời giữ tại Q hiện hữu.


### DEC-008 — Baseline công nghệ Hub

| Trường | Giá trị |
|---|---|
| Trạng thái | DRAFT |
| Trả lời câu hỏi | Q-24 |
| D-* truy nguyên | D-10 |
| Ràng buộc/giả định liên quan | A-02 (MySQL 8), A-03 (công nghệ), A-04 (Jinja2/long-poll) |
| Ngày quyết định | OWNER chưa cung cấp |
| Ngày ghi | 2026-09-17 |
| Người quyết định | OWNER (theo nhãn biểu mẫu; chưa có tên) |
| Người ghi | Codex — ghi chép tài liệu |
| Thay thế cho | Không |
| Bị thay bởi | Không |

**Câu hỏi.** Chấp thuận stack Hub (Python/FastAPI/MySQL...) và phiên bản cụ thể

**Nguồn trả lời.** [DECISION_QUESTIONNAIRE.md](DECISION_QUESTIONNAIRE.md), ô Q-24.

**Phương án đã có trong tài liệu.** TECH_STACK.md đề xuất **một** baseline duy nhất: Python; FastAPI + Pydantic + Uvicorn; MySQL 8; SQLAlchemy + PyMySQL; Alembic; giao diện Jinja2 render phía server; long-poll cho lệnh; Nginx làm reverse proxy; systemd quản lý tiến trình; pytest + MySQL container để test. Tài liệu tự ghi: "nguồn không có tên framework trong nguồn" — tức đây hoàn toàn là đề xuất, không phải trích từ HTML gốc. Không có phương án thay thế nào được liệt kê để so sánh.

**Quyết định — nguyên văn OWNER.**

> Đồng ý. Phê duyệt bộ Tech Stack được đề xuất
> làm baseline cho Hub:
> 
> Python, FastAPI, Pydantic, Uvicorn,
> MySQL 8, SQLAlchemy, PyMySQL, Alembic,
> Jinja2, Long-poll, Nginx, systemd, pytest
> và MySQL container cho development.

**Lý do.** OWNER không nêu.

**Phạm vi.** Chốt đúng danh sách OWNER nêu, gồm MySQL container cho development. Chưa chốt phiên bản cụ thể ngoài dòng MySQL 8, đóng gói, VM, worker, hàng đợi MySQL, volume assets hay repo. Không suy rộng thành duyệt toàn bộ A-02/A-03/A-04.

**Hệ quả cho tài liệu.** [TECH_STACK.md](TECH_STACK.md), [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md), [API_PROTOCOL.md](API_PROTOCOL.md), [DEPLOYMENT.md](DEPLOYMENT.md), [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md), [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md); [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md), Q-24.

**Câu hỏi phát sinh.** Không tạo Q mới; phần chưa trả lời giữ tại Q hiện hữu.


### DEC-009 — MID 1–999999 và không tái sử dụng

| Trường | Giá trị |
|---|---|
| Trạng thái | DRAFT |
| Trả lời câu hỏi | Q-27 |
| D-* truy nguyên | Không có |
| Ràng buộc/giả định liên quan | C-05, REQ-02 |
| Ngày quyết định | OWNER chưa cung cấp |
| Ngày ghi | 2026-09-17 |
| Người quyết định | OWNER (theo nhãn biểu mẫu; chưa có tên) |
| Người ghi | Codex — ghi chép tài liệu |
| Thay thế cho | Không |
| Bị thay bởi | Không |

**Câu hỏi.** Miền giá trị MID khi Hub cấp phát

**Nguồn trả lời.** [DECISION_QUESTIONNAIRE.md](DECISION_QUESTIONNAIRE.md), ô Q-27.

**Phương án đã có trong tài liệu.** Không có.

**Quyết định — nguyên văn OWNER.**

> MID là số nguyên dương trong khoảng 1–999999.
> 
> MID đã cấp không được tái sử dụng, kể cả khi machine
> bị decommission hoặc thay thế.

**Lý do.** OWNER không nêu.

**Phạm vi.** Chốt MID nguyên dương 1–999999, không tái sử dụng kể cả decommission/thay thế. Chưa xác nhận giới hạn bit/payload QR; chưa trả lời quan hệ định danh Q-12.

**Hệ quả cho tài liệu.** [DATABASE_SPEC.md](DATABASE_SPEC.md), [API_PROTOCOL.md](API_PROTOCOL.md), [SECURITY_SPEC.md](SECURITY_SPEC.md), [DEPLOYMENT.md](DEPLOYMENT.md), [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md), [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md); [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md), Q-27.

**Câu hỏi phát sinh.** Không tạo Q mới; phần chưa trả lời giữ tại Q hiện hữu.
