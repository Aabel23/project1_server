# 🚀 project1_server

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Chào mừng bạn đến với repository **project1_server**. Đây là máy chủ trung tâm xử lý các luồng nghiệp vụ, định tuyến và giao tiếp với các agent trong hệ thống.

---

## 📚 Tài liệu dự án (Documentation)

Toàn bộ thông tin chi tiết về **kiến trúc hệ thống, bản vẽ thiết kế, và kế hoạch phát triển** không được đặt ở đây để tránh làm file README quá dài. 

Vui lòng truy cập vào thư mục `docs` để nắm bắt toàn bộ bối cảnh và định hướng của dự án:

👉 **[Đọc Tài liệu Thiết kế & Kế hoạch tại đây](./docs)** 👈

Trong thư mục `docs`, bạn sẽ tìm thấy:
- 🏗️ **System Architecture:** Sơ đồ khối và luồng dữ liệu.
- 📅 **Project Roadmap:** Kế hoạch phát triển qua từng giai đoạn (Milestones).
- 🔌 **API Specifications:** Chi tiết các endpoint và cách thức giao tiếp.

---

## 📂 Cấu trúc thư mục

- `/agents` - Chứa logic của các agent xử lý tác vụ cụ thể.
- `/docs` - **(Quan trọng)** Tài liệu thiết kế, quy chuẩn và lộ trình.
- `/internal` - Các module dùng chung, core logic nội bộ.
- `/machine` - Quản lý trạng thái và cấu hình máy.
- `/server` - Khởi tạo server và các thiết lập mạng.
- `routing.py` - File định tuyến chính của ứng dụng.

---

## 🛠️ Cài đặt & Khởi chạy (Getting Started)

**1. Clone dự án về máy**
```bash
git clone [https://github.com/Aabel23/project1_server.git](https://github.com/Aabel23/project1_server.git)
cd project1_server
