# Agent A (Opus): đưa middleware R5 vào server mẹ

Ngày 2026-10-08. Agent chỉ đọc, không sửa file. Đây là báo cáo gốc, phiên chính chỉ định dạng lại.

**Ký hiệu:**
- **[HT]**: hiện trạng.
- **[ĐX]**: đề xuất.
- **[GĐ]**: giả định.
- **[CĐC]**: chưa đối chiếu.

**Viết tắt nguồn:**
- **D** = `androidv0.1/agent_workspace/tasks/middleware/internal/packet-security/design.md`
- **TK** = `server/docs/thiet_ke_server_me.html` (số dòng là của bản trước đợt sửa đêm 08/10)

## 1. Tóm tắt R5

### Đã có trong code androidv0.1 [HT]

- PBKDF2-SHA256 200k vòng (`server/lib/security/user_password.py:8-15`)
- SHA-256 của token (`user_session.py:23-32`)
- HMAC vân tay request, khoá nằm trong RAM (`data_hash.py:9,17-20`)
- `compare_digest`

Server đó chạy HTTP `0.0.0.0:8000` (`server/config/config.py:3-4`), không có TLS, HPKE hay chữ ký. Phần còn lại của R5 chỉ là đề xuất: chưa có vector, chưa có prototype (D:553-554).

### Đề xuất R5, user đã chốt ngày 07/10 (D:9-27)

- **Lớp ngoài:** HTTPS bắt buộc. Lớp E chạy bên trong TLS, mã hoá hai chiều và chứng minh nguồn gửi. Server được giải mã, tức là hai chặng riêng, không phải E2EE (D:34-37).
- **Mã hoá:** HPKE Base single-shot, mỗi attempt một lần. Suite C1-A: X25519 / HKDF-SHA256 / AES-128-GCM (D:79-84).
- **Chữ ký:** một chữ ký ngoài trên `Tuple(label, M, enc, ct)`, kiểm trước khi giải mã.
  - C2-B: ECDSA P-256, r‖s 64 byte, low-s.
  - Khoá ký tách khỏi khoá KEM.
  - Không dùng HPKE Auth vì có KCI (D:59-69, 81-85).
- **Response:** khoá lấy bằng Export từ context của request. Mỗi CID chỉ Seal một lần, chốt bằng CAS `SEAL_STARTED` ghi bền. Nhánh thua chỉ nhận lỗi vận chuyển, không có bản mã (D:246-274).
- **Định dạng gói:** LP/Tuple có nhãn domain. Envelope = `ver‖LP(M)‖LP(enc)‖LP(ct)‖LP(sig)`. M có 15 trường. Route được bảo vệ không dùng GET hay query (D:172-232).
- **Chống phát lại:** claim bền `UNIQUE(audience, credential_kid, attempt_id)`, đặt sau verify + Open và trước mọi tác động (D:321-340).
- **Thao tác vật lý:**
  - Ticket do server cấp `operation_id`, có MAC theo `recovery_epoch`.
  - Ledger server và ledger máy đi qua các trạng thái claimed → dispatched → done/unknown.
  - Không hứa exactly-once vật lý (D:379-454).
- **Lệnh trong poll:** bind với `poll_attempt_id` và `intent_deadline`. Máy kiểm hạn bằng CLOCK_BOOTTIME (D:342-372).
- **Khoá:**
  - Manifest khoá server do root P-256 ký, máy giữ root ở chế độ air-gapped.
  - Máy tự sinh khoá lúc lắp đặt (D3-B), lưu file quyền 0600, không có TPM (D:100-160).
- **Đồng hồ:**
  - Sau boot ở trạng thái CLOCK_UNTRUSTED, lưu high-water `max_now_seen`.
  - Dùng chrony NTS. Không có route đồng bộ giờ trong giao thức (D:280-318).
- **Chống restore lùi:** witness HMAC trên `server_seq`, chuỗi hash ledger máy, audit challenge (D:570-626).
- **Ingress:** giới hạn cứng trước khi parse và verify. Không log plaintext (D:469-483).
- **Triển khai:** chuyển một đợt qua bảo trì, không chạy song song với bản plaintext (D:655-677).
- **Thư viện:** C3-A là PyHPKE. Vector không đạt thì dừng rollout (D:87-96).

### Lệch giữa các tài liệu

