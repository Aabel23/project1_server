# Tranh luận architect X và Y: thiết kế cuối cho server mẹ có middleware mã hoá

Bắt đầu: 2026-10-08.

- **X:** trung thành với R5.
- **Y:** đơn giản, dễ vận hành.
- Cả hai đều dùng Opus và chỉ đọc nguồn.

## Vòng 1: X

**Lập trường:** giữ R5 (C1-A, C2-B, C3-A, D3-B, D5-A, D6-A), chỉ nới ở chỗ có bằng chứng bối cảnh khác.

### Lớp mã hoá và phạm vi

- **Envelope R5:**
  - HPKE Base X25519 / HKDF-SHA256 / AES-128-GCM.
  - Chữ ký ECDSA P-256 kiểm trước khi Open.
  - Nhãn `flexmix-sm-*-v1`.
- **Phạm vi:**
  - Mọi route agent đều dùng envelope.
  - Ngoại lệ 1: trust-bundle, xác thực bằng HMAC theo mã enroll.
  - Ngoại lệ 2: media chỉ đi TLS, có `sha256` và `size` nằm trong snapshot đã seal.
  - Trình duyệt: TLS + session, không envelope, vì JS do chính server giao.
- **Phản bác FM-1 của B:**
  - User yêu cầu rõ phải có lớp mã hoá bên trong.
  - FM-1 vẫn bắt server giữ secret ở dạng giải mã được.
  - A1 không chỉ là proxy.

### Thư viện và response

- PyHPKE cho phần HPKE, `cryptography` cho ECDSA.
- Gate P0: chạy vector RFC 9180, có cả Export. Không đạt thì dừng và hỏi user.
- **Response:**
  - Lấy Export, trộn thêm `rn` 16 byte ngẫu nhiên (RFC 9458), qua HKDF ra key/nonce.
  - Bỏ CAS `SEAL_STARTED` và bỏ lưu bytes đã seal.
  - Đây là chỗ lệch R5 §5, cần user chốt.

### Khoá và enroll

- P-256 (giữ C2-B). Máy chỉ có khoá ký.
- **Enroll bằng mã một lần ≥100 bit:**
  1. Agent nhận trust bundle có HMAC theo `K_code`.
  2. Agent sinh khoá, gửi enroll ở chế độ bootstrap kèm PoP.
  3. Server tiêu mã trong cùng transaction với việc insert credential.
- **Sửa B7:** agent chạy bằng user riêng `flexmix-agent`, khoá đặt ở `/var/lib/flexmix-agent`. Thêm `display-helper` chạy cùng user kiosk, nói với agent qua unix socket.
- **Xoay khoá:** ký bằng khoá cũ, kèm PoP khoá mới, khoá cũ chuyển sang `retiring`.
- **Thu hồi:** credential `revoked`, muốn dùng lại phải enroll lại.
- Lỗi chưa xác thực chỉ là lỗi vận chuyển (sửa B5).

### TLS

- Dùng cheroot, server tự kết thúc TLS. Không đặt proxy phía trước (G1).
- Hai listener: cổng quản trị và cổng agent, mỗi cổng một pool thread.
- CA nội bộ mới. Không dùng lại CA trong `.caddy-data` vì `root.key` đã lộ.

### Pipeline ở server

1. Ingress.
2. Frame.
3. Kiểm rẻ M: audience, kid, route, hạn, tra claim chỉ-đọc.
4. ECDSA.
5. Open.
6. JSON.
7. Một transaction: claim + kiểm credential + upsert.
8. `machine_id` lấy từ credential.
9. Handler.
10. Seal.
- Lỗi trước claim trả 4xx thân cố định.
- InnoDB `innodb_flush_log_at_trx_commit=1`.

### Đồng hồ

- Server là nguồn giờ gốc.
- Lưu `max_now_seen`. Giờ lùi thì khoá admission và khoá bước dọn bản ghi.
- Không áp D2-C.
- Máy dùng attempt + BOOTTIME để kiểm freshness.

