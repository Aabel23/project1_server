# P0 · Spike mật mã và khởi tạo

- **Trạng thái:** CHƯA THỰC HIỆN.
- **Cổng chặn:** P0 không đạt thì dừng lại hỏi user. Không tự ghép primitive khác, không tự đổi thư viện. Theo mục 12 của thiết kế và `crypto_tranh_luan.md:339-346`.

## Mục tiêu

Trả lời bằng số đo và test, trước khi viết dòng code nghiệp vụ nào: bộ primitive FM1 đã chọn có chạy đúng và đủ nhanh trên Pi thật không?

Bộ đó gồm:

- HPKE Base X25519 / HKDF-SHA256 / AES-128-GCM của `cryptography`;
- Ed25519;
- AES-128-GCM cho response;
- long-poll qua TLS của cheroot.

## Điều kiện vào

- Q8: user cho phép `git init` thư mục `server/`.
- Có một Pi 5 thật đã cài version1.0. Dùng để đo, không sửa gì trên máy bán hàng.
- Máy dev cài được PyHPKE. Hiện chưa có (`crypto_A_diem_trien_khai.md:226`).

## Đầu ra

| Đầu ra | Ở đâu |
|---|---|
| Repo `server/` có commit đầu | `server/.git` |
| Thư mục spike, không trộn với code chạy thật | `server/spike/` |
| Báo cáo kết quả có lệnh, môi trường, output, đạt hoặc chưa | `server/internal/plan/bang_chung/P0.md` |
| Phiên bản `cryptography` ghim kèm hash, cho cả server và Pi | `server/requirements.lock`, bản ghi cho Pi ở báo cáo P0 |

## Phase con

### P0.1 Khởi tạo repo và gom routing

**Việc:**

| ID | Việc | File | Kiểm |
|---|---|---|---|
| P0.1.1 | `git init`. Thêm `.gitignore` cho `__pycache__/`, khoá, `*.key`, `*.pem`, `/var` cục bộ | `server/.gitignore` | `git status` sạch sau commit |
| P0.1.2 | Xoá bản trùng `server/routing.py`, chỉ giữ `server/server/config/routing.py` (mục 7 của thiết kế) | `server/routing.py` | `grep -r "routing" server/` chỉ còn một bản |
| P0.1.3 | Ghi `README.md` ngắn: thư mục nào làm gì, trỏ về thiết kế và plan | `server/README.md` | Reviewer đọc được |

- **Rollback:** xoá `.git`. Bản `routing.py` cũ vẫn còn trong commit đầu.
- **Lưu ý:** chưa đổi nội dung routing. Đổi sang bản 2 ở P1.1.

### P0.2 HPKE liên thông byte-exact

`cryptography` không có AAD và không có Export, nên không chạy nguyên văn vector RFC 9180 trên nó được (`crypto_tranh_luan.md:135-137`). Vì vậy cổng gồm 4 phần:

| ID | Việc | Kiểm, đạt khi |
|---|---|---|
| P0.2.1 | Chạy vector RFC 9180 đầy đủ trên PyHPKE, suite X25519 / HKDF-SHA256 / AES-128-GCM, mode Base | Mọi vector của suite này khớp |
| P0.2.2 | Seal bằng `cryptography`, open bằng PyHPKE, và ngược lại. `info = Tuple("fm1-req", SHA256(M))`, aad rỗng | 1.000 lần ngẫu nhiên mỗi chiều, plaintext khớp từng byte |
| P0.2.3 | Test âm: đổi 1 bit trong M (qua info), trong `enc`, trong `ct`; cắt cụt `ct`; đổi nhãn `fm1-req` | Mọi ca đều mở thất bại, không ném lỗi lạ |
| P0.2.4 | Ghi lại upstream `cryptography` có chạy vector HPKE trong CI không, kèm link commit hoặc file test | Có link nguồn |

- **File:** `server/spike/hpke_interop.py`, `server/spike/test_hpke_interop.py`.
- **Chạy:** `pytest server/spike -q` trên máy dev, rồi chạy lại trên Pi.
- **Không đạt:** dừng P0, báo user kèm output.
  - Phương án lùi đã được xét trong thiết kế: PyHPKE + Export + nonce ngẫu nhiên (`crypto_tranh_luan.md:440`).
  - Phương án lùi chỉ được dùng khi user chọn.

