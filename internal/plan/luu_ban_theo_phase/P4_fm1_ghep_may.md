# P4 · FM1, ghép máy, long-poll

- **Trạng thái:** CHƯA THỰC HIỆN.
- **Luồng thiết kế:** mục 4 (4.2 hình dạng gói, 4.4 pipeline server, 4.5 pipeline agent, 4.6 khoá), M1, M2 (phía server), M3 (khung), M4, M5. Lỗi kiểm định: B1, B5, B6, B8, B9, B11, B14, A1, A2, G2.

## Mục tiêu

- Máy ghép được vào server bằng mã ghép một lần.
- Mọi gói trên kênh máy đi qua FM1.
- Máy treo long-poll được và nhận `target_menu_version`.
- Thu hồi một máy thì máy đó dừng gửi, nhưng vẫn bán.

Ở phase này long-poll chưa mang lệnh. Lệnh có ở P6.

## Điều kiện vào

- P0 ✓, P1 ✓, P3 ✓.
- Q1: user chấp nhận các chỗ lệch R5. Chặn P4.1. Nếu user chọn bám R5 sát hơn thì phải sửa lại plan P4 trước khi làm.

## Đầu ra

| Đầu ra | File (server) | File (agent) |
|---|---|---|
| Mã hoá khung, LP, Tuple, M | `security/fm1_encoding.py` | `agent/fm1_encoding.py` (cùng nội dung) |
| Mật mã | `security/fm1_crypto.py` | `agent/fm1_crypto.py` |
| Pipeline | `security/agent_gate.py`, `security/claims.py` | `agent/transport.py`, `agent/main.py` |
| Khoá | `security/keys.py` | |
| Ghép máy | `security/enroll.py` | `agent/enroll.py` |
| Migration | `db/migrations/0003_credential.sql`: `machine_credential`, `enrollment_code`, `packet_claim`, `server_key` | |
| Vector dùng chung | `tests/vectors/fm1/*.json` | dùng cùng thư mục vector |
| Test tấn công | `tests/p4/attack/` | |

## Phase con

### P4.1 Mã hoá gói (thuần, không mật mã)

| ID | Việc | Kiểm |
|---|---|---|
| P4.1.1 | ⏸ Q1. Chốt định dạng M theo bảng "Trường trong M" ở mục 4.2: domain, version, suite, audience, server_kid, credential_kid, method, route_id, attempt_id, issued_at, server_epoch_seen. Query luôn rỗng | Reviewer so với mục 4.2 |
| P4.1.2 | LP, Tuple có nhãn. Nhãn: `fm1-req`, `fm1-sig`, `fm1-resp`, `fm1-cmd`, `fm1-bundle`, `fm1-proof` | Test thuộc tính: khác nhãn thì không ra cùng chuỗi byte |
| P4.1.3 | Bộ vector JSON tạo một lần, dùng cho cả hai phía. Nếu hai bản `fm1_encoding.py` lệch nhau thì test vector báo đỏ | `pytest` chạy vector ở cả repo server và repo máy |
| P4.1.4 | Cách giữ hai bản giống nhau: file trong repo máy là bản chép, đầu file ghi commit nguồn. Test so sha256 của hai file | Test đỏ khi một bên sửa mà bên kia chưa chép |

### P4.2 Mật mã hai phía

Theo mục 4.2: request là `ver ‖ LP(M) ‖ LP(enc) ‖ LP(ct) ‖ LP(sig)`; response là `ver ‖ LP(nonce) ‖ LP(ct)`.

| ID | Việc | Kiểm |
|---|---|---|
| P4.2.1 | Agent: sinh `attempt_id` và `resp_key` 16 byte; HPKE seal `LP(resp_key) ‖ LP(body)` tới khoá KEM server đã ghim, info = `Tuple("fm1-req", SHA256(M))`; ký Ed25519 trên `Tuple("fm1-sig", M, enc, ct)` | Vector |
| P4.2.2 | Server: verify chữ ký; HPKE open; tách `resp_key` khỏi body; không log `resp_key` | Vector; test log không có `resp_key` |
| P4.2.3 | Server seal response: AES-128-GCM bằng `resp_key`, nonce ngẫu nhiên, AAD = `Tuple("fm1-resp", SHA256(M))`. Bên trong: `{attempt_id, status, server_epoch, body}` | Vector; 10.000 lần seal không lặp nonce (A1) |
| P4.2.4 | Agent mở response bằng `resp_key` của chính attempt đang chờ; kiểm `attempt_id` và hạn đo bằng BOOTTIME; xoá `resp_key` sau khi mở | Test: response của attempt khác thì không mở được |