### Lệnh

- `command_id` 16 byte, fingerprint gồm cả `args_bytes`.
- Trạng thái: `queued → offered → done/failed/failed_no_effect/unknown`.
- Giao lại cùng id trong hạn, cùng epoch, cùng generation. Có outbox.
- Deadline BOOTTIME.
- **Dùng operation ticket R5 cho mọi lệnh có tác dụng từ trình duyệt** (K2, L1–L4). Lý do: phản ví dụ restore F4.

### Restore

- `server_epoch` lưu trong file ngoài vùng backup.
- `restore.sh` sinh epoch mới, xoay `ticket_key`, áp lại `revoked.list`.
- Agent đối soát ledger, so menu theo sha256.

### Lỗi B1–B14 sau khi đổi giao thức

- **Tự hết:** B1, B6.
- **Phải sửa riêng:** B9, B10 (CSP khả thi), B11 (hai pool thread, mỗi máy một long-poll), B13.
- **Chờ user:** B12.

### Thay đổi cụ thể

- **routing.py:**
  - POST cho commands/menu.
  - `command_result` không còn `{id}` trên path.
  - Media theo sha256.
  - Thêm enroll, bundle, xoay khoá, thu hồi, `OPERATION_PREPARE`/`STATUS`, display apply/keep.
  - Thêm `ROUTE_POLICY`.
- **DB:** đã liệt kê đầy đủ trong báo cáo X.
- **Luồng:** 22 → 24, thêm M6 (khôi phục DB) và L0 (vòng đời lệnh).

### Chờ user

1. `response_nonce`.
2. Media đi ngoài envelope.
3. Xác thực lại cho `used→unused`.
4. Cài CA lên điện thoại.
5. Agent chạy bằng user riêng.
6. TTL mã enroll và hạn cert.

## Vòng 1: Y

**Lập trường:** chọn FM1, phương án lai, gọn hơn R5.

### Lớp mã hoá và phạm vi

- **Request:** HPKE Base single-shot, suite X25519 / HKDF-SHA256 / AES-128-GCM (giữ C1-A), mã hoá tới khoá KEM của server đã ghim lúc ghép máy. Ký thêm bằng **Ed25519**.
- **Response:** AES-128-GCM bằng `resp_key` 16 byte. Máy tự sinh `resp_key` và gửi kín bên trong request. Nonce ngẫu nhiên, nên A1 tự hết.
- **Thư viện:** chỉ dùng `cryptography`, Pi đã có sẵn.
  - M ràng buộc qua `info = Tuple("fm1-req", SHA256(M))`.
  - Không dùng PyHPKE và Export.
- **Phạm vi:**
  - Mọi route agent đều dùng FM1.
  - Media chỉ đi TLS + sha256/size.
  - Trình duyệt: TLS + cookie HttpOnly + CSP, không envelope.
- **Lý do lớp trong có giá trị thật, không chỉ vì user yêu cầu:** `.caddy-data` đang để lộ `root.key` cho mọi người đọc. Đây là A1 thực tế do lỗi vận hành PKI. Khoá KEM của FM1 được ghim độc lập với PKI của TLS.

### Kiểm thử P0

API của `cryptography` không có AAD, nên không chạy nguyên văn vector RFC 9180 được. Thay bằng kiểm liên thông byte-exact với một cài đặt độc lập, dùng aad rỗng.

### Khoá và ghép máy

- Dùng Ed25519 thay P-256. Lý do giữ P-256 ở R5 là Android Keystore, server mẹ không có app nên không áp dụng.
- **Ghép máy:**
  - Mã một lần ≥ 80 bit, hạn 10 phút, tối đa 5 lần thử.
  - Trust bundle có HMAC theo mã.
  - Enroll dạng FM1, `kid="enroll"`, kèm proof HMAC.