`server/docs/cryptography/crypto-primer.html` và `packet-security.html` còn ghi "suite chưa chốt" và dùng ví dụ Ed25519 + AES-256-GCM. Trong khi D §0 đã chốt AES-128-GCM + P-256.

## 2. Bản đồ áp dụng [ĐX]

### Chỗ đặt middleware trong sơ đồ râu

- **Bảo mật A:** session HMAC, role, `user_machine`, ticket thao tác → `/api/*` cho trình duyệt.
- **Bảo mật B:** chính là middleware envelope → `/api/agent/*`.
- **Đường truyền:**
  - Trên server: TLS do nginx hoặc cheroot đảm nhận, dùng CA nội bộ, đi qua LAN.
  - Phía trình duyệt: kết nối TLS thường.
  - Phía agent máy: TLS client có pin CA → Bảo mật B của agent → các module agent.

### Thứ tự xử lý của server cho `/api/agent/*`

1. TLS.
2. Giới hạn ingress: số kết nối, header/body, route + method nằm trong allowlist, semaphore cho phần mật mã.
3. Parse envelope và kiểm độ dài.
4. Tra `credential_kid` và `server_kid`. So route/method/audience trong M với route thật. Kiểm hạn (bước rẻ).
5. Verify chữ ký.
6. HPKE Open.
7. Parse JSON có giới hạn.
8. Claim bền. Trong cùng transaction kiểm lại hạn, credential còn active và `max_now_seen`.
9. Quyền: `machine_id` bên trong phải đúng máy của credential. Kiểm ticket và ledger.
10. Chạy module.
11. Dựng response có binding → CAS `SEAL_STARTED` → Export → Seal → gửi.

### Thứ tự cho trình duyệt

TLS → ingress → session → role → `user_machine` → ticket (chỉ với lệnh vật lý) → module.

### Lấy nguyên từ R5

- HPKE Base
- Chữ ký kiểm trước khi giải mã
- LP/Tuple với nhãn `flexmix-sm-*`
- Claim bền
- Export + Seal một lần
- Thông báo lỗi tối giản
- Các trường của lệnh
- Ledger máy ghi claimed trước khi gọi executor
- Cấm hạ xuống plaintext
- Giới hạn ingress
- Chuyển một đợt

### Phải đổi

| Bối cảnh | Đổi |
|---|---|
| Trình duyệt thay app | Không có Keystore, recovery code (D4-B) hay kênh giờ D2-C. Ticket với trình duyệt là chuỗi opaque, trình duyệt không làm phép mật mã nào |
| Không có APK | Trust bundle được cài lúc enroll. Manifest và root offline thành tuỳ chọn |
| Flask + waitress | Waitress không làm TLS được → đặt nginx ở localhost phía trước, hoặc dùng cheroot |
| SQLite FULL | MySQL InnoDB với `innodb_flush_log_at_trx_commit=1` trên cả server và Pi (độ bền trên thẻ SD: [CĐC]) |
| Long-poll GET | `AGENT_COMMANDS_PATH` và `AGENT_MENU_PATH` chuyển sang POST (D:226). Context HPKE giữ trong RAM tối đa 25 s, mỗi máy tối đa một context |
| Media lớn | Không bọc HPKE. Chỉ dùng TLS và kiểm sha256 có trong snapshot đã seal |
| Nhiều máy | Mỗi máy một credential. Audience là cả deployment |
| Witness, chuỗi hash | Để pha sau |

## 3. Theo nhóm luồng [ĐX]

| Luồng | Bảo vệ |
|---|---|
| M1 | Envelope bootstrap (kid sentinel) + mã enroll + chứng minh giữ khoá (PoP) |
| M2 | Ngoài giao thức (chrony) |
| M3 | Envelope đầy đủ. Response mang lệnh được seal bằng Export, bind `poll_attempt_id` |
| M4 | Thay bằng middleware |
| M5 | Agent tự xoay khoá, admin thu hồi |
| A1–A3, N1–N4, N6, K4, D3 | TLS + session (N2 đã có `row_version`) |
| N5 | Menu và ack: envelope. Media: TLS + sha256 |
| K3, D1, D2 | Envelope với `operation_id=0`. Upsert vốn idempotent, claim chặn phát lại. Đây là chỗ cần giấu giá, đơn hàng, tồn kho |
| K1, L3 | TLS + session. Lệnh đi qua M3, không cần ticket |
| K2, L2 | **Bắt buộc ticket + ledger:** `add_gram` không idempotent; in hai nhãn dùng được là lỗi. Ledger máy hiện thiết kế đã khớp R5; cần thêm fingerprint và trạng thái `unknown`, không tự chạy lại |
| L4 | `intent_deadline` 10 s + đồng hồ đơn điệu. Nên có ticket cho `apply` |
| L1 | Ticket tuỳ chọn, vì thao tác idempotent |

