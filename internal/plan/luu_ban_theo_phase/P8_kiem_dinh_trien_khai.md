# P8 · Kiểm định và triển khai

- **Trạng thái:** CHƯA THỰC HIỆN.
- **Luồng thiết kế:** mục 11 (toàn bộ mã B, A, G), mục 9 bước 2, mục 13 (rủi ro).

## Mục tiêu

1. Mọi lỗi kiểm định đều có test phản ví dụ chạy đạt.
2. Có số đo thật về tải và mất điện.
3. Đưa server vào dùng thật:
   - từng máy chuyển sang server mẹ;
   - xoá admin_gui khỏi máy;
   - có runbook cho người vận hành.

## Điều kiện vào

- P7 ✓.
- Q2: cài root CA lên thiết bị quản trị và điện thoại nhân viên.
- Q9: máy server, IP cố định, tên in vào cert.
- Q7: dữ liệu ban đầu. Cần cho P8.4.

## Phase con

### P8.1 Test phản ví dụ theo mục 11

Mỗi mã có ít nhất một test tái hiện kịch bản tấn công hoặc hỏng hóc trong bảng mục 11, và test phải đạt trên bản hiện tại. Hacker viết kịch bản, tester đưa vào bộ test.

| Mã | Test (tóm tắt) | Phase đã làm phần sửa |
|---|---|---|
| B1 | Phản chiếu và phát lại response | P4.2 |
| B2 | Giả NTP rồi phát lại lệnh nạp kho | P4.9, P6.2.4 |
| B3 | Khôi phục DB làm trùng `command_id` | P6.1.1, P7 |
| B4 | Mất response, người dùng bấm lại, nạp hai lần | P6 |
| B5 | Gói 401 giả làm máy ngừng đồng bộ | P4.5.2 |
| B6 | Đổi query hoặc status ngoài phần ký | P4.4.7 |
| B7 | Kiosk đọc khoá agent | P3.2 |
| B8 | Mã ghép bị đoán hoặc dùng lại | P4.6 |
| B9 | Máy này ghi kết quả cho lệnh máy khác | P4.4.5, P6.1.5 |
| B10 | XSS từ dữ liệu của máy | P1.7.4, P5.5.3, P6.8 |
| B11 | Flood cổng quản trị làm máy bị coi là offline | P1.2.3, P4.8 |
| B12 | Chuyển vé đã dùng về chưa dùng | P6.4.3 (theo Q3) |
| B13 | Media làm đầy thẻ SD | P5.2.1 |
| B14 | Sai thứ tự kiểm; mốc thu hồi lệch múi giờ | P4.4.1, P1.5.4 |
| A1 | Seal hai lần lặp nonce GCM | P4.2.3 |
| A2 | Verify chạy trước kiểm rẻ | P4.4.1 |
| G2 | Khoá theo giờ khoá oan cả hệ thống | P4.9 |
| G4 | Mất response thành unknown liên tục | P6.1.4 |

- **File:** `tests/p8/counterexamples/test_<mã>.py`.
- **Đạt khi:** tất cả xanh.

### P8.2 Mất điện trên thẻ SD (G3)

| ID | Kịch bản | Đạt khi |
|---|---|---|
| P8.2.1 | Rút điện Pi đúng lúc transaction nạp kho kèm ledger đang commit, lặp nhiều lần | Tồn kho và ledger luôn khớp nhau: cùng có hoặc cùng không |
| P8.2.2 | Rút điện giữa lúc áp menu | DB máy giữ bản cũ hoặc bản mới, không nửa vời |
| P8.2.3 | Ledger mất dù đã flush | Lệnh thành `unknown`, không tự chạy lại |

Ghi số lần thử và kết quả vào `bang_chung/P8.md`. Nếu P8.2.1 có lần không khớp thì dừng, báo user. Không tự đổi cấu hình lưu trữ.

### P8.3 Tải

| ID | Việc | Ghi lại |
|---|---|---|
| P8.3.1 | Giả lập N agent treo long-poll, gửi đơn mỗi 10 s; N theo số máy thật (Q9) cộng biên | p50, p95 thời gian trả lời; CPU, RAM server |
| P8.3.2 | Cùng lúc flood đăng nhập ở cổng quản trị | Không máy nào bị coi là offline |
| P8.3.3 | Đo thời gian từ lúc lưu giá trên trình duyệt tới lúc POS hiện giá mới | p50, p95 |

Plan không đặt ngưỡng. Số đo đưa user xem để chốt.

### P8.4 Chuyển từng máy sang server mẹ

Mỗi máy làm theo thứ tự sau. Xong máy đầu tiên thì dừng lại cho user xem rồi mới làm tiếp.

| Bước | Việc | Kiểm |
|---|---|---|
| 1 | Backup DB máy bằng `deploy/backup.sh` có sẵn | File backup mở được |
| 2 | ⏸ Q7. Lần đầu: nhập dữ liệu của máy vào server (P2.6.4). Những lần sau: so dữ liệu máy với server, báo chỗ lệch | Danh sách lệch được user duyệt |
| 3 | Cài agent và helper (P3.7), ghép máy (P4.6) | Trang Máy hiện "đã ghép" |
| 4 | Gán menu, chờ máy áp | Màn bán hàng hiện đúng menu |
| 5 | Bán thử, kiểm báo cáo trên server | Số đơn khớp |

**Quay lui:** gỡ agent và helper, giữ admin_gui như cũ, khôi phục DB từ bước 1.

### P8.5 Xoá admin_gui trên máy (mục 9 bước 2)

Chỉ làm sau khi máy đó đã qua P8.4.

| ID | Việc | File | Kiểm |
|---|---|---|---|
| P8.5.1 | Bỏ `import admin_gui.serve` và chuyển route admin | `store_gui/serve.py:96`, `:435`, `:569-592` | store_gui khởi động, POS bán được |
| P8.5.2 | Bỏ mục admin_gui | `configuration/served_paths.py:74` | |
| P8.5.3 | Bỏ bước tạo tài khoản admin | `deploy/install.sh:387-402` (phase_account) | Cài mới trên Pi sạch không hỏi tài khoản admin |
| P8.5.4 | Xoá thư mục `admin_gui/` | | `grep -r admin_gui` chỉ còn tài liệu lịch sử |

**Quay lui:** tag git trước P8.5; cài lại bản tag nếu có sự cố.

### P8.6 Thiết bị quản trị và runbook

| ID | Việc |
|---|---|
| P8.6.1 | ⏸ Q2. Cài root CA lên máy tính và điện thoại quản trị, kể cả điện thoại nhân viên bấm "Giữ" ở L4. Ghi từng loại thiết bị đã thử |
| P8.6.2 | Runbook `server/docs/runbook.md`: cài server, tạo CA và cất root ra USB, backup và `restore.sh`, ghép máy, thu hồi, cấp lại leaf khi đổi IP, xác nhận giờ, xử lý lệnh `unknown`, giới hạn "chụp cả ổ đĩa" |
| P8.6.3 | Người vận hành làm thử runbook trên server sạch, không có người viết đứng cạnh |

## Cổng ra P8

- P8.1 đạt.
- P8.2 không có lần nào không khớp.
- P8.3 có số đo, user đã xem.
- Ít nhất một máy thật chạy trên server mẹ không cần admin_gui, sau một thời gian quan sát do user chọn.
- Runbook đã được làm thử.
- Reviewer, cybersecurity, hacker cùng duyệt.