- **Sửa B7:**
  - Agent chạy bằng user riêng `flexmix-agent`.
  - Việc cần quyền kiosk đi qua helper `flexmix-local`, gọi bằng `sudo -n -u flexxource`, chỉ nhận động từ có ngữ pháp chặt.
  - MySQL có tài khoản riêng cho agent.
  - Phương án lùi: vẫn chạy user kiosk, khoá đặt ngoài thư mục dự án.
- **Thu hồi:**
  - Server vẫn mở gói của credential đã thu hồi, chỉ để trả response đã seal `{status:"revoked"}`. Agent dừng dựa trên thông báo có xác thực.
  - Không xoay khoá máy định kỳ ở pha đầu.
- **Clone thẻ SD:** chỉ phát hiện được (mỗi máy một poll; `issued_at` lùi dưới high-water thì bật cờ).

### TLS

- Dùng cheroot. CA nội bộ do `make_ca.py` sinh; `root.key` chép ra USB rồi xoá khỏi server.
- Không ghim SPKI của leaf.
- IP server phải cố định.
- Cổng 80 chỉ redirect và cho tải `ca.crt` kèm vân tay.

### Pipeline ở server (13 bước, kiểm rẻ trước)

1. Ingress.
2. Frame.
3. Kiểm rẻ M:
   - `|issued_at−now| ≤ W`;
   - `issued_at ≥ hw(kid) − W`;
   - tra claim chỉ-đọc.
4. Ed25519.
5. HPKE decrypt.
6. JSON.
7. Một transaction: claim + kiểm credential active + cập nhật high-water.
8. `machine_id` lấy từ credential.
9. Module.
10. Seal.

- **Dọn claim:** theo high-water của từng kid, không theo giờ hệ thống.
- **Chống cạn thread:** mỗi máy một long-poll, giữ thread dự trữ cho quản trị.

### Đồng hồ

- Mọi quyết định thời gian nằm ở server (W + high-water theo kid).
- Agent dùng `ttl_ms` đo bằng BOOTTIME.
- Pi giữ timesyncd, chỉ trỏ `NTP=` về server.
- Bỏ CLOCK_UNTRUSTED, D2-C và NTS.

### Lệnh

- `command_id` 16 byte; fingerprint gồm `args_bytes`.
- **Trạng thái:**
  - `queued → offered → done/failed`;
  - `offered → unknown`;
  - `queued → expired/cancelled`;
  - `unknown → done/failed/expired` (nhờ nút "Kiểm tra" qua lệnh `ledger.query`).
- Giao lại cùng id trong hạn. Outbox giữ kết quả tới khi được ack.
- **Trình duyệt dùng idempotency key:** `crypto.randomUUID()` + UNIQUE(created_by, request_key), **thay** cho operation ticket có MAC.

### Restore

- **Tự phát hiện:** `server_epoch` lưu ở cả bảng `server_state` lẫn file. Khác nhau lúc khởi động ⇒ DB vừa restore. Server sinh epoch mới, chuyển lệnh queued/offered sang unknown, đổi khoá ký token phiên.
- Agent so menu theo cặp (epoch, version), đặt lại con trỏ đơn/lỗi, gửi lại outbox.

### Lỗi B, A, G sau FM1

- **Tự hết:** B1, B2, B6, A1, G1, G2.
- **Phải sửa riêng:** B3, B4, B5, B7, B9, B10, B11, B13.
  - B10: CSP; thay khoảng 78 chỗ `innerHTML`; dùng cookie thay Bearer trong sessionStorage.
- **Chờ user:** B12 (xác thực lại cho used→unused và in lại vé).

### Thay đổi cụ thể

- **routing.py:**
  - `AGENT_RESULTS_PATH` POST theo lô.
  - Media theo sha256.
  - Thêm trust, enroll, revoke, command status/check, display apply/keep, step-up, `ca_cert`.
  - Thêm `ROUTE_POLICY`.
- **Luồng:** thêm M6.

### Đặc tả HTML

