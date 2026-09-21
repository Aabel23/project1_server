# FlexMix Hub Server Operations Guide

**Kiểm tra:** 2026-09-18. **Phạm vi:** repository `/home/claw001/Server_Flex_mix` và host được kiểm tra tại thời điểm ghi. Đây là hướng dẫn vận hành prototype, không phải runbook production.

Không ghi password, Argon2 hash, enrollment token, database password, Cloudflare token hay private key vào tài liệu, shell history, URL hoặc log.

## 1. Purpose

Hướng dẫn này giúp người mới nhận server khởi động, dừng, kiểm tra Hub, đăng nhập Admin, kiểm tra MySQL/Nginx/Quick Tunnel, làm việc với fleet và xử lý lỗi thông thường. Mục **CHƯA CẤU HÌNH** không được coi là tính năng đang vận hành.

## 2. Current Architecture

```text
Browser local/LAN -- Nginx :80 -----------+
                                           v
Cloudflare Quick Tunnel ------------> Hub 127.0.0.1:8010 --> MySQL 127.0.0.1:13306
Machine -- authenticated outbound /v1/... -^
```

| Thành phần | Trạng thái thực tế |
| --- | --- |
| Hub | Uvicorn chạy thủ công, bind `127.0.0.1:8010` |
| MySQL | Compose service `mysql`; `127.0.0.1:13306` tới container port `3306` |
| Nginx | `nginx.service` active; `/etc/nginx/sites-available/flexmix` enabled qua `/etc/nginx/sites-enabled/flexmix`; listen `:80`, proxy `127.0.0.1:8010` |
| Cloudflare | `/usr/local/bin/cloudflared`, Quick Tunnel chạy thủ công tới Hub tại thời điểm kiểm tra |
| Named tunnel/domain/HTTPS Nginx | **CHƯA CẤU HÌNH / CHƯA XÁC MINH** |
| Hub systemd service | **CHƯA CẤU HÌNH**; chỉ có file mẫu |

Machine tự gọi Hub. Hub không nằm trên đường bán/pha local; không mở backend Machine qua Wi-Fi/LAN cửa hàng.

## 3. Server Directory Structure

| Path | Nội dung |
| --- | --- |
| `/home/claw001/Server_Flex_mix` | project root |
| `.venv/` | Python environment hiện có |
| `.env` | local config, bị gitignore |
| `src/flexmix_hub/` | FastAPI Hub, dashboard, API |
| `src/flexmix_machine/` | Machine runtime/adapters prototype, không phải service được cài |
| `migrations/hub/` | Alembic migrations |
| `tests/` | unit và integration tests |
| `compose.yaml` | MySQL development container |
| `config/examples/` | ví dụ `.env`, fleet env, Tailscale ACL |
| `deploy/nginx/flexmix-hub.conf.example` | mẫu HTTPS, chưa cài |
| `deploy/systemd/flexmix-hub.service.example` | mẫu systemd Hub, chưa cài |
| `deploy/backups/nginx-20260918-094635/` | backup Nginx config đã lưu |
| `/tmp/flexmix-hub-backups` | default Hub machine-package storage |
| `/tmp/flexmix-hub-releases` | default prototype release artifact storage |

## 4. Environment & Secrets

`.env` được đọc tại project root. Không dùng `cat .env`, `env`, hoặc `docker inspect` để đưa secret ra terminal.

| Setting/file | Mục đích |
| --- | --- |
| `FLEXMIX_DB_HOST`, `FLEXMIX_DB_PORT`, `FLEXMIX_DB_NAME`, `FLEXMIX_DB_USER` | MySQL; default host `127.0.0.1`, port `13306` |
| `FLEXMIX_DB_PASSWORD_FILE` | đường dẫn tuyệt đối đến app DB password file |
| `MYSQL_ROOT_PASSWORD_FILE` | root password file khi MySQL container khởi tạo |
| `FLEXMIX_PROTOTYPE_ENROLLMENT_TOKEN_FILE` | fleet/catalogue/command/overview prototype API token file |
| `ADMIN_USERNAME` / `FLEXMIX_ADMIN_USERNAME` | Dashboard username |
| `ADMIN_PASSWORD_HASH` / `FLEXMIX_ADMIN_PASSWORD_HASH` | Argon2 Dashboard password hash |
| `FLEXMIX_BACKUP_ROOT` | optional; default `/tmp/flexmix-hub-backups` |
| `FLEXMIX_RELEASE_ROOT` | optional; default `/tmp/flexmix-hub-releases` |

