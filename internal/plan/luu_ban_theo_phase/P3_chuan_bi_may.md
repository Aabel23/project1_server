# P3 · Chuẩn bị máy

- **Trạng thái:** CHƯA THỰC HIỆN.
- **Luồng thiết kế:** M2 (phía máy), mục 9 bước 1 và bước 3–7, B7, B13.
- **Repo:** nhánh máy do user chọn ở Q6 (`version1.0` hoặc `version1.1`). Mọi số dòng dưới đây lấy theo `version1.0`; nếu Q6 chọn `version1.1` thì phải đối chiếu lại số dòng trước khi làm.

## Mục tiêu

Máy sẵn sàng để agent chạy. Máy vẫn bán hàng như cũ, và admin_gui vẫn còn trên máy cho tới P8.

Cụ thể:

1. Màn bán hàng không còn đọc order-mode qua route của admin_gui.
2. Có user `flexmix-agent`. Code agent nằm ở `/opt`, khoá ở `/var/lib/flexmix-agent`. User kiosk không đọc được thư mục khoá.
3. Có helper `flexmix-local` chạy bằng user kiosk. Helper chỉ nhận lệnh từ uid của agent, tập lệnh cố định. Đồng hồ thử màn hình 20 giây nằm trong helper.
4. Ledger và trạng thái agent có bảng trong MySQL máy. Agent có tài khoản MySQL riêng.

## Điều kiện vào

- P0 ✓: đã biết phiên bản `cryptography` cần ghim.
- Q6 đã chốt nhánh.
- Có một Pi thử, không phải máy đang bán.

P3 không phụ thuộc P1, nên chạy song song với P1 và P2.

## Đầu ra

| Đầu ra | File |
|---|---|
| Handler order-mode cục bộ | `store_gui/serve.py`, `store_gui/drinks-pos.js` |
| Khung agent: service, user, thư mục, venv | `deploy/agent/flexmix-agent.service`, `agent/main.py` (chưa nói chuyện với server) |
| Helper | `deploy/agent/flexmix-local.service`, `helper/flexmix_local.py` |
| Migration máy | `database/migrations/0003_agent.sql` |
| install.sh có phase cài agent | `deploy/install.sh` |
| Test | `tests/agent/`, `tests/helper/` |

Agent nằm trong repo máy, cài ra `/opt/flexmix-agent`. Hai file `fm1_encoding.py` và `fm1_crypto.py` dùng chung với server (mục 10). Cách đồng bộ hai bản quyết định ở P4.1.

## Phase con

### P3.1 Tách order-mode khỏi admin_gui (mục 9 bước 1, phần đọc)

| ID | Việc | File | Kiểm |
|---|---|---|---|
| P3.1.1 | Thêm route đọc order-mode cục bộ trong store_gui, đọc `configuration/order_mode.py`, không cần đăng nhập, chỉ trên loopback như hiện nay | `store_gui/serve.py` | `curl` trên Pi trả đúng `printQR` và `runDirect` |
| P3.1.2 | Đổi `ORDER_MODE_URL` sang route mới | `store_gui/drinks-pos.js:1549` | Đổi order-mode bằng admin_gui cũ, POS thấy giá trị mới |

**Phạm vi:**

- Chưa xoá `import admin_gui.serve` ở `store_gui/serve.py:96`.
- Chưa bỏ chuyển route ở `:435` và `:569-592`.

Hai việc này thuộc P8.5, sau khi server đã thay được admin_gui.

### P3.2 User, thư mục và service của agent (B7)

| ID | Việc | Kiểm |
|---|---|---|
| P3.2.1 | Tạo user hệ thống `flexmix-agent`, không có shell đăng nhập | `id flexmix-agent` |
| P3.2.2 | `/opt/flexmix-agent` thuộc root:root, quyền 755. Có venv riêng. `vendor/admin_functions` chép từ một commit đã ghim, không import gì từ `/home/flexxource` | `sudo -u flexxource touch /opt/flexmix-agent/x` thất bại |
| P3.2.3 | `/var/lib/flexmix-agent` thuộc flexmix-agent, quyền 0700 | `sudo -u flexxource ls /var/lib/flexmix-agent` thất bại |
| P3.2.4 | Unit `flexmix-agent.service`, `User=flexmix-agent`, tự khởi động lại. Ở P3 agent chỉ ghi log "chưa ghép" rồi chờ | `systemctl status` chạy; kill thì tự lên lại |
| P3.2.5 | Agent đọc `QRPROTO_MACHINE_ID` và dừng nếu thiếu, không mặc định về 1 (`phuong_an_kien_truc.md` §1) | Bỏ biến thì service báo lỗi rõ |

### P3.3 Helper flexmix-local