- **HTML mới phải chạy offline hoàn toàn**, không nạp Mermaid từ CDN.
- Thêm các mục:
  - bảng "ai thấy gì";
  - hình hai user trên Pi + helper;
  - bố cục byte của envelope.

### Chờ user

1. Envelope chỉ cho kênh máy.
2. Ba chỗ lệch R5: Ed25519, `cryptography` thay PyHPKE, `resp_key` thay Export.
3. Agent chạy user riêng + helper.
4. Xác thực lại cho used→unused.
5. Cài CA lên điện thoại.
6. Dùng cheroot.

## Điểm khác nhau sau vòng 1

| # | Vấn đề | X | Y |
|---|---|---|---|
| 1 | Thư viện và response | PyHPKE + Export + `rn` | `cryptography` + `resp_key` gửi kín trong request |
| 2 | Chữ ký | P-256 (giữ C2-B) | Ed25519 |
| 3 | Chống trùng thao tác từ trình duyệt | Operation ticket có MAC, gắn epoch | Idempotency key + tự đánh dấu unknown khi phát hiện restore |
| 4 | Phát hiện restore | Chỉ qua `restore.sh` | Tự động: so epoch giữa DB và file |
| 5 | Xoay khoá máy | Agent tự xoay | Không xoay định kỳ ở pha đầu |
| 6 | Credential bị thu hồi | Không seal; agent lùi mãi | Seal `{status:"revoked"}`; agent dừng |
| 7 | Helper quyền kiosk | Service unix socket | Gọi qua `sudo -n` |
| 8 | Đồng hồ server | `max_now_seen` + khoá khi giờ lùi | W + high-water theo kid, không khoá toàn cục |
| 9 | Hai listener | Hai cổng, hai pool thread | Một pool, giữ thread dự trữ |

**Đã đồng thuận:**

- Envelope chỉ cho kênh agent; trình duyệt dùng TLS + session.
- Media chỉ đi TLS + sha256.
- Dùng cheroot, không đặt proxy.
- CA nội bộ mới.
- Agent chạy user riêng.
- Kiểm rẻ trước verify.
- `machine_id` lấy từ credential.
- Máy trạng thái lệnh có unknown, giao lại cùng id, outbox.
- `server_epoch`.
- Thêm M6.
- Sửa B9–B13.

## Vòng 2: X phản biện Y

X chấp nhận 8/9 điểm của Y, kèm điều kiện, và nêu **"không còn bất đồng chặn"**.

### Từng điểm

1. **FM1 + `cryptography` + `resp_key`: chấp nhận.**
   - Lý do R5 chọn PyHPKE là để có Export (D:89-90). FM1 không cần Export nên lý do đó mất.
   - Điều kiện:
     - Mỗi attempt sinh `resp_key` mới.
     - Response có AAD bắt buộc: `Tuple("fm1-resp", SHA256(M))`.
     - `info` tối đa 64 byte.
     - P0: pin phiên bản `cryptography`, kiểm liên thông hai chiều với một cài đặt độc lập, kiểm âm khi M bị đổi.
   - Phương án lùi nếu user không duyệt: PyHPKE + Export + `rn`.
2. **Ed25519: chấp nhận.** Cột `alg` lưu theo từng credential, giữ đường đổi sang P-256 nếu sau này có TPM.
3. **Idempotency key: chấp nhận**, với luật JS:
   - Key chỉ nằm trong RAM của trang.
   - Gặp 401 thì bỏ mọi thao tác đang chờ.
   - Server lưu fingerprint body theo key; cùng key khác body thì trả 409.
   - Cơ chế đỡ restore: epoch đổi kéo theo đổi khoá ký token phiên, nên request thử lại sẽ bị 401.
4. **Tự phát hiện restore: chấp nhận và hợp nhất.**
   - Mất file epoch thì coi như epoch mới.
   - Mọi lệnh queued/offered chuyển sang unknown.
   - **Giữ `revoked.list` ngoài vùng backup** để restore không hồi sinh credential đã bị thu hồi.
   - Thêm nút "Kiểm tra".