Secret files cần ở ngoài repository, permission `0600`; thư mục cha `0700`. Enrollment token không phải Dashboard password.

Tạo Argon2 hash mà không in password:

```bash
cd /home/claw001/Server_Flex_mix
.venv/bin/python -c 'from getpass import getpass; from argon2 import PasswordHasher; print(PasswordHasher().hash(getpass("New admin password: ")))' 
```

Ghi output vào `ADMIN_PASSWORD_HASH` trong `.env`, rồi restart Hub. Không dán password vào command line.

## 5. Start the Server

```bash
cd /home/claw001/Server_Flex_mix
docker compose up -d --wait
.venv/bin/alembic upgrade head
.venv/bin/uvicorn flexmix_hub.main:create_app --factory --host 127.0.0.1 --port 8010
```

Uvicorn chạy foreground. Giữ terminal mở. Nginx là system service hiện có:

```bash
systemctl is-active nginx
```

Chỉ mở Quick Tunnel sau khi Hub health pass:

```bash
cloudflared tunnel --url http://127.0.0.1:8010
```

URL `trycloudflare.com` được in bởi lệnh này, là URL tạm thời; không đoán hoặc lưu cứng URL.

## 6. Stop / Restart

### Hub

Dùng `Ctrl+C` tại terminal chạy Hub. Nếu cần dừng process bị mất terminal, xác minh PID trước:

```bash
pgrep -af 'uvicorn flexmix_hub.main:create_app'
kill <PID_DA_XAC_MINH>
```

Khởi động lại bằng lệnh ở mục 5. `flexmix-hub.service` chưa được cài.

### MySQL

```bash
cd /home/claw001/Server_Flex_mix
docker compose ps
docker compose restart mysql
```

`docker compose down` dừng MySQL development. Không chạy `docker compose down -v`: lệnh này xóa volume dữ liệu.

### Nginx và Cloudflare

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl restart nginx
pgrep -af 'cloudflared tunnel --url'
```

Dừng Quick Tunnel bằng `Ctrl+C`, hoặc `kill <PID_DA_XAC_MINH>`. `cloudflared.service` chưa được cấu hình.

## 7. Health Check

| Component | Command | Expected result |
| --- | --- | --- |
| Hub liveness | `curl -fsS http://127.0.0.1:8010/health` | `{"status":"ok"}` |
| Hub DB readiness | `curl -fsS http://127.0.0.1:8010/health/ready` | `{"status":"ok"}`; 503 nếu DB unavailable |
| MySQL | `docker compose ps` | `mysql` healthy |
| Alembic revision | `.venv/bin/alembic current` | revision hiện hành, repository head `0007_backups` |
| Alembic diff | `.venv/bin/alembic check` | `No new upgrade operations detected.` |
| Hub process | `pgrep -af 'uvicorn flexmix_hub.main:create_app'` | Uvicorn đúng project |
| Nginx | `systemctl is-active nginx` | `active` |
| Nginx proxy | `curl -fsS http://127.0.0.1/health` | `{"status":"ok"}` |
| Listening ports | `ss -ltnp | rg ':(80|443|8010|13306)\b'` | `8010`/`13306` loopback, Nginx `80`; không kỳ vọng `443` |
| Quick Tunnel | `pgrep -af 'cloudflared tunnel --url'` | process khi tunnel còn chạy |
| Tunnel URL | `curl -fsS https://<URL_TU_OUTPUT_CLOUDFLARED>/health` | health 200 khi URL phiên hiện tại còn sống |