### P0.3 Ed25519, AES-GCM và LP/Tuple

| ID | Việc | Kiểm |
|---|---|---|
| P0.3.1 | Viết bản thử LP (4 byte độ dài + nội dung) và Tuple có nhãn, theo mục 4.2 | Hai Tuple khác nhãn không bao giờ ra cùng chuỗi byte (test thuộc tính) |
| P0.3.2 | Ký Ed25519 trên `Tuple("fm1-sig", M, enc, ct)`, verify ở phía kia | Đổi 1 byte bất kỳ trong M, enc hoặc ct là verify sai |
| P0.3.3 | Seal response AES-128-GCM bằng `resp_key`, nonce 12 byte ngẫu nhiên, AAD `Tuple("fm1-resp", SHA256(M))` | Mở bằng sai `resp_key` hoặc sai M là thất bại; 10.000 lần seal không lặp nonce |

- **File:** `server/spike/fm1_shape.py`.
- Code này là bản thử. P4.1 viết lại thành module thật, có thể chép logic sang nhưng không import từ `spike/`.

### P0.4 Benchmark trên Pi thật

- **Đo:** thời gian một vòng agent đầy đủ phía Pi: sinh cặp khoá, HPKE seal, ký, mở response. Đo cả phía server: verify, open, seal.
- **Cách đo:** 1.000 vòng, ghi p50, p95, max và CPU. Ghi model Pi, OS, phiên bản Python và `cryptography`.
- **File:** `server/spike/bench_fm1.py`.
- **Đạt khi:** có số đo thật. Plan không đặt ngưỡng. Số đo đưa user xem cùng tần suất trong thiết kế: poll tối đa 25 s, đơn mỗi 10 s (`crypto_A_diem_trien_khai.md:233`).
- **Phiên bản trên Pi:** nếu `cryptography` trên Pi không có `hazmat.primitives.hpke` (có từ bản 47.0.0), ghi lại phiên bản cần ghim. Việc ghim trên máy làm ở P3.4.

### P0.5 Long-poll qua TLS của cheroot

| ID | Việc | Kiểm |
|---|---|---|
| P0.5.1 | Một app Flask nhỏ chạy trên cheroot với `SSLContext` TLS 1.3. Hai server cheroot trong một tiến trình, hai cổng, mỗi cổng một pool | Cả hai cổng trả lời được |
| P0.5.2 | Route POST treo tối đa 25 s rồi trả lời; đánh thức sớm bằng `threading.Condition` dùng chung giữa hai pool | Client treo đủ 25 s không bị cắt; đánh thức trả lời ngay |
| P0.5.3 | Treo N kết nối ở cổng agent, đồng thời flood cổng quản trị | Cổng quản trị không làm các poll đang treo bị cắt (B11) |

- **File:** `server/spike/cheroot_longpoll.py`.
- **N:** bằng số máy dự kiến cộng 8. User cho số máy ở Q9. Chưa có thì đo với 10 và ghi rõ đó là giả định.

## Cổng ra P0

Tất cả các điều sau phải đạt:

- P0.2.1–P0.2.4 đạt.
- P0.3 đạt.
- P0.4 có số đo trên Pi thật.
- P0.5 đạt.
- Reviewer và cybersecurity đã đọc báo cáo `bang_chung/P0.md`.

Không đạt thì dừng và hỏi user. Cổng này không có ngoại lệ.

## Rủi ro

| Rủi ro | Khi xảy ra |
|---|---|
| PyHPKE không cài được trên Python 3.14 của máy dev | Chạy P0.2 trong venv Python cũ hơn, ghi rõ phiên bản |
| `cryptography` trên Pi quá cũ, không có module hpke | Ghi phiên bản cần ghim. Không tự nâng trên máy bán hàng ở P0 |
| cheroot cắt kết nối treo vì timeout mặc định | Ghi cấu hình timeout cần đặt; nếu không đặt được thì báo user (ảnh hưởng mục 10) |