5. **Không xoay khoá máy định kỳ: chấp nhận.** M5 đổi tên thành "Thu hồi và enroll lại". Route xoay khoá dời sang P7.
6. **Seal phản hồi `{status:"revoked"}`: chấp nhận.** Kèm rate-limit theo kid và không tạo tác dụng phụ.
7. **Helper gọi qua `sudo -n`: chấp nhận.**
   - Helper và file sudoers thuộc root. Output của helper coi là không tin cậy.
   - Deadline 20 s của L4 lưu bền. Agent khởi động lại mà thấy đã quá hạn thì revert.
8. **Đồng hồ dùng W + high-water theo kid: chấp nhận.**
   - Chống phát lại không phụ thuộc giờ tường của server.
   - Thêm thao tác "đặt lại high-water" cho người vận hành.
   - So giờ thực với monotonic chỉ để hiện banner.
9. **Hai listener: X GIỮ, không chặn.**
   - Kịch bản: handshake TLS chậm chiếm worker ngay trước khi định tuyến, và có thể nghẽn cả khâu accept.
   - Hai listener còn cho đặt firewall riêng cho từng cổng.
   - Hợp nhất: hai listener, cộng các semaphore của Y.

- **HTML chạy offline: chấp nhận.**

### Phát hiện mới của X

- **Vấn đề:** code và venv của agent phải nằm ngoài thư mục mà user kiosk ghi được. Hiện project nằm ở `/home/flexxource/hungvu/version1.0`.
- **Cách làm:**
  - Cài agent ở `/opt/flexmix-agent`, venv riêng, quyền `root:root 755`.
  - Vendor `admin_functions` vào gói agent.
  - Không import code từ `/home/flexxource` lúc chạy.

### Các chỗ lệch R5 cần user chốt

1. Dùng `cryptography` + `resp_key` thay cho PyHPKE + Export (C3-A, §5).
2. Ed25519 thay P-256 (C2-B).
3. Idempotency key thay operation ticket.
4. Seal phản hồi "revoked".
5. Đồng hồ dùng high-water thay khoá theo giờ (§6).
6. Bỏ manifest và root offline ở pha đầu (D1-B).
7. Media đi ngoài envelope.

## Vòng 2: Y phản biện X

Y nêu **"không còn bất đồng chặn"**.

### Ba câu hỏi bắt buộc

**(a) Khi khoá KEM của server bị lộ**

- `resp_key` và Export + `rn` lộ như nhau: cả hai đều là HPKE Base, không có forward secrecy.
- Khác biệt thật:
  - Export + `rn` là mẫu có trong RFC.
  - Request của Y mang theo một bí mật. Middleware phải tách `LP(resp_key)` ra trước khi chuyển cho handler, và không được log.
  - Wire của Y làm được bằng cả `cryptography` lẫn PyHPKE.

**(b) Kiểm thử P0, gate hợp nhất**

1. Chạy vector RFC 9180 đầy đủ trên PyHPKE, dùng làm bản tham chiếu, chỉ có trong môi trường test.
2. Kiểm liên thông byte-exact giữa `cryptography` và PyHPKE.
3. Test âm.
4. Xác nhận upstream có chạy vector.

Theo quy tắc dừng của X: không đạt thì dừng lại và hỏi user.

**(c) Idempotency key khi restore DB**

- Nếu không gắn epoch thì **không an toàn**: phản ví dụ F4 của X đúng.
- Sửa:
  - Form nhận `server_epoch` lúc tải trang và gửi kèm theo.
  - Epoch đã khác → server trả 409 "tải lại trang".
  - Cùng key mà khác body → conflict.

### Chín điểm