| ID | Việc | Kiểm |
|---|---|---|
| P3.3.1 | Service `User=flexxource`, file code thuộc root. Nghe trên unix socket | Socket tồn tại, quyền đúng |
| P3.3.2 | Kiểm `SO_PEERCRED`: chỉ nhận kết nối từ uid của `flexmix-agent` | Kết nối bằng uid khác thì bị đóng ngay |
| P3.3.3 | Tập lệnh cố định, parse chặt: `display apply\|keep\|revert\|status`, `order-mode set`, `menu publish`, `print <hex64>`. Mode phải nằm trong danh sách mode màn hình hỗ trợ | Fuzz đầu vào: mọi chuỗi ngoài ngữ pháp đều bị từ chối |
| P3.3.4 | Chuyển logic thử độ phân giải 20 giây từ `admin_gui/serve.py:3219-3337` vào helper. Nhớ mode cũ, tự quay về khi hết giờ, kể cả khi agent đã chết | Test trên Pi thật: apply, kill agent, sau 20 s màn hình về mode cũ |
| P3.3.5 | `menu publish` gọi `store_gui/sync_menu.py:893` `publish_menu()` | `menu-data.js` được dựng lại |
| P3.3.6 | Agent coi mọi output của helper là dữ liệu không tin cậy, parse chặt | Test: output lạ thì agent báo lỗi, không crash |

**Phạm vi:** admin_gui vẫn giữ cơ chế thử màn hình của nó tới P8. Ở P3 hai bản cùng tồn tại; chỉ helper được gọi từ agent.

### P3.4 Thư viện mật mã trên Pi

| ID | Việc | File | Kiểm |
|---|---|---|---|
| P3.4.1 | Ghim phiên bản `cryptography` theo kết quả P0, kèm hash, trong venv của agent | `deploy/agent/requirements.lock` | `pip install --require-hashes` thành công trên Pi |
| P3.4.2 | Không đụng phiên bản mà các tiến trình bán hàng đang dùng (`install.sh:223`) | | Tiến trình bán hàng vẫn import được như cũ |

### P3.5 DB máy cho agent

| ID | Việc | Kiểm |
|---|---|---|
| P3.5.1 | `0003_agent.sql`: `agent_ledger` (command_id, fingerprint, kind, state claimed/done/failed, result_json, acked, server_epoch) và `agent_state` (kid, server_epoch, applied epoch/version/sha256, con trỏ đơn và lỗi, hash tồn kho, install_uuid) | Chạy qua `database/migrate.py`; chạy lại lần hai không đổi gì |
| P3.5.2 | Tài khoản MySQL riêng cho agent. Cấp quyền theo cột để agent không đọc được `order_ticket.payload` | Đăng nhập bằng tài khoản agent, `SELECT payload` bị từ chối |
| P3.5.3 | `innodb_flush_log_at_trx_commit=1`, `sync_binlog=1` trên Pi | `SHOW VARIABLES` |

### P3.6 Giờ trên máy (M2)

| ID | Việc | Kiểm |
|---|---|---|
| P3.6.1 | Giữ `systemd-timesyncd` và bước chờ đồng bộ có sẵn (`install.sh:536-563`), chỉ đổi `NTP=` về địa chỉ server | `timedatectl timesync-status` thấy server |
| P3.6.2 | Agent chờ đồng bộ giờ xong mới gửi gói đầu tiên | Tắt chrony server: agent chờ, máy vẫn bán |

### P3.7 install.sh

| ID | Việc | Kiểm |
|---|---|---|
| P3.7.1 | Thêm phase cài agent: tạo user, thư mục, venv, helper, unit | Chạy `install.sh` trên Pi sạch, cài xong cả agent lẫn helper |
| P3.7.2 | Hỏi URL `https://…` của server và `machine_id`; bắt buộc đặt `QRPROTO_MACHINE_ID`. Phần hỏi mã ghép thêm ở P4.6 | Bỏ trống thì dừng, không đoán |
| P3.7.3 | Chạy lại `install.sh` trên máy đã cài thì giữ nguyên khoá và dữ liệu agent | Chạy hai lần, `/var/lib/flexmix-agent` không đổi |

Bước `admin_gui.auth` (`install.sh:387-402`) giữ nguyên tới P8.5.

## Cổng ra P3

- Trên Pi thử:
  - đặt món, in QR, quét, pha đủ một vòng như trước;
  - POS đọc order-mode từ route mới.
- `sudo -u flexxource` không đọc được `/var/lib/flexmix-agent` và không ghi được `/opt/flexmix-agent`.
- Helper từ chối uid khác và chuỗi ngoài ngữ pháp.
- Thử màn hình tự quay về khi agent bị kill.
- `pytest tests/agent tests/helper -q` đạt.
- Reviewer và cybersecurity duyệt phần phân quyền.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Helper hoặc sudoers sai quyền làm agent leo lên user kiosk rộng hơn mong muốn | Không dùng sudoers. Chỉ dùng socket với `SO_PEERCRED`, tập lệnh cố định. Cybersecurity kiểm |
| Đổi `drinks-pos.js` làm POS lỗi trên máy đang bán | Chỉ làm trên Pi thử. P8 mới đưa lên máy thật |
| Q6 chọn `version1.1` mà số dòng khác | Đối chiếu lại trước P3.1, cập nhật số dòng trong file này |
