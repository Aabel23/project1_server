# Bằng chứng S-NET · review sửa lỗi đạt trên dev

Ngày 08/10/2026 (Bangkok). Nhánh `khoi/s-net`, worktree `server-wt-s-net`.
Cập nhật trong working tree chính: đã sửa P2 poll đến muộn khi shutdown và
P3 redirect percent-encode; hồi quy và bộ kiểm tích hợp 161 test đạt.
Chi tiết/kiểm lại tại [REVIEW_CODEX.md](REVIEW_CODEX.md).
User cho phép làm phần độc lập khi C0 chưa xong. Không sửa settings, contracts,
routing, wiring hoặc code nghiệp vụ. Không tự đánh dấu C0 hoàn tất.

## File và API tạm

- `server/core/net/tls.py`: SSLContext TLS 1.3, kiểm file khoá 0600 trên POSIX.
- `server/core/net/wake.py`: Wake và singleton `wake`, đánh thức các poll của đúng máy.
- `server/core/net/main.py`, `__init__.py`: NetSettings, NetServer và serve.
- `deploy/server/make_ca.py`: CA offline và leaf, kiểm tất cả đầu ra trước khi ghi.
- `deploy/server/chrony.conf`, `flexmix-server.service`: mẫu triển khai Linux.
- `tests/s_net/test_net.py`: cert tạm, test server thật và flood 25 giây.
- Tài liệu này.

```python
from server.core.net import NetSettings, serve, wake

settings = NetSettings(
    cert_file=leaf_crt, key_file=leaf_key, ca_file=ca_crt, hostname=hostname,
    host="0.0.0.0", admin_port=443, agent_port=8443, http_port=80,
    admin_threads=8, agent_threads=18, http_threads=4,
    timeout=60, shutdown_timeout=30,
)
serve(admin_app, agent_app, settings)
# Sau commit nghiệp vụ:
wake.notify(machine_id)
# Trong handler poll; notify không giữ hàng đợi, phải đọc lại DB sau wait:
woken = wake.wait(machine_id, timeout=25)
```

`NetServer(admin_app, agent_app, settings).start()` và `.stop()` dành cho test
hoặc host có vòng đời riêng. `serve` chạy trên main thread, chờ SIGINT/SIGTERM,
dừng listener/pool, huỷ poll hiện tại và poll đến trong lúc drain rồi khôi phục
handler signal cũ. Wake giữ trạng thái dừng tới khi NetServer.start gọi resume;
khởi động lại cùng server cho phép poll chờ/notify bình thường.
Wake không giữ machine_id khi hết người chờ. Nhiều người chờ cùng máy đều
được đánh thức. Notify trước wait không phải hàng đợi lệnh.

Hai cổng TLS có pool riêng; HTTP có pool thứ ba. Settings kiểm hostname,
cổng và số thread; port 0 chỉ dùng lấy cổng tạm trong test. Redirect không dùng
Host do client gửi. GET/HEAD tải CA tại `CA_CERT_PATH` hiện có (`/api/ca-cert`),
header `X-CA-SHA256` là fingerprint hex SHA-256 của cert DER. Cert CA được parse
và mã hoá PEM lại trước khi phục vụ, không xuất bytes thừa có thể chứa khoá.

Access log chỉ chứa listener cố định và HTTP status. Cheroot error log và
Flask uncaught exception log chỉ ghi sự kiện cố định, không traceback/message
do client điều khiển. Hook Flask được khôi phục khi stop. Các module nghiệp vụ
tự viết log phải tuân thủ cùng quy tắc, không log dữ liệu request hoặc bí mật.

## Kiểm đã chạy

Python 3.14.0, OpenSSL 3.0.18, Windows. Không thêm dependency.

```text
..\server\.venv\Scripts\python -m pytest tests/s_net tests/c0 -q -s
29 passed in 28.49s
```