1. **`resp_key` + `cryptography`:** Y giữ, không chặn. Đưa user chọn giữa hai phương án.
2. **Chữ ký:** Y **chuyển sang P-256** để bớt một chỗ lệch R5 và dùng chung adapter với androidv0.1.
3. **Chống trùng thao tác:** idempotency key gắn epoch + fingerprint; bỏ `OPERATION_PREPARE`.
4. **Restore, hợp nhất:**
   - File epoch và `revoked.list` nằm ngoài vùng backup.
   - Có `restore.sh`.
   - So epoch cả lúc khởi động lẫn trong transaction claim.
   - Agent gửi lại ledger N giờ gần nhất.
5. **Xoay khoá máy:** dùng giao thức của X, kích hoạt bằng nút ở P6. Lợi ích: ảnh thẻ SD cũ mất hiệu lực, và lộ ra nếu có clone.
6. **Credential bị thu hồi:** Y **chuyển sang không seal**. Từ chối ngay ở bước kiểm rẻ. Agent lùi tối đa khoảng 5 phút và ghi trạng thái "cần ghép lại".
7. **Helper:** Y **chuyển sang service unix socket** `flexmix-local`, kiểm SO_PEERCRED.
   - Lý do: timer revert 20 s của L4 phải sống trong tiến trình giữ màn hình.
   - Phản biện nhóm setgid: `publish_menu` ghi theo kiểu tạo tạm rồi rename.
8. **Đồng hồ, hợp nhất:** W + high-water. `max_now_seen` chỉ dùng để hiện banner. Có thao tác "Xác nhận giờ đúng" (bắt xác thực lại) để đặt lại high-water. Không khoá toàn cục.
9. **Hai listener:** chấp nhận.

## Sau vòng 2: hai bên đổi chéo

Ở bốn điểm 2, 5, 6, 7, mỗi bên đều chuyển sang ý ban đầu của bên kia:

| Điểm | X sau vòng 2 | Y sau vòng 2 |
|---|---|---|
| Chữ ký | Ed25519 | P-256 |
| Helper | `sudo -n` | Service socket |
| Credential bị thu hồi | Seal `{revoked}` | Không seal, lùi ≤ 5 phút |
| Xoay khoá | Không làm (P7) | Có nút, P6 |

**Đã đồng thuận:**

- Response: `resp_key` + `cryptography` làm chính, PyHPKE làm bản tham chiếu trong test, Export + `rn` làm phương án lùi.
- Idempotency key gắn epoch + fingerprint, key chỉ nằm trong RAM, 401 thì bỏ thao tác đang chờ.
- Đồng hồ: W + high-water, banner, đặt lại high-water.
- Hai listener.
- Restore theo cơ chế hợp nhất.
- Agent cài ở `/opt`.

→ Mở vòng 3 để chốt bốn điểm đổi chéo.

## Vòng 3: hai bên lại đổi chéo

Ở vòng 3, cả hai cùng ghi "CHỐT" và đều đồng ý mọi bổ sung của nhau. Nhưng ở bốn điểm còn lại, **mỗi bên lại chọn đúng phương án vòng 2 của bên kia**:

| Điểm | X vòng 3 | Y vòng 3 |
|---|---|---|
| Chữ ký | P-256 + `deterministic_signing` (RFC 6979), wire r‖s low-s | Ed25519 + cột `alg` |
| Helper | Service socket. Kịch bản quyết định: agent crash lặp lại giữa 20 s thử độ phân giải → màn hình kẹt | `sudo -n` + deadline lưu bền + autostart áp lại mode đã lưu |
| Credential bị thu hồi | Không seal. Kịch bản: flood bằng kid đã thu hồi ép server tốn verify + open + seal cho từng gói | Seal `{revoked}`. Kịch bản: kỹ thuật viên cần một kết luận có xác thực, lỗi chưa xác thực không chứng minh được gì |
| Xoay khoá | Có, kích hoạt bằng nút ở P6. Kịch bản: thẻ SD bị chụp ảnh khi mang đi sửa | Không làm (P7). Kịch bản: kẻ có ảnh thẻ cũng xoay được trước máy thật |