**Khi response bị mất sau Seal:** lệnh ở trạng thái `dispatched`. Server giao lại **cùng `command_id`** trong hạn, ledger máy chặn việc chạy lần hai. Câu "expires_at để giao lại" trong `phuong_an_kien_truc.md` cần viết lại theo đúng nghĩa này.

## 4. Trình duyệt quản trị

- **WebCrypto có gì:**
  - AES-GCM, HKDF, ECDH và ECDSA P-256: mọi trình duyệt hiện đại.
  - X25519: Chrome 133, Firefox 130.
  - Ed25519: Chrome 137, Firefox 129–130, Safari 17.
  - Các số phiên bản này lấy từ nguồn web, chưa thử trên thiết bị thật.
- **HPKE:** không có sẵn, phải vendor thư viện JS. LAN không có internet nên không tải từ CDN được.
- **Secure context:** `crypto.subtle` chỉ chạy trong secure context, nên đằng nào cũng phải có HTTPS.
- **Đánh đổi:** JS do chính server giao qua cùng kênh TLS. Ai MITM được TLS thì thay được cả JS lẫn khoá công khai. Vì vậy bảo đảm A1 của R5, vốn dựa vào root cài sẵn trong APK, **không chuyển sang trình duyệt được**.
- **Khuyến nghị:**
  - Dùng TLS + session như admin_gui (`auth.py:645-733`, token để trong `sessionStorage`, gửi qua header Bearer), thêm ticket cho lệnh vật lý.
  - Pha sau có thể gắn session với thiết bị: khoá ECDSA non-extractable lưu trong IndexedDB, phải sửa mọi fetch wrapper (`admin-guard.js:234`, `menu-store.js:124`…).

## 5. TLS trong LAN [ĐX]

- **CA nội bộ:** root sinh offline, hạn khoảng 10 năm [GĐ].
- **Cert server:** SAN là IP, hoặc tên `.lan` nếu có DNS.
- **Gia hạn:** không có ACME, làm theo runbook. Server cảnh báo trên UI khi cert sắp hết hạn.
- **Agent:** dùng `ssl.create_default_context(cafile=ca.pem)`, chỉ tin CA nội bộ. Pin SPKI của leaf là tuỳ chọn, nếu làm thì cần có khoá dự phòng.
- **Trình duyệt:** phải cài root CA lên từng PC và điện thoại, kể cả điện thoại nhân viên dùng để bấm "Giữ" ở L4.
- **HTTP:** chỉ dùng để redirect sang HTTPS.
- **mTLS:** là một phương án thay cho chữ ký tầng ứng dụng.
- **Quan hệ với HMAC:**
  - Ở kênh agent: thay hẳn HMAC + `secret_enc`. Nhờ đó bỏ được rủi ro "lộ DB + master key là lộ secret mọi máy".
  - Không bọc HMAC bên trong envelope.
  - Vẫn giữ HMAC cho token phiên của trình duyệt, và cho ticket nếu chọn ticket có MAC.

## 6. Khoá, DB, routing [ĐX]

### Enroll (thay M1)

1. Trang Máy tạo một mã enroll dùng một lần, entropy cao, hạn khoảng 10 phút [GĐ]. Server chỉ lưu hash của mã và giới hạn số lần thử.
2. `install.sh` sinh cặp khoá ký trên Pi và tải trust bundle (CA, KEM pub, sign pub, audience).
3. Xác thực bundle bằng HMAC với khoá dẫn từ mã enroll, hoặc kỹ thuật viên so fingerprint.
4. Gửi `AGENT_ENROLL` dạng bootstrap, kèm khoá công khai và PoP.

Nếu máy quét QR hoạt động như bàn phím thì có thể quét mã thay vì gõ tay [CĐC].

### Lưu khoá trên Pi

