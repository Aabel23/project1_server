# Ráp khối và triển khai

- **Trạng thái:** CHƯA THỰC HIỆN.
- **Ráp:** một lần ráp chỉ bắt đầu khi mọi khối trong lần ráp đó đã ✓.
- **Khi lỗi:** lỗi tìm thấy lúc ráp được ghi về khối gây lỗi. Khối đó quay về → cho tới khi test riêng của nó (thêm ca mới tái hiện lỗi) đạt lại. Không vá tại chỗ trong code ráp.
- **Bằng chứng:** mỗi lần ráp ghi kịch bản, môi trường, output, đạt hay chưa vào `bang_chung/R<n>.md`.

## Ráp

### R1 · Quản trị qua HTTPS

- **Khối:** S-DB, S-NET, UI-SHELL, S-SECA, M-ACC, M-MAC (phần trang).
- **Chờ:** Q2 (cài root CA), Q9 (máy server, IP).

| Kịch bản | Đạt khi |
|---|---|
| Mở trang từ máy tính và điện thoại đã cài root CA | Không có cảnh báo cert |
| Đăng nhập, tạo nhân viên, đổi quyền, gán máy | Như admin_gui |
| Manager cửa hàng A đăng nhập | Không thấy máy B |
| `openssl s_client` | Chỉ có TLS 1.3 |
| Flood đăng nhập | 429, cổng agent không bị ảnh hưởng |

### R2 · Menu trên server

- **Khối:** R1 + M-CAT, M-MENU, M-REP.

| Kịch bản | Đạt khi |
|---|---|
| Tạo món, gắn vào hai menu, đổi giá một menu | `menu_version` tăng đúng menu đó |
| Hai người cùng sửa một menu | Người sau nhận 409 |
| Mở trang Báo cáo khi chưa có dữ liệu | Hiện "chưa có dữ liệu" |

### R3 · Máy nối với server

- **Khối:** R1 + S-FM1, M-KEY, M-MAC; trên Pi thử: A-HOST, A-DB, A-NET, H-LOCAL.
- **Chờ:** Q1, Q6.

| Kịch bản | Đạt khi |
|---|---|
| Tạo mã ghép, cài trên Pi thử | Trang Máy hiện "đã ghép", vân tay hai bên khớp |
| Đổi giá trên server | Long-poll đang treo trả lời ngay |
| Thu hồi máy | Máy dừng gửi, vẫn bán; ghép lại được |
| Bộ tấn công của hacker: phát lại, đổi route, đổi byte, kid cũ, mã ghép hết hạn, bundle sai HMAC, hai IP cùng khoá, 401 giả | Mọi ca bị chặn |
| Kiosk đọc khoá agent | Thất bại |

### R4 · Menu xuống máy, dữ liệu lên server

- **Khối:** R2 + R3 + M-PUB, M-ING; trên Pi: A-POS, A-APPLY, A-UP, A-STOCK.

| Kịch bản (mục 3 của thiết kế) | Đạt khi |
|---|---|
| Đổi giá Peach Tea trong menu Quận 1 | POS của máy dùng menu đó hiện giá mới; máy dùng menu khác không đổi |
| Rút mạng máy, đổi giá, cắm lại | Lúc offline bán giá cũ; cắm lại thì áp giá mới |
| Bán 20 ly | Báo cáo có đủ 20 dòng, không trùng |
| Báo cáo `?machine=all` | Gộp đúng theo SKU |
| Món thiếu nguyên liệu trên máy | POS hiện "hết"; trang Máy hiện lý do |

### R5 · Lệnh

- **Khối:** R4 + M-CMD, A-RUN.
- **Chờ:** Q3.

| Kịch bản | Đạt khi |
|---|---|
| Nạp kho, cắt kết nối sau khi máy chạy xong, trước khi server nhận kết quả, người dùng bấm lại | Tồn kho chỉ tăng một lần |
| Thử màn hình, kill agent | 20 s sau màn hình về mode cũ |
| Bấm Giữ màn hình, reboot | Giữ mode mới |
| In lại vé, crash agent ngay sau claimed | Không in lần hai |
| Đổi trạng thái vé | Máy và bản sao trên server cùng đổi |
| Máy offline | Nút gửi lệnh bị khoá; xem nguyên liệu thì hiện bản đệm "chỉ đọc" |

### R6 · Khôi phục

- **Khối:** R5 + S-EPOCH.
- **Chờ:** Q4, Q10.

| Kịch bản | Đạt khi |
|---|---|
| Tạo vài lệnh nạp, backup, chạy thêm lệnh, khôi phục **bằng tay** | Server phát hiện; lệnh đã chạy không chạy lại; máy bị thu hồi sau backup vẫn bị chặn; đối soát hiện đúng danh sách |
| Form mở trước khi khôi phục, bấm gửi sau | 409, không tạo lệnh |
| Mọi phiên đăng nhập cũ | Phải đăng nhập lại |

