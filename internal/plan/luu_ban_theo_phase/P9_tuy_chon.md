# P9 · Tuỳ chọn

- **Trạng thái:** CHƯA THỰC HIỆN. Chỉ mở khi user yêu cầu, hoặc khi có số đo hay sự cố cho thấy cần.
- **Nguồn:** mục 4.7 (các phần R5 "hoãn P7") và mục 13 của thiết kế.

| ID | Việc | Khi nào nên làm | Đã chuẩn bị sẵn |
|---|---|---|---|
| P9.1 | Xoay khoá máy định kỳ | Khi Pi có chip giữ khoá, hoặc user yêu cầu | Cột `generation`, `alg`, trạng thái `retiring` đã có ở P4.3.3 |
| P9.2 | Manifest khoá server ký bằng root offline | Khi cần xoay khoá KEM server mà không ghép lại mọi máy | Response đã có chỗ công bố khoá kế tiếp (mục 4.6) |
| P9.3 | Witness, chuỗi hash, audit challenge | Khi user cần bằng chứng chống sửa lịch sử | |
| P9.4 | NTS cho chrony bằng cert của CA nội bộ | Khi giả NTP trong LAN thành vấn đề thật | Máy đã trỏ NTP về server (P3.6) |
| P9.5 | Profile cho app Android theo R5 nói chuyện trực tiếp với server mẹ | Nếu Q5 trả lời "có" | |
| P9.6 | ECDSA P-256 + deterministic_signing thay Ed25519, để bám R5 sát hơn | Nếu user đổi ý ở Q1 | Cột `alg` |

Mỗi việc khi được mở sẽ có file đặc tả riêng: mục tiêu, bước, kiểm, quay lui, như các phase P0–P8.