- `/etc/flexmix/agent_sign.key`, quyền 0600. `agent.env` không còn chứa secret.
- **Rủi ro:** agent chạy cùng user với kiosk, nên tiến trình kiosk đọc được khoá. Hai hướng: chấp nhận (xếp vào A3), hoặc tách phần mật mã sang một user riêng.
- Pi 5 không có TPM. Việc clone thẻ SD nằm ngoài bảo đảm.
- `QRPROTO_KEY` dùng riêng cho QR, không dùng lại cho kênh truyền.

### Xoay và thu hồi khoá (thay M5)

- **Agent tự xoay:** gửi khoá mới, ký bằng khoá cũ, kèm PoP của khoá mới. Có cửa sổ chuyển tiếp, không cần ai nhập lại.
- **Admin thu hồi:** credential chuyển sang `revoked`. Muốn dùng lại máy đó phải enroll lại.
- **Khoá KEM của server:** khoá mới được ký bằng khoá ký của server. Root offline là tuỳ chọn.

### DB server

- **Sửa:**
  - `machine`: bỏ `secret_enc`.
  - `agent_nonce` → `packet_claim`: UNIQUE(audience, kid, attempt_id), `cid`, trạng thái CLAIMED → SEAL_STARTED → SEALED, `expires_at`.
  - `machine_command`: thêm `operation_id`, `fingerprint`, `intent_deadline`, `poll_attempt_id`, trạng thái `unknown`.
- **Thêm:**
  - `machine_credential` (kid, pub, alg, status, generation)
  - `enrollment_code`
  - `server_key` (khoá riêng nằm trong file, không nằm trong DB)
  - `operation` (UNIQUE principal/action/machine/op_id, fingerprint, state, command_id)
  - `server_state` (`max_now_seen`; bản gốc của `recovery_epoch` lưu trong file nằm ngoài phạm vi backup)

### DB máy

`agent_command_done` → `agent_ledger` (machine_id, command_id, operation_id, fingerprint, state).

### routing.py

- **Chuyển sang POST:** `AGENT_COMMANDS_PATH`, `AGENT_MENU_PATH`. Tham số `wait` và `since` đưa vào body.
- **Bỏ:** `AGENT_HEARTBEAT_PATH`.
- **Thêm cho agent:** `AGENT_TRUST_BUNDLE_PATH`, `AGENT_ENROLL_PATH`, `AGENT_KEY_ROTATE_PATH`, `AGENT_SERVER_KEYS_PATH`.
- **Thêm cho quản trị:**
  - `MACHINE_ENROLL_CODE_PATH`
  - `MACHINE_CREDENTIAL_REVOKE_PATH` (thay `MACHINE_TOKEN_ROTATE_PATH`)
  - `OPERATION_PREPARE_PATH`
- **Thêm bảng `ROUTE_POLICY`:** mỗi `route_id` (tên hằng) ghi chế độ envelope (full / bootstrap / none), method và kích thước body tối đa.

## 7. Đồng hồ

- **Server:** `local stratum 10`, không nhận giờ từ mạng.
  - Giờ lệch dần không phá bảo mật, vì hạn gói được kiểm theo giờ server.
  - Lưu `max_now_seen` bền.
  - Giờ lùi quá σ: khoá mọi Seal và mọi bước dọn bản ghi.
  - Giờ nhảy tới: khoá cho tới khi người vận hành xác nhận.
  - UI hiện độ lệch giữa giờ server và giờ trình duyệt, chỉ để cảnh báo.
- **Pi:** NTP thường bị giả trong LAN chỉ gây DoS được, vì response đã bind attempt và có hạn đơn điệu.
- **NTS:** chrony có NTS server dùng cert của CA nội bộ. Để pha sau. Máy hiện dùng timesyncd (`install.sh:537-564`), cần đổi sang chrony.
- **Kết luận:** đủ cho tính đúng nếu chốt server là nguồn giờ gốc. Đây là chỗ lệch R5 (R5 đòi giờ đã xác thực, FINDINGS F02), user cần chấp nhận.

## 8. Thư viện và CPU

