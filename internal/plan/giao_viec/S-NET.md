# Giao việc khối S-NET · cho GPT Sol (Codex)

Dán toàn bộ file này vào Codex, mở tại thư mục `D:\PROJECT\CODE\InternProj\server`.

---

Bạn là coder của dự án "server mẹ FlexMix". Bạn làm đúng **một khối: S-NET** (TLS, hai cổng, tín hiệu đánh thức, giờ). Làm gọn, đúng phạm vi, không thêm việc ngoài danh sách. Code, comment và tài liệu viết tiếng Việt có dấu, câu ngắn.

## 0. Điều kiện bắt đầu

Kiểm tra trước khi làm gì khác:

1. `git log --oneline` có commit của khối C0 (hợp đồng).
2. Các file sau tồn tại:
   - `internal/contracts/interfaces.md`
   - `server/config/settings.py`
   - `server/config/routing.py` có `CA_CERT_PATH`
   - `server/contracts/`
   - `tests/c0/test_isolation.py`
   - `internal/plan/bang_chung/G0.md` với G0.7 đạt

Thiếu bất kỳ thứ nào thì **dừng lại**, báo rõ thiếu gì và không viết code.

## 1. Bối cảnh cần đọc

| File | Đọc phần nào |
|---|---|
| `internal/plan/index.md` | Mục "Module cô lập, nối tại một điểm", "Quy ước", "Định nghĩa khối xong" |
| `internal/plan/khoi_server.md` | Mục "S-NET · TLS, hai cổng, giờ": đây là đặc tả của bạn |
| `internal/contracts/interfaces.md` | Phần S-NET: `serve(admin_app, agent_app)`, `wake.notify` / `wake.wait`, cổng 80 |
| `spike/longpoll_g0_7.py` và `internal/plan/bang_chung/G0.md` | Mẫu cheroot + TLS 1.3 + long-poll đã chạy được. Chép cách làm, **không import** từ `spike/` |
| `docs/server_architect.html` | Mục 6 (bảng cổng: 443, 8443, 80) và mục 10 (stack, lý do dùng cheroot). File lớn, chỉ tìm đúng đoạn |

## 2. Việc phải làm

Code đặt ở `server/core/net/`. Riêng file triển khai đặt ở `deploy/server/`.

| ID | Việc | Kiểm |
|---|---|---|
| S-NET.1 | `deploy/server/make_ca.py`: sinh root và leaf. Root ghi ra đường dẫn người vận hành chọn, không ghi vào repo. SAN và hạn leaf lấy từ tham số dòng lệnh hoặc cấu hình. Hạn leaf chưa chốt (Q4) nên bắt buộc truyền vào, không tự đặt mặc định | Test: cert sinh ra có đúng SAN và hạn; không file khoá nào nằm trong repo |
| S-NET.2 | `tls.py`: `SSLContext` chỉ TLS 1.3. Trên Linux, khoá có quyền khác 0600 thì dừng. Trên Windows bỏ qua kiểm quyền và ghi rõ trong code | Test: client ép TLS 1.2 thì bị từ chối |
| S-NET.3 | `serve(admin_app, agent_app)`: hai server cheroot, hai pool thread, cổng lấy từ settings. Tắt êm khi nhận SIGTERM hoặc Ctrl+C | Test với hai app Flask giả: route của app này gọi vào cổng kia thì 404 |
| S-NET.4 | `wake`: tín hiệu đánh thức theo `machine_id`, dùng chung giữa hai pool | Treo `wait(machine_id, timeout)`, gọi `notify(machine_id)`: trả về ngay; máy khác không bị đánh thức |
| S-NET.5 | Cổng 80: chỉ chuyển hướng sang HTTPS và cho tải `ca.crt` kèm vân tay SHA-256 (`CA_CERT_PATH`) | Test: request thường nhận 301; `CA_CERT_PATH` trả đúng file |
| S-NET.6 | Logger chung: không ghi body, cookie, header `Authorization`, khoá | Test: log của một request mẫu không chứa các thứ đó |
| S-NET.7 | `deploy/server/chrony.conf` (`local stratum 10`, `allow <dải LAN>` để dạng biến, không trỏ nguồn ngoài) và `deploy/server/flexmix-server.service` (user riêng, tự khởi động lại) | Reviewer đọc. Không kiểm trên máy dev |

**Kiểm cuối của khối:** treo N = 10 poll ở cổng agent, đồng thời flood cổng quản trị. Không poll nào bị cắt. Đây là G0.7 chạy lại trên code thật. Ghi rõ N = 10 là giả định, vì số máy (Q9) chưa chốt.

## 3. Test

- Đặt ở `tests/s_net/`.
- Cert tạm sinh trong thư mục tạm của pytest (`tmp_path`), không commit.
- `.venv` không theo vào worktree. Dùng Python trong `.venv` của thư mục repo gốc:
  ```
  ..\server\.venv\Scripts\python -m pytest tests/s_net tests/c0 -q
  ```
  Test `tests/c0/test_isolation.py` phải vẫn xanh.

## 4. Không được

- Chỉ sửa trong `server/core/net/`, `deploy/server/`, `tests/s_net/` và `internal/plan/bang_chung/S-NET.md`.
- **Không sửa** `server/wiring.py`, `server/contracts/`, `server/config/routing.py`, `server/config/settings.py`, `internal/contracts/`, `internal/plan/*.md`, `docs/`, `machine/`, `spike/`.
- Thấy hợp đồng thiếu hoặc sai thì **không tự sửa**. Ghi vào báo cáo, mục "Cần đổi hợp đồng".
- Không import module nghiệp vụ nào, không dùng lại CA cũ trong `.caddy-data`, không commit khoá hay cert.
- Chỉ `pip install` vào `.venv` khi thật cần (cheroot, flask).

## 5. Git

1. Tạo nhánh và worktree riêng để không đụng agent khác:
   ```
   git worktree add ..\server-wt-s-net -b khoi/s-net
   ```
   Làm việc trong `..\server-wt-s-net`.
2. Chỉ `git add` đúng các file của bạn. Không dùng `git add -A` hay `git add .`.
3. Commit message tiếng Việt, mở đầu bằng `S-NET:`.
4. Không merge vào `main`. Operator sẽ review rồi mới merge.

## 6. Báo cáo khi xong

Ghi `internal/plan/bang_chung/S-NET.md`, gồm:

- danh sách file;
- lệnh test và output rút gọn;
- số liệu của kiểm cuối (N, thời gian treo, số poll bị cắt);
- từng bước S-NET.1 đến S-NET.7: đạt, chưa đạt hay chưa kiểm được;
- mục "Cần đổi hợp đồng", nếu có.

Trả lời cuối ngắn gọn, đúng nội dung đó.
