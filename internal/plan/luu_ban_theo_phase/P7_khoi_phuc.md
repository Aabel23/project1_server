# P7 · Khôi phục DB server

- **Trạng thái:** CHƯA THỰC HIỆN.
- **Luồng thiết kế:** M6. Lỗi kiểm định: B3, B4 (phần restore).

## Mục tiêu

Khi DB server được nạp lại từ bản sao lưu, server tự phát hiện, kể cả khi người vận hành khôi phục bằng tay mà không chạy script. Sau đó server:

- không chạy lại lệnh đã chạy;
- không làm sống lại máy đã bị thu hồi;
- đối soát được với máy.

## Điều kiện vào

- P6 ✓.
- Q4: N giờ gửi lại ledger. Chặn P7.3.
- Q10: route để máy gửi lại ledger. Chặn P7.3.

## Đầu ra

| Đầu ra | File |
|---|---|
| Phát hiện epoch | `security/epoch.py` |
| Script khôi phục | `deploy/server/restore.sh` |
| Đối soát lệnh | `modules/commands/reconcile.py` |
| Test | `tests/p7/` |

## Phase con

### P7.1 Epoch phía server

| ID | Việc | Kiểm |
|---|---|---|
| P7.1.1 | `server_epoch` là 16 byte ngẫu nhiên, nằm ở bảng `server_state` và file `/var/lib/flexmix-server/epoch`. Bản sao lưu chỉ có DB, không có file | Backup không chứa file epoch |
| P7.1.2 | So epoch khi khởi động **và** trong transaction claim (P4.4.4) | Khôi phục DB khi server đang chạy: request kế tiếp đã thấy epoch lệch |
| P7.1.3 | Lệch hoặc thiếu file thì: sinh epoch mới; lệnh `queued` và `offered` thành `unknown`; đổi khoá ký token phiên (mọi phiên đăng nhập lại); áp lại `revoked.list`; hiện banner "vừa khôi phục, cần đối soát" | Test từng hệ quả |

### P7.2 Epoch phía trình duyệt

- **Việc:** form gửi kèm `server_epoch` lấy lúc tải trang. Epoch khác thì server trả 409 "tải lại trang". P2.4.4 và P6.3.2 đã làm; ở đây kiểm lại sau khôi phục thật.
- **Kiểm:** mở form, khôi phục DB, bấm gửi: nhận 409, không tạo lệnh.

### P7.3 Máy thấy epoch đổi và đối soát

| ID | Việc | Kiểm |
|---|---|---|
| P7.3.1 | Response nào cũng mang `server_epoch`. Agent thấy khác bản đã lưu thì vào chế độ đối soát | Test |
| P7.3.2 | ⏸ Q10. Gửi lại ledger N giờ gần nhất, kể cả dòng đã ack | Server nhận đủ |
| P7.3.3 | Đặt lại con trỏ đơn và lỗi, gửi lại (upsert nên không trùng) | Số dòng `sale` không tăng ảo |
| P7.3.4 | Gửi hello với menu đang áp (epoch, version, sha256) | Server biết bản đang áp |
| P7.3.5 | Server giải lệnh `unknown` theo ledger. Liệt kê lệnh máy đã chạy mà server không có, để người vận hành xem | Trang hiện danh sách |

Ledger trên máy phải giữ ít nhất N giờ và không xoá dòng `unknown` chưa đối soát (P6.2.6).

### P7.4 restore.sh

- **Việc:** dừng service, nạp DB, sinh epoch mới, khởi động. Đây là đường khuyên dùng; P7.1 vẫn bắt được khi không dùng script.
- **Kiểm:** chạy trên server thử với một bản backup cũ hơn vài lệnh.

## Cổng ra P7

Tester làm đủ các bước sau:

1. Tạo vài lệnh nạp kho.
2. Backup.
3. Chạy thêm lệnh.
4. Khôi phục **bằng tay**, không dùng `restore.sh`.

Đạt khi:

- server phát hiện việc khôi phục;
- lệnh đã chạy sau backup không chạy lại;
- máy bị thu hồi sau backup vẫn bị chặn;
- đối soát hiện đúng danh sách.

`pytest tests/p7 -q` đạt.

## Giới hạn

Chụp và khôi phục cả ổ đĩa, DB và file cùng lúc, thì không phát hiện được. Thiết kế đã ghi giới hạn này; P8 ghi vào runbook.