- **Trên máy dev:** Python 3.14, cryptography 50.0.1, không có `pyhpke`. Module `cryptography.hazmat.primitives.hpke` có từ bản 47.0.0, nhưng chỉ có single-shot: **không có AAD, không có Export** (issue pyca/cryptography #15292). Vì vậy không chạy đủ vector RFC và không làm được response theo R5.
- **Hai lựa chọn:**
  - **(a) PyHPKE**, như C3-A: có context, AAD và Export (FINDINGS F11), nhưng chưa có audit độc lập.
  - **(b) Chỉ dùng `cryptography`:** đưa M vào `info`; khoá response sinh ngẫu nhiên và gửi trong plaintext của request. Lệch R5, cần user duyệt.
- **Trên Pi:**
  - Phiên bản cryptography đang cài: [CĐC]. `install.sh:223` có import `cryptography`.
  - Mỗi request agent tốn: sinh 1 cặp khoá + 1 DH X25519, HKDF, AES-GCM, 1 lần ký. Phía server: verify, DH, open, Export, seal.
  - Tần suất thấp: poll ≤ 25 s, đơn mỗi 10 s.
  - Pi 5 có lệnh AES phần cứng. Chưa đo, cần benchmark p95 trên Pi thật làm điều kiện đi tiếp.

## 9. Sửa tài liệu và lộ trình

### Sửa TK (số dòng theo bản cũ)

- HTTP → HTTPS ở lead và ô LAN.
- Ô Bảo mật B (cả hai phía) và chú thích sơ đồ.
- Mục 2: bước 7-10 dùng envelope, response seal bằng Export, GET → POST.
- Mục 3: các dòng `agent_nonce`, `agent.env`, `agent_command_done` và bảng cổng.
- M1, M2, M3: viết lại.
- **M4 viết lại toàn bộ** thành pipeline middleware.
- M5: xoay + thu hồi khoá.
- A1: bỏ câu "token đi rõ".
- K2, L2, L4, N5: thêm ticket, deadline, sha256 media.
- Mục 5: bảng phong bì, method, loại lệnh, các sửa đổi routing.
- Mục 6: schema.
- Mục 7: bước 5-6.
- Mục 8: TLS terminator; thêm `security/envelope.py`, `keys.py`, `claims.py`, `tickets.py`.
- Mục 9: mở lại quyết định "chưa dùng TLS", thêm các rủi ro mới (CA trên điện thoại, cert hết hạn, khoá đọc được từ kiosk, PyHPKE chưa audit).

### Lộ trình

| Pha | Việc |
|---|---|
| P0 | Chốt các câu hỏi ở mục 10. Viết spec `sm-draft1`. Chạy vector RFC 9180 và benchmark trên Pi |
| P1 | TLS + CA nội bộ + nginx hoặc cheroot |
| P2 | Khoá, enroll, thu hồi |
| P3 | Middleware kênh agent: verify / Open / claim / Seal một lần, POST, giới hạn ingress |
| P4 | Ticket + ledger + `intent_deadline` |
| P5 | Đồng hồ: `max_now_seen`, chrony, NTS tuỳ chọn |
| P6 | Test phản ví dụ, test tải, runbook |
| P7 (tuỳ chọn) | Root offline, witness / chuỗi hash, `recovery_epoch` |

## 10. Cần user chốt

1. Envelope chỉ cho kênh agent (đề xuất), hay cả trình duyệt?
2. Thư viện: PyHPKE (đúng R5) hay chỉ `cryptography` (lệch R5 ở phần response)?
3. Chữ ký: P-256 (giữ C2-B) hay Ed25519?
4. TLS: nginx đứng trước waitress, hay đổi sang cheroot?
5. Root offline: làm ngay, để sau, hay bỏ?
6. Ai được tạo mã enroll?
7. Chấp nhận dùng server làm nguồn giờ gốc và khoá khi giờ lùi? NTS và RTC: làm ngay hay để sau?
8. Witness, chuỗi hash và `recovery_epoch` để pha sau được không? Có chấp nhận cài CA lên điện thoại nhân viên?

## Nguồn web agent dẫn

- cryptography HPKE: https://cryptography.io/en/stable/hazmat/primitives/hpke/
- Issue AAD: https://github.com/pyca/cryptography/issues/15292
- PyHPKE: https://pyhpke.readthedocs.io/en/latest/api.html
- WebCrypto secure curves (Igalia): https://blogs.igalia.com/jfernandez/2025/02/28/can-i-use-secure-curves-in-the-web-platform/
- MDN deriveKey (secure context): https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/deriveKey
- waitress reverse proxy: https://github.com/Pylons/waitress/blob/v2.1.1/docs/reverse-proxy.rst