`/health` chỉ kiểm tra tiến trình. `/health/ready` chỉ chạy `SELECT 1`, không thay thế migration hoặc nghiệp vụ checks.

## 8. Admin Login

URL local: `http://127.0.0.1:8010/login`. LAN qua Nginx: `http://<LAN_IP>/login`.

1. Dùng username từ `ADMIN_USERNAME` và password khớp Argon2 hash tại `ADMIN_PASSWORD_HASH`.
2. Login thành công tạo HttpOnly, SameSite=Lax cookie một giờ rồi redirect tới `/`.
3. Logout gọi `POST /logout` và xóa cookie.

Token URL không xác thực Dashboard. Đổi username/hash trong `.env` cần restart Hub. Với HTTP local/LAN hiện tại cookie không có `Secure`; HTTPS production chưa cấu hình.

## 9. Network Access

### Localhost

`http://127.0.0.1:8010/login`

### LAN

Nginx listen `0.0.0.0:80` và `[::]:80`; proxy tới Hub loopback. Wi-Fi IP được quan sát là `10.107.3.206`, nhưng DHCP có thể thay đổi.

`http://<LAN_IP>/login`

Đây là HTTP plaintext, chỉ dùng mạng tin cậy.

### Internet

Quick Tunnel HTTPS có thể dùng để test. Chạy lệnh mục 5, lấy URL từ output, thử `/health` và `/login` từ mạng khác. URL `trycloudflare.com` mất hiệu lực khi process dừng.

Named tunnel, fixed hostname/domain và HTTPS Nginx: **CHƯA CẤU HÌNH**. Cần setup thủ công trong Cloudflare Zero Trust/DNS, cài connector service, và giữ token ngoài repository.

## 10. Nginx Operations

| Item | Giá trị thực tế |
| --- | --- |
| Site config | `/etc/nginx/sites-available/flexmix` |
| Enabled link | `/etc/nginx/sites-enabled/flexmix` |
| Listener | port `80`, `[::]:80` |
| Upstream | `http://127.0.0.1:8010` |

```bash
sudo nginx -t
sudo systemctl reload nginx
systemctl status nginx --no-pager
sudo tail -n 50 /var/log/nginx/access.log
sudo tail -n 50 /var/log/nginx/error.log
```

Mẫu HTTPS `deploy/nginx/flexmix-hub.conf.example` có placeholder domain/certificate và chưa cài. Không copy mẫu lên host trước khi thay placeholder, có certificate và `nginx -t` pass.

Backup hiện có tại `deploy/backups/nginx-20260918-094635/`. Restore ghi đè config hiện hành:

```bash
cd /home/claw001/Server_Flex_mix
sudo cp deploy/backups/nginx-20260918-094635/flexmix /etc/nginx/sites-available/flexmix
sudo nginx -t
sudo systemctl reload nginx
```

Chỉ restore sau khi xác minh backup và lưu bản config hiện tại.

## 11. Cloudflare Tunnel Operations

`cloudflared` tại `/usr/local/bin/cloudflared`; version kiểm tra `2026.9.1`.

```bash
cloudflared tunnel --url http://127.0.0.1:8010
pgrep -af 'cloudflared tunnel --url'
cloudflared --version
```

Quick Tunnel đi trực tiếp tới Hub, không qua Nginx. Logs nằm ở terminal chạy process. Named tunnel, named tunnel status và service logs: **CHƯA CẤU HÌNH**. Không ghi tunnel token vào `.env` repository hoặc docs.

## 12. Database Operations

```bash
cd /home/claw001/Server_Flex_mix
docker compose up -d --wait
docker compose ps
.venv/bin/alembic current
.venv/bin/alembic check
.venv/bin/alembic upgrade head
```

Xác minh được image `mysql:8.4.11`, host `127.0.0.1`, port `13306`. Database name/user lấy từ `.env`; không in giá trị. App password đọc từ `FLEXMIX_DB_PASSWORD_FILE`.

Alembic có command `downgrade`, nhưng không có quy trình rollback production kiểm thử. Không downgrade dữ liệu vận hành.

