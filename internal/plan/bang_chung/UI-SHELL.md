# Bằng chứng UI-SHELL · Codex tiếp quản Claude

Ngày 08/10/2026 (Bangkok). User giao Codex làm tiếp vì Claude hết token.
Trạng thái: code và kiểm trên máy dev đã có, chưa nghiệm thu trình duyệt R1.
Review độc lập không có lỗi mới đủ bằng chứng trong code/stub; kiểm Node lại
đạt sau sửa các khối nền. Xem [REVIEW_CODEX.md](REVIEW_CODEX.md).

- `server/static/shell/admin.css`: chép CSS từ version1.0, đổi đường dẫn font.
- `server/static/shell/fonts/`: bốn font cục bộ và hai giấy phép từ version1.0.
- `server/static/shell/admin-guard.js`: API cookie, guard, thanh bên, tên tài
  khoản, picker máy, chữ an toàn và request key.
- `tests/ui_shell/check_shell.cjs`: kiểm bằng Node và stub DOM/API, không npm.

API: `api(path, body)` GET khi thiếu body, POST JSON khi có body, tự gửi
`X-FM-Req: 1`, cookie cùng origin và không cache. Không tự gửi lại request.
Khi có 401, hủy mọi request đang chờ và chuyển tới `login.html`; response cũ
không trả dữ liệu để cập nhật màn hình. Key do `newRequestKey()` sinh bằng
`crypto.randomUUID()` một lần khi mở form, caller giữ key trong bộ nhớ.

`setText(el, value)` dùng textContent; tên máy, tên tài khoản, toast và nhãn
đều không chèn HTML. `machinePicker(mount, machines, onChange)` nhận danh sách
`{machine_id, name}`, trả select có label; danh sách rỗng khóa select.
`await AdminAuth.initPage(active)` đọc WHOAMI, dựng thanh bên theo `pages`,
trả false khi lỗi hoặc không có quyền. Việc kiểm quyền server vẫn thuộc S-SECA.

Không lưu token trên trình duyệt. Trang của module dùng CSS/JS này, có
`sidebar-mount`, `current-user` và mount picker riêng. Chưa tạo trang login
hoặc route đăng xuất vì đó là phần M-ACC/C0 chưa được giao triển khai.

## Kiểm đã chạy

```text
node tests/ui_shell/check_shell.cjs
UI-SHELL: đạt cookie, text an toàn, picker và hủy request khi 401
node --check server/static/shell/admin-guard.js
exit code 0
```

UI.1: bỏ token; CSS và font giữ cục bộ. UI.2: kiểm 401 có request đồng thời,
response trễ và không retry. Review độc lập phát hiện race whoami/401;
đã thấy test mới đỏ trước sửa, xanh sau guard ngay sau await trong initPage.
UI.3: JS là file ngoài, không inline script;
header CSP và console trình duyệt thật còn chờ S-SECA/R1. UI.4: textContent,
không innerHTML; chuỗi script/img được giữ nguyên như chữ trong phép kiểm.

Chưa kiểm tay trên điện thoại/trình duyệt hoặc có backend tài khoản thật.