### P4.3 Khoá server và credential

| ID | Việc | Kiểm |
|---|---|---|
| P4.3.1 | Khoá riêng KEM X25519 của server nằm trong file, quyền 0600, không có trong DB. `server_key` chỉ giữ kid, khoá công khai và trạng thái hiện tại/kế tiếp | Sai quyền file thì server không khởi động |
| P4.3.2 | `manage.py make-server-key` và hướng dẫn chép một bản offline ra USB (mục 4.6) | Chạy trên DB rỗng tạo được khoá |
| P4.3.3 | `machine_credential`: kid, machine_id, alg (`ed25519`), pubkey, status (active / retiring / revoked), generation, hw_issued_at, last_revoked_notice_at | Migration áp được |

### P4.4 Pipeline server (mục 4.4)

Thứ tự bắt buộc: kiểm rẻ chạy trước kiểm tốn CPU (A2).

| ID | Bước | Kiểm (test tấn công) |
|---|---|---|
| P4.4.1 | Kiểm rẻ: độ dài khung, `ver`, parse M, audience, kid còn active, `route_id` khớp đường dẫn và có trong `ROUTE_POLICY`, `issued_at` trong cửa sổ W, `issued_at` không thấp hơn high-water của kid trừ W, `attempt_id` chưa có trong `packet_claim` (đọc, chưa claim) | Gói của kid đã thu hồi bị từ chối mà không chạy verify (đếm số lần gọi verify = 0) |
| P4.4.2 | Verify chữ ký Ed25519 | Đổi 1 byte trong M, enc hoặc ct thì bị từ chối |
| P4.4.3 | HPKE open, tách `resp_key` | Đổi info (M) thì open thất bại |
| P4.4.4 | Một transaction: claim `attempt_id` (PK `(kid, attempt_id)`), kiểm lại credential, so `server_epoch`, cập nhật high-water | Phát lại cùng gói thì bị từ chối; hai gói cùng `attempt_id` gửi đồng thời thì chỉ một gói qua |
| P4.4.5 | Gọi module với `machine_id` lấy từ credential, không lấy từ body (B9) | Body ghi `machine_id` khác thì vẫn dùng id của credential |
| P4.4.6 | Seal response (P4.2.3) | |
| P4.4.7 | Lỗi trước bước P4.4.4: HTTP 4xx thân cố định `{"e": gợi ý}`, không mã hoá. Route không có trong `ROUTE_POLICY` thì từ chối | Đổi route của gói sang route khác thì bị từ chối (B6) |
| P4.4.8 | Dọn `packet_claim` theo high-water của từng máy, không theo giờ hệ thống | Test: đổi giờ hệ thống không làm dọn sớm |

### P4.5 Pipeline agent (mục 4.5)

| ID | Việc | Kiểm |
|---|---|---|
| P4.5.1 | `transport.py`: HTTPS chỉ tin CA nội bộ đã ghim; không bao giờ dùng URL `http://` | Cert lạ thì từ chối |
| P4.5.2 | Lỗi mạng, 4xx thân cố định hoặc response không mở được: lùi 1, 2, 5, 10, 30 s rồi gửi attempt mới. Không bao giờ dừng hẳn (B5) | Gửi 401 giả thì agent chỉ lùi lại |
| P4.5.3 | Chỉ thông báo `revoked` đã xác thực mới làm agent dừng gửi | Test: response seal hợp lệ mang `revoked` thì agent dừng và ghi trạng thái |

### P4.6 M1 · Ghép máy