Lần chạy đầy đủ dùng 18 ca S-NET và 11 ca C0 routing có trong worktree.
Sau đó thêm test lỗi Flask chứa Authorization và kiểm đầu ra leaf đã tồn tại.
Chạy lại bộ ngắn để kiểm các chỉnh sửa này:

```text
..\server\.venv\Scripts\python -m pytest tests/s_net tests/c0 -q -k "not longpoll"
29 passed, 1 deselected in 2.92s
```

Test isolation C0 mới chưa có trong worktree tại thời điểm chạy; phải chạy lại
ở checkout tích hợp khi Claude/C0 bàn giao. Không tính thiếu test là skip đạt.

Kiểm cuối chạy trên `NetServer` và `wake` thật, không import `spike/`:

```text
N = 10 (giả định vì Q9 chưa chốt), wait = 25 s
admin: 8 thread; agent: 18 thread; 32 luồng flood
poll timeout 0..4: 25.062, 25.062, 25.049, 25.046, 25.061 s
poll wake trực tiếp 5..8: 10.066, 10.066, 10.065, 10.066 s
poll wake qua HTTP admin 9: 10.229 s
admin flood hoàn tất: 4.080 request; lỗi: 0
poll đạt: 10/10; poll bị cắt: 0; mọi poll HTTP 200 và TLSv1.3
```

## Trạng thái từng bước

| Bước | Trạng thái | Bằng chứng / giới hạn |
|---|---|---|
| S-NET.1 | Đạt trên dev | SAN IP/DNS, hạn leaf đúng tham số, verify chữ ký CA; từ chối đầu ra trong repo/worktree và mọi file đã tồn tại; không ghi đè khoá |
| S-NET.2 | Đạt trên dev; Linux thật chưa kiểm | Min/max TLS 1.3; client ép TLS 1.2 bị từ chối; test nhánh POSIX từ chối 0644; Windows bỏ kiểm POSIX và cần ACL do operator quản lý |
| S-NET.3 | Đạt trên dev | Route sang cổng kia trả 404; pool độc lập; stop đóng socket/pool, trả poll đang chờ; SIGINT/SIGTERM mô phỏng bằng Python signal trên Windows và khôi phục handler |
| S-NET.4 | Đạt | Notify đánh thức mọi poll đúng máy, máy khác hết timeout; state được dọn |
| S-NET.5 | Đạt | GET nhận 301 với hostname cấu hình; CA/fingerprint đúng; HEAD không body; phương thức ngoài GET/HEAD bị 405 |
| S-NET.6 | Đạt với server và stub | Request/error log không có body/cookie/Authorization/query/keys/exception secret |
| S-NET.7 | Có mẫu; chưa kiểm triển khai | Chrony không nguồn ngoài, local stratum 10, LAN để operator thay; systemd user riêng, restart, SIGTERM. Chưa có wiring entrypoint nên ExecStart là placeholder, chưa cài/chạy unit |

Chưa kiểm Linux/Pi/LAN thật, quyền ACL Windows, reboot/systemd, nguồn giờ thật.
N=10 chưa thay thế benchmark với số máy chính thức Q9.

## Cần đổi hợp đồng / phối hợp C0

Đối chiếu `serve(admin_app, agent_app, settings)` với hợp đồng C0 khi sẵn sàng;
cấu hình hiện truyền trực tiếp, không tự tạo `server/config/settings.py`.
Claude/R1 phải nối hai app qua wiring và chọn module chạy thật cho systemd.
Q4 hạn leaf và Q9 SAN/số máy vẫn do operator cung cấp. Lệnh sinh cert yêu cầu
`--root-dir`, `--leaf-dir`, `--san` (có thể lặp), `--leaf-days`; mọi output nằm
ngoài tất cả repo/worktree. Giữ root.key offline, chỉ chép leaf/key/CA đến server.

```text
python deploy/server/make_ca.py --root-dir E:\offline-ca --leaf-dir E:\leaf \
  --san flexmix.lan --san 192.168.1.20 --leaf-days <SO_NGAY_DA_CHOT>
```

Không commit khoá/cert. Không merge main; operator review rồi tích hợp.