## 13. Backup / Restore

Machine prototype `MachineBackupManager` có thể tạo tarball gồm `mysql.sql` (`mysqldump --single-transaction`), `pump_calib.json`, `calib_loadcell.json`, `machine_profile.json`, và `manifest.json`; khi caller gọi nó giữ tối đa 7 file tại local root được truyền vào.

Hub nhận upload ở `POST /v1/backups`, gắn với MID xác thực, lưu metadata MySQL và file tại `FLEXMIX_BACKUP_ROOT/<MID>/`. Default `/tmp/flexmix-hub-backups` không bền vững. Endpoint latest backup chỉ phục vụ Machine đã xác thực; Dashboard chỉ hiện metadata.

`restore_backup()` prototype chỉ validate và giải nén ra target directory; không import SQL, không restore Hub DB. Automated nightly backup, Hub DB backup, persistent retention và production restore: **CHƯA CẤU HÌNH**.

```bash
find /tmp/flexmix-hub-backups -maxdepth 2 -type f -name '*.tar.gz'
```

Không giải nén hoặc import `mysql.sql` vào DB đang chạy nếu chưa có maintenance window và backup đã xác minh.

## 14. Machine / Fleet Operations

| Workflow | Prototype hiện có |
| --- | --- |
| Enroll | `POST /v1/prototype/fleet/machines`; enrollment token header và device public key; Hub cấp MID 1–999999, không reuse |
| Auth | UUID + Ed25519 request signature; Hub suy MID từ registry |
| Desired state | `GET /v1/state?have=<version>` trả snapshot/304; local apply idempotent |
| Events | `POST /v1/events`; deduplicate `(machine_mid,event_id)`, ACK cursor |
| Commands | `POST /v1/prototype/commands`, Machine poll/ACK; type hiện có `refresh_state` |
| Heartbeat | `POST /v1/beat`; stale sau 120 giây ở overview |
| Backup | `POST /v1/backups`; retry backup ID không nhân metadata |
| Offline/reconnect | local prototype state/outbox giữ dữ liệu và retry |

Dashboard Provision / Enroll là trang trạng thái; browser enrollment flow chưa có. Không đưa private Machine key lên Hub.

## 15. Catalogue / Menu Operations

```text
Ingredients + Drinks + Recipe actions
  -> PUT /v1/prototype/catalogue (enrollment token)
  -> desired-state version tăng
  -> Machine GET /v1/state -> local idempotent apply
```

`PUT /v1/prototype/catalogue` validate duplicate IDs, recipe references, price và amount trước transaction. `GET /v1/prototype/catalogue` đọc catalogue/version. UI Ingredients, Drinks, Recipes và Current Menu là read-only. Publish Menu editor và Version History: **CHƯA CẤU HÌNH**.

## 16. Orders / Events

`order_ticket` là local source of truth trong Machine runtime prototype. Local flow: tạo ticket, atomic claim `unused` → `in_progress`, complete → `used`, ghi event outbox, retry upload; cursor chỉ tiến sau ACK `cursor_to` đúng. Hub chỉ giữ monitoring copy và deduplicate event. `note` không có trong telemetry. Hub unavailable không chặn local runtime prototype, nhưng đây không phải chứng nhận hardware/Machine production.

## 17. Releases / Updates

Hub `POST /v1/prototype/releases` lưu metadata/artifact tại `FLEXMIX_RELEASE_ROOT`; default `/tmp/flexmix-hub-releases`. Hub không nhận release private signing key, nhưng endpoint chưa verify signature trước khi lưu.

Machine `ReleaseManager` prototype verify Ed25519 signature, digest, target và version; staging/rename activation và một `previous` rollback. Rollout service, Machine update CLI và production release lifecycle: **CHƯA CẤU HÌNH**. Release signing key phải ở ngoài Hub.

## 18. Common Troubleshooting

