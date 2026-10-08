# Quy ước sơ đồ cho báo cáo thiết kế (user chốt 2026-10-08)

Mỗi loại sơ đồ chỉ dùng cho đúng một việc.

## 1. Sơ đồ tuần tự (sequence): chuỗi trao đổi giữa NHIỀU bên

- **Dùng khi** cần thể hiện một chuỗi hoạt động qua lại giữa nhiều cá thể, ví dụ bắt tay HTTPS, máy áp menu, đọc nguyên liệu qua long-poll.
- **Bố cục:**
  - Mỗi bên là một cột, có đường đời (lifeline) dọc.
  - Mũi tên được đánh số theo thứ tự.
  - Các giai đoạn ngăn bằng dải tiêu đề, ví dụ "GIAI ĐOẠN 1 · ĐẶT MÓN VÀ IN VÉ".
  - Vòng lặp đặt trong khung `loop`.
  - Ghi chú điều kiện để trong hộp vàng.
  - Phản hồi vẽ nét đứt.

## 2. Sơ đồ khối (flowchart): MỘT luồng đơn lẻ

- **Dùng khi** cần vẽ logic bên trong một tiến trình hoặc một luồng, ví dụ vòng chờ mã QR → dựng công thức → runner kết thúc ra sao.
- **Ký hiệu:**
  - Xử lý vẽ hình chữ nhật.
  - Quyết định vẽ hình thoi.
  - Mỗi nhánh có nhãn.
  - Đường quay lại vòng lặp được vẽ rõ.
- **Màu:**
  - Xử lý: cam.
  - Quyết định và chờ: vàng.
  - Thành công: xanh.
  - Lỗi: đỏ.
- Tham khảo mục 4.1 và 4.x của `FexMix_Munual.html`.

## 3. Sơ đồ tổng quan: dạng "râu"

User phác bằng Paint:

```
SV ─┬─ râu (module/service) ─┐
    ├─ râu (module/service) ─┼─ Secure (middleware) ─ Endpoint ─ Client
    └─ râu (module/service) ─┘
```

- **Mỗi râu là một module hoặc service**, ví dụ gọi món, đồng bộ menu.
- **Trong mỗi râu ghi các tham số dùng để đóng gói tin** (Param1, IP, Param2…).
- **Mọi râu gom về một khối bảo mật (middleware)**, rồi tới một khối endpoint, rồi nối tới client.

### Góp ý đã gửi user (chờ phản hồi)

- **Tách theo hai loại client.** Server có hai loại client là trình duyệt admin và agent trên máy. Mỗi loại đi qua một lớp bảo mật khác nhau: admin dùng session và quyền theo máy, agent dùng HMAC cùng nonce.
- **Vẽ đối xứng hai đầu.** Phía máy cũng có các module (áp menu, báo tồn kho, gửi đơn, chạy lệnh). Đề xuất vẽ: server – bảo mật – endpoint ═ mạng LAN ═ endpoint – bảo mật – module agent.
- **Kho lưu đặt sau các module.** DB nằm phía sau các module. Hàng đợi lệnh/long-poll là module dùng chung, nhiều râu cắm vào nó.
- **Thứ tự request đi vào:** client → endpoint → bảo mật → module → DB. Response đi ngược lại và được ký ở lớp bảo mật.