## Triển khai

### X1 · Test phản ví dụ theo mục 11

- **Việc:** mỗi mã B1–B14, A1, A2, G2, G4 có một test tái hiện kịch bản trong bảng mục 11. Test đặt ở `tests/counterexamples/test_<mã>.py`. Hacker viết kịch bản, tester đưa vào bộ test.
- **Đạt khi:** tất cả xanh.

| Mã | Khối giữ phần sửa |
|---|---|
| B1, A1 | S-FM1, A-NET |
| B2 | S-FM1, A-RUN |
| B3, B4 | M-CMD, A-RUN, S-EPOCH |
| B5 | A-NET |
| B6 | S-FM1 |
| B7 | A-HOST |
| B8 | M-KEY |
| B9 | S-FM1, M-CMD |
| B10 | UI-SHELL, M-REP |
| B11 | S-NET, M-MAC |
| B12 | M-CMD (Q3) |
| B13 | A-APPLY |
| B14 | S-SECA, S-FM1 |
| A2 | S-FM1 |
| G2 | S-FM1 |
| G4 | M-CMD |

### X2 · Mất điện trên thẻ SD (G3)

| Kịch bản | Đạt khi |
|---|---|
| Rút điện Pi đúng lúc transaction nạp kho kèm ledger đang commit, lặp nhiều lần | Tồn kho và ledger luôn khớp |
| Rút điện giữa lúc áp menu | DB máy giữ bản cũ hoặc bản mới, không nửa vời |
| Ledger mất dù đã flush | Lệnh thành unknown, không tự chạy lại |

Có lần không khớp thì dừng, báo user. Không tự đổi cấu hình lưu trữ.

### X3 · Tải

- **Việc:**
  - giả lập N agent treo long-poll, gửi đơn mỗi 10 s, N theo Q9 cộng biên;
  - cùng lúc flood đăng nhập;
  - đo thời gian từ lúc lưu giá tới lúc POS hiện giá.
- **Ghi lại:** p50, p95, CPU, RAM.
- Plan không đặt ngưỡng. Đưa số đo cho user chốt.

### X4 · Chuyển từng máy sang server mẹ

Máy đầu tiên xong thì dừng lại cho user xem rồi mới làm tiếp.

| Bước | Việc | Kiểm |
|---|---|---|
| 1 | Backup DB máy bằng `deploy/backup.sh` | File backup mở được |
| 2 | ⏸ Q7. Lần đầu nhập dữ liệu máy vào server (M-CAT.6); các lần sau so và báo chỗ lệch | User duyệt danh sách lệch |
| 3 | Cài agent và helper, ghép máy | Trang Máy hiện "đã ghép" |
| 4 | Gán menu, chờ áp | POS đúng menu |
| 5 | Bán thử | Báo cáo khớp |

**Quay lui:** gỡ agent và helper, giữ admin_gui, khôi phục DB từ bước 1.

### X5 · Xoá admin_gui trên máy (mục 9 bước 2)

Chỉ làm trên máy đã qua X4.

| Việc | File | Kiểm |
|---|---|---|
| Bỏ import admin_gui và chuyển route admin | `store_gui/serve.py:96`, `:435`, `:569-592` | store_gui khởi động, POS bán được |
| Bỏ mục admin_gui | `configuration/served_paths.py:74` | |
| Bỏ bước tạo tài khoản admin | `deploy/install.sh:387-402` | Cài mới không hỏi tài khoản admin |
| Xoá thư mục `admin_gui/` | | `grep -r admin_gui` chỉ còn tài liệu lịch sử |

**Quay lui:** tag git trước X5; cài lại bản tag nếu có sự cố.

### X6 · Thiết bị và runbook

| Việc | Kiểm |
|---|---|
| ⏸ Q2. Cài root CA lên máy tính, điện thoại quản trị, điện thoại nhân viên | Ghi từng loại thiết bị đã thử |
| Runbook `server/docs/runbook.md`: cài server, tạo CA và cất root ra USB, backup và `restore.sh`, ghép máy, thu hồi, cấp lại leaf khi đổi IP, xác nhận giờ, xử lý lệnh unknown, giới hạn "chụp cả ổ đĩa" | Người vận hành làm thử trên server sạch, không có người viết đứng cạnh |

## Tuỳ chọn, chỉ mở khi user yêu cầu

| Việc | Đã chuẩn bị sẵn |
|---|---|
| Xoay khoá máy định kỳ | Cột `generation`, `alg`, trạng thái `retiring` (M-KEY) |
| Manifest khoá server ký bằng root offline | Response có chỗ công bố khoá kế tiếp |
| Witness, chuỗi hash, audit challenge | |
| NTS cho chrony | Máy đã trỏ NTP về server (A-HOST.7) |
| Profile cho app Android theo R5 (Q5) | |
| ECDSA P-256 thay Ed25519 (nếu đổi ý ở Q1) | Cột `alg` |