| ID | Việc | Route | Kiểm |
|---|---|---|---|
| P4.6.1 | Tạo mã ghép: tối thiểu 80 bit, base32. Server chỉ lưu verifier và khoá MAC dẫn từ mã. Hạn 10 phút, 5 lần thử sai (mặc định). Cần xác thực lại | `MACHINE_ENROLL_CODE_PATH` | Mã sai 5 lần thì khoá; hết hạn thì từ chối |
| P4.6.2 | Trust bundle: CA, khoá KEM server, audience, epoch, kèm HMAC `fm1-bundle` dẫn từ mã ghép | `AGENT_TRUST_PATH` | Đổi 1 byte trong bundle thì `install.sh` dừng |
| P4.6.3 | Agent sinh khoá Ed25519 trong `/var/lib/flexmix-agent`, quyền 0600; ghim CA và khoá KEM vào `trust.json` | | Quyền file đúng |
| P4.6.4 | Enroll bằng FM1 với `credential_kid = enroll`, ký bằng khoá mới. Bên trong có `proof = HMAC(khoá dẫn từ mã, Tuple(pubkey, machine_id, install_uuid))` | `AGENT_ENROLL_PATH` | Proof sai thì từ chối |
| P4.6.5 | Tiêu mã trong cùng transaction với việc tạo credential | | Hai enroll đồng thời cùng mã: chỉ một thành công |
| P4.6.6 | Màn cài đặt và trang Máy cùng hiện vân tay khoá máy | | Kỹ thuật viên so được |
| P4.6.7 | `install.sh` hỏi mã ghép rồi chạy enroll | | Chạy trên Pi thử: máy hiện "đã ghép" trên trang Máy |

### P4.7 M5 · Thu hồi

| ID | Việc | Kiểm |
|---|---|---|
| P4.7.1 | `MACHINE_REVOKE_PATH`, cần xác thực lại: credential thành revoked, ghi thêm vào `revoked.list` (file ngoài DB) | File có dòng mới |
| P4.7.2 | Gói của kid đã thu hồi: trả response seal status `revoked`, tối đa 1 lần mỗi phút cho mỗi kid (`last_revoked_notice_at`). Ngoài khoảng đó thì 4xx thân cố định | Gửi 100 gói: chỉ một gói được seal trong một phút |
| P4.7.3 | Ghép lại theo M1 với `install_uuid` mới; lịch sử đơn của máy giữ nguyên | Test trên Pi thử |

Phần huỷ lệnh khi thu hồi (queued → expired, offered → unknown) làm ở P6.1, vì bảng lệnh có ở đó.

### P4.8 M3 · Long-poll và hello (chưa có lệnh)

| ID | Việc | Route | Kiểm |
|---|---|---|---|
| P4.8.1 | Hello: agent gửi phiên bản và bản menu đã áp. Server trả `target_menu_version`, `server_epoch`, `server_time` (chỉ để chẩn đoán) | `AGENT_HELLO_PATH` | Có trong log chẩn đoán |
| P4.8.2 | Long-poll POST, `wait` tối đa 25 s, nằm trong body đã mã hoá. Trả `target_menu_version` khi bản đích đổi | `AGENT_COMMANDS_PATH` | Đổi giá trên server (P2) thì poll đang treo trả lời ngay |
| P4.8.3 | Mỗi máy một poll: poll mới thay poll cũ. Hai poll cùng khoá từ hai IP khác nhau thì bật cờ "nghi nhân bản" (`clone_flag_at`) | | Test giả hai IP |
| P4.8.4 | `last_seen`; máy online khi `last_seen` không quá ba chu kỳ chờ | | Trang Máy hiện online/offline đúng |

### P4.9 M2 · Giờ phía server

| ID | Việc | Kiểm |
|---|---|---|
| P4.9.1 | Từ chối gói có `\|issued_at − giờ server\| > W` hoặc `issued_at` thấp hơn high-water của máy trừ W | Test với giờ máy lệch |
| P4.9.2 | So giờ tường với đồng hồ đơn điệu; giờ server nhảy thì hiện banner cảnh báo | Đổi giờ server: banner hiện |
| P4.9.3 | Nút "Xác nhận giờ đúng" của owner: xác thực lại, đặt lại high-water | `CLOCK_CONFIRM_PATH` |

## Cổng ra P4

- `pytest tests/p4 -q` đạt ở server. Test vector đạt ở cả hai repo.
- Hacker chạy bộ tấn công, mọi ca đều bị chặn: phát lại, đổi route, đổi byte, kid cũ, mã ghép hết hạn, bundle sai HMAC, hai IP cùng khoá, 401 giả.
- Trên Pi thử:
  - ghép được;
  - long-poll treo và trả lời khi đổi menu;
  - thu hồi thì máy dừng gửi, vẫn bán;
  - ghép lại được.
- Reviewer và cybersecurity duyệt.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Hai bản `fm1_encoding.py` lệch nhau | Test sha256 ở P4.1.4 và vector chung |
| Thread của cổng agent cạn khi nhiều máy treo poll | Số thread lớn hơn số máy cộng biên; đo ở P8.3 |
| Clone thẻ SD | Chỉ phát hiện được (P4.8.3). Thiết kế đã ghi giới hạn này |