| Symptom | Check | Command | Expected | Fix |
| --- | --- | --- | --- | --- |
| Hub không chạy | process/listener | `pgrep -af 'uvicorn flexmix_hub.main:create_app'` | Uvicorn process | start mục 5 |
| `/health` fail | Hub | `curl -i http://127.0.0.1:8010/health` | HTTP 200 | kiểm terminal/process/port |
| Port 8010 chiếm | listener | `ss -ltnp | rg ':8010\b'` | PID xác minh | dừng PID đúng hoặc không start Hub thứ hai |
| Login fail | config/restart | `curl -I http://127.0.0.1:8010/login` | 200 | kiểm tên biến/hash path mà không in secret; restart Hub |
| MySQL fail | container/readiness | `docker compose ps`; `curl -i http://127.0.0.1:8010/health/ready` | healthy/200 | `docker compose up -d --wait`; kiểm file paths `.env` |
| Migration fail | revision/schema | `.venv/bin/alembic current`; `.venv/bin/alembic check` | current/no diff | xác nhận DB đúng, backup rồi mới upgrade |
| Nginx proxy fail | config/upstream | `sudo nginx -t`; `curl -i http://127.0.0.1/health` | pass/200 | Hub phải nghe `127.0.0.1:8010`; reload Nginx |
| Machine không sync | identity/health | Hub `/health/ready`; Machine config | Hub reachable | kiểm registered UUID/public key/Hub URL; không log private key |
| Command không tới | command/poll | Dashboard Commands | pending/delivered/acknowledged | kiểm MID và Machine poll; chỉ `refresh_state` hiện có |
| Heartbeat không cập nhật | Machine beat | Dashboard Machine Health | recent heartbeat | kiểm outbound connection/identity |
| Backup fail | package/root | Dashboard Backup History | metadata mới | kiểm machine required files/mysqldump/root permission |
| Cloudflared fail | tunnel/local Hub | `pgrep -af 'cloudflared tunnel --url'` | process | chạy tunnel mới, dùng URL mới |
| Máy khác không vào | LAN/Nginx | `ip -4 -o addr show scope global`; `ss -ltnp | rg ':80\b'` | LAN IP/Nginx | dùng DHCP IP hiện tại, cùng mạng, kiểm firewall |
| Quick URL fail | URL phiên hiện tại | `curl -fsS https://<URL_TU_OUTPUT>/health` | health 200 | URL cũ/tunnel dừng; tạo tunnel mới |

## 19. Server Reboot Procedure

Không giả định Hub hoặc Quick Tunnel tự start: service của chúng chưa cài. Sau reboot:

```bash
cd /home/claw001/Server_Flex_mix
docker compose up -d --wait
.venv/bin/alembic upgrade head
.venv/bin/uvicorn flexmix_hub.main:create_app --factory --host 127.0.0.1 --port 8010
```

Terminal khác:

```bash
curl -fsS http://127.0.0.1:8010/health
curl -fsS http://127.0.0.1:8010/health/ready
systemctl is-active nginx
curl -fsS http://127.0.0.1/health
```

Nếu cần Internet prototype access:

```bash
cloudflared tunnel --url http://127.0.0.1:8010
```

Lấy URL mới từ output, kiểm tra `/health` và `/login` từ mạng khác. Regression check:

```bash
cd /home/claw001/Server_Flex_mix
FLEXMIX_TEST_MYSQL=1 .venv/bin/pytest -q
```

## Prototype vs Production

| Prototype hiện có | Production chưa có / cần thao tác thủ công |
| --- | --- |
| Uvicorn manual, Compose MySQL, Nginx HTTP LAN, Quick Tunnel temporary | Hub/cloudflared systemd, named tunnel/domain, TLS Nginx, persistent backup storage, Hub DB backup/restore |
| Argon2 Dashboard login, HttpOnly cookie, Machine Ed25519 proof | credential lifecycle/replay policy, RBAC/audit, full operator workflows |
| catalogue/event/command/heartbeat/backup/release adapters và tests | real Machine/hardware rollout, automation scheduler, release orchestration, recovery validation |

Không dùng prototype này như production server trước khi các mục production được cấu hình và kiểm thử.