**Kết luận của operator:** bốn điểm này là đánh đổi gần ngang nhau. Hai architect dao động qua lại hai lượt, không tự hội tụ được. Operator (phiên chính) quyết bằng kịch bản mạnh nhất của mỗi bên, và đánh dấu để user duyệt.

## Quyết định của operator cho bốn điểm dao động

1. **Chữ ký: Ed25519**, cột `alg` lưu theo từng credential.
   - Lý do: tất định sẵn, thư viện trả thẳng 64 byte, không có lớp chuyển DER → r‖s và chuẩn hoá low-s, là chỗ dễ viết sai.
   - P-256 + `deterministic_signing` cũng an toàn. Đã thử: `cryptography` 50.0.1 có hỗ trợ tham số này.
   - Lý do còn lại để chọn P-256 chỉ là bớt một chỗ lệch R5 và dùng chung adapter với androidv0.1.
   - Ghi vào danh sách lệch R5 để user chốt. User muốn khớp R5 thì đổi sang P-256 mà không ảnh hưởng gì khác.
2. **Helper: service unix socket `flexmix-local`**, user kiosk, kiểm SO_PEERCRED, tập lệnh cố định. Helper giữ timer revert 20 s.
   - Lý do: ở kịch bản agent crash lặp lại, `sudo` cộng deadline lưu bền vẫn để màn hình đen tới lần khởi động lại phiên X, có thể kéo dài hàng giờ.
   - Tiến trình nhỏ, chỉ làm một việc, giữ trạng thái màn hình là đúng mẫu admin_gui đang dùng (timer nằm trong tiến trình đổi màn hình).
3. **Credential bị thu hồi: lai.**
   - Mặc định từ chối ở bước kiểm rẻ, không verify, không open.
   - Mỗi kid được seal **tối đa một** response `{status:"revoked"}` trong một khoảng thời gian (ví dụ 1 lần/phút, tham số chưa chốt) để máy thật nhận được thông báo có xác thực.
   - Agent:
     - nhận thông báo có xác thực → dừng gửi, hiện "cần ghép lại";
     - gặp lỗi chưa xác thực → lùi tối đa khoảng 5 phút, không bao giờ dừng (B5).
   - Như vậy flood không ép được server tốn CPU (A2), mà kỹ thuật viên vẫn có kết luận chắc chắn.
4. **Xoay khoá máy: không làm ở pha đầu (P7)**, nhưng giữ sẵn các cột `generation`, `alg` và trạng thái `retiring` trong schema.
   - Lý do: ca "thẻ SD mang đi sửa" xử lý được bằng thu hồi + ghép lại khi trả thẻ, vì lúc đó kỹ thuật viên đang đứng ở máy.
   - Kẻ có ảnh thẻ cũng xoay được trước máy thật, nên giá trị của việc xoay hẹp so với độ phức tạp thêm vào.
   - M5 = "Thu hồi và ghép lại".

## Thiết kế cuối đã đồng thuận (để dựng HTML bản 2)

- **TLS:** TLS 1.3 do cheroot kết thúc, không có proxy. Hai listener (cổng quản trị, cổng agent) với hai pool thread riêng. CA nội bộ mới: root sinh offline, cất ra USB. Không dùng CA trong `.caddy-data`.
- **Trình duyệt:** TLS + cookie HttpOnly / Secure / SameSite=Strict + header `X-FM-Req` + CSP `script-src 'self'` + rate-limit đăng nhập + xác thực lại cho thao tác nhạy cảm. Không dùng envelope.
- **FM1 (chỉ kênh `/api/agent/*`):**
  - Request: HPKE Base single-shot X25519 / HKDF-SHA256 / AES-128-GCM tới khoá KEM của server, `info = Tuple("fm1-req", SHA256(M))`. Chữ ký Ed25519 trên `Tuple("fm1-sig", M, enc, ct)`.
  - Response: AES-128-GCM bằng `resp_key` 16 byte do máy sinh cho từng attempt và gửi kín trong request. Nonce 12 byte ngẫu nhiên. AAD = `Tuple("fm1-resp", SHA256(M))`.
  - Middleware tách `resp_key` ra trước khi chuyển cho handler và không log.
  - Media đi ngoài envelope: TLS + sha256 + size lấy từ snapshot.
- **Thư viện:** `cryptography`, ghim phiên bản. PyHPKE chỉ làm bản tham chiếu trong test. Gate P0: vector RFC 9180 trên PyHPKE, liên thông byte-exact, test âm; không đạt thì dừng và hỏi user. Phương án lùi: PyHPKE + Export + `rn`.
- **Pipeline server:** ingress → frame → kiểm rẻ M (audience, kid, route, `|issued_at − now| ≤ W`, `issued_at ≥ hw − W`, tra claim chỉ-đọc) → verify → open → JSON → một transaction (claim + kiểm credential + so epoch + cập nhật hw) → `machine_id` từ credential → handler → seal. Lỗi trước bước seal trả thân cố định.
- **Ghép máy:** mã một lần ≥ 80–100 bit, ngắn hạn, giới hạn số lần thử. Trust bundle có HMAC theo mã. Enroll dạng bootstrap + PoP + proof. Mã bị tiêu trong cùng transaction với việc tạo credential. Hai bên so fingerprint.
- **Trên Pi:** agent ở `/opt/flexmix-agent`, venv riêng, `root:root`, vendor `admin_functions`, user `flexmix-agent`, khoá 0600, tài khoản MySQL riêng. Helper socket chạy bằng user kiosk.
- **Lệnh:**
  - `command_id` 16 byte, fingerprint gồm `args_bytes`.
  - Trạng thái: queued → offered → done / failed; offered → unknown; queued → expired / cancelled; unknown → done / failed / expired qua "Kiểm tra" (`ledger.query`).
  - Giao lại cùng id trong hạn. Outbox. `ttl_ms` đo bằng BOOTTIME. Ledger claim trước khi chạy.
  - Từ trình duyệt: idempotency key (chỉ trong RAM) + `server_epoch` + fingerprint body; epoch khác thì trả 409; gặp 401 thì bỏ thao tác đang chờ.
- **Đồng hồ:** W + high-water theo kid. `max_now_seen` và so wall/monotonic chỉ để hiện banner. Có thao tác "Xác nhận giờ đúng" (xác thực lại) để đặt lại high-water. Pi giữ timesyncd trỏ về server. Không dùng D2-C, CLOCK_UNTRUSTED hay NTS.
- **Restore:** epoch lưu ở bảng + file ngoài backup, so lúc khởi động và trong transaction claim. Khi epoch đổi: queued/offered → unknown, đổi khoá ký token phiên, áp lại `revoked.list` (nằm ngoài backup). Agent gửi lại ledger N giờ gần nhất, so menu theo (epoch, version) hoặc sha256. Có `restore.sh` cho đường chuẩn.
- **Lỗi B9–B13:** sửa riêng như mô tả của X/Y. B12 chờ user.
- **Luồng:** M1 viết lại (ghép máy), M2 sửa nhẹ, M3 viết lại, M4 thành pipeline FM1, M5 thành thu hồi và ghép lại, thêm M6 khôi phục DB và L0 vòng đời lệnh. A1, K1, K2, L1, L2, L4, N5 có sửa.
- **Lệch R5 chờ user:**
  1. `resp_key` + `cryptography` thay PyHPKE + Export.
  2. Ed25519 thay P-256.
  3. Idempotency key gắn epoch thay operation ticket.
  4. High-water thay khoá theo giờ.
  5. Bỏ manifest và root offline ở pha đầu.
  6. Media ngoài envelope.
  7. Seal revoked có giới hạn.
