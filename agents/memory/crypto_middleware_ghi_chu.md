# Middleware mã hoá cho server mẹ: ghi chú phân tích

Bắt đầu: 2026-10-08, khoảng 01:40 (Bangkok), trong lúc user ngủ. Người viết: Claude (phiên chính).
Trạng thái: **ĐANG LÀM**. Mục 3 và 4 chờ hai agent Opus nộp kết quả.

## 0. Yêu cầu của user (nguyên ý)

- Đọc `server/docs/cryptography/`. Đây là phần middleware mã hoá gói tin **trước khi** gói được gửi lên endpoint qua **HTTPS**.
- Không hỏi lại, chỉ đọc và phân tích. Đồng thời gọi hai agent Opus 5.5 mức high:
  - Agent A: tìm các điểm triển khai và cách kết hợp với thiết kế server mẹ hiện tại.
  - Agent B: tìm lỗi hoặc chỗ cần cải tiến trong giao thức bảo mật.
- Ghi lại thành md để khi dậy có việc làm tiếp.
- Sau đó gọi hai architect tranh luận theo vòng cho tới khi chốt thiết kế cuối, rồi tạo một **HTML doc mới (bản cải tiến)**.

**Hệ quả lớn:** quyết định cũ "LAN, HTTP, chưa dùng TLS" nay đổi thành **HTTPS + một lớp mã hoá và ký ở tầng ứng dụng bên trong**. Các chỗ cần cập nhật theo:

- `phuong_an_kien_truc.md`
- `docs/thiet_ke_server_me.html`, mục 9

## 1. Đã đọc

| Nguồn | Nội dung |
|---|---|
| `server/docs/cryptography/crypto-primer.html` | Cẩm nang 18 thuật toán theo thiết kế R5 |
| `server/docs/cryptography/packet-security.html` | Sơ đồ bảo vệ gói tin hai chiều R5 |
| `server/docs/cryptography/phase-map.json` | Kế hoạch G0–G7 của middleware androidv0.1, trạng thái `planning_only` |
| `androidv0.1/agent_workspace/tasks/middleware/internal/packet-security/{design,keys,protocol,duplicates}.md` | Nguồn gốc R5 (agent đọc chi tiết) |
| `androidv0.1/doc/security-research/2026-10-07/FINDINGS.md` | Kết quả nghiên cứu bảo mật trước đó |

R5 được thiết kế cho **app điện thoại ↔ server ↔ máy** của androidv0.1. Server mẹ khác ở hai điểm: trình duyệt quản trị thay cho app, và mạng là LAN không có internet.

## 2. Phân tích của phiên chính

### 2.1 R5 tóm gọn (theo crypto-primer và packet-security)

- **Lớp ngoài:** HTTPS. **Lớp trong:** envelope = `version ‖ LP(M) ‖ LP(enc) ‖ LP(ct) ‖ LP(sig)`.
- **Mã hoá:** HPKE Base single-shot (RFC 9180).
  - KEM X25519, KDF HKDF-SHA256, AEAD AES-GCM hoặc ChaCha20. Tất cả đều là ứng viên, chưa chốt.
- **Chữ ký ngoài:** Ed25519 hoặc P-256, ký trên `Tuple(nhãn, M, enc, ct)`.
  - Kiểm chữ ký **trước** khi giải mã. Lý do: HPKE Base không chứng minh người gửi là ai.
- **M ở dạng rõ nhưng được bảo vệ:** M được ràng buộc bằng AAD và chữ ký. M gồm:
  - domain, version, suite
  - audience, server_kid, credential_kid
  - method, route_id, query
  - attempt_id, issued_at, expires_at
  - operation_id, recovery_epoch, mốc seq của server và witness
- **Chống phát lại:** claim bền `UNIQUE(audience, credential_kid, attempt_id)`, thực hiện trước mọi tác động.
- **Response:**
  - Khoá lấy bằng HPKE **Export** từ context của request, có nhãn riêng.
  - Mỗi response chỉ seal một lần, chốt bằng CAS `SEAL_STARTED`.
  - Bản mã được lưu lại; nhận lại cùng attempt thì gửi lại đúng bản đã lưu.
- **Các phần khác:**
  - Manifest khoá server, ký bởi root offline.
  - Operation ticket và ledger băm nối chuỗi.
  - Witness HMAC chống server bị restore lùi.
  - `CLOCK_UNTRUSTED`: khoá các luồng cần mã hoá khi giờ chưa tin được.
- **Tình trạng:** đã qua 5 vòng review, nhưng chưa có code HPKE, chưa chạy vector chuẩn, chưa benchmark.

### 2.2 Kiểm thư viện trên máy dev (đã chạy thật)

- Python 3.14.0, **cryptography 50.0.1** đã có module `cryptography.hazmat.primitives.hpke`.
  - KEM: X25519, P256, P384, P521, cùng hybrid hậu lượng tử **MLKEM768_X25519**, MLKEM1024_P384.
  - KDF: HKDF-SHA256/384/512.
  - AEAD: AES-128/256-GCM, ChaCha20-Poly1305.
- **API chỉ có `Suite.encrypt(plaintext, public_key, info)` và `Suite.decrypt(ciphertext, private_key, info)`.**
  - Đầu ra = `enc ‖ ct`: gói 4 byte thành 52 byte.
  - **Không có tham số AAD riêng và không có Export.**
  - Hệ quả: phần "response dùng HPKE Export" của R5 **không làm được bằng API này**. M phải được ràng buộc qua `info`; đổi `info` thì giải mã báo `InvalidTag`, đã thử.
  - Response cần một cách khác. Ví dụ: server seal response tới **khoá KEM công khai của máy**, info chứa hash của request. Hoặc dùng một thư viện có Export.
- **Chi phí:** 500 lần seal + open với gói 512 byte mất 0,073 s trên PC dev. Chưa đo trên Pi; với nhịp long-poll ≤ 25 s mỗi máy thì không đáng lo.
- **Phía máy chưa ghim phiên bản `cryptography`:** `install.sh:223` chỉ import, không ghim. Phải ghim bản có `hpke`. Chưa đối chiếu bản nào bắt đầu có module này.

### 2.3 Điểm triển khai vào thiết kế server mẹ (ý kiến phiên chính, chờ đối chiếu với agent A)

1. **Vị trí middleware: thay hai khối "Bảo mật A/B" trong sơ đồ râu.** Thứ tự đề xuất:

   ```
   TLS kết thúc → giới hạn kích thước/tần suất → parse khung LP
   → kiểm version/suite theo allowlist → verify chữ ký theo credential_kid
   → HPKE open → kiểm M (audience, route, hạn) → claim attempt_id bền
   → quyền theo feature → module → seal response
   ```

2. **Máy ↔ server (Bảo mật B): đáng áp R5 nhất.** Đổi secret HMAC dùng chung thành **cặp khoá riêng của mỗi máy**:
   - Máy giữ khoá ký Ed25519 và khoá KEM X25519. Server chỉ lưu khoá công khai.
   - Cách này **xoá được rủi ro "server giữ secret giải mã được"** ở thiết kế cũ (mục 9, M1).
   - Enroll (thay M1):
     1. Máy sinh khoá khi chạy `install.sh`.
     2. Màn kiosk hoặc terminal hiện fingerprint và một mã ngắn.
     3. Admin nhập mã trên trang Máy để duyệt.
     4. Không còn secret nào phải chép qua tay.
3. **Response của long-poll mang lệnh là chỗ R5 hợp nhất.**
   - Lệnh phải ràng buộc với đúng attempt poll và deadline. Máy kiểm trước khi chạy.
   - Vì không có Export, server seal lệnh tới khoá KEM của máy, info gồm `attempt_id` của poll và hash M của request.
4. **Lệnh vật lý** (nạp `add_gram`, in lại, màn hình):
   - `agent_command_done` hiện có là một "ledger rút gọn". Nên giữ.
   - Thêm trạng thái `unknown` khi mất kết quả, đúng tinh thần R5. Không tự gửi lại và không ghi là `failed`.
5. **Trình duyệt quản trị (Bảo mật A):** giai đoạn đầu chỉ cần **TLS + session**.
   - Session: cookie HttpOnly, Secure, SameSite=Strict, kèm CSRF token.
   - Không làm envelope trong trình duyệt. Trình duyệt không có chỗ giữ khoá riêng an toàn tương đương app.
   - Cần agent A xác nhận WebCrypto hỗ trợ được gì.
6. **TLS trong LAN không internet:**
   - Thư mục `InternProj/.caddy-data/pki/authorities/local/` đã có root và intermediate CA của Caddy. Nghĩa là đã từng dùng `tls internal`.
   - Phương án: Caddy đứng trước Flask/waitress, dùng CA nội bộ. Máy ghim root CA, hoặc ghim khoá công khai của server. Thiết bị quản trị phải cài root CA.
   - **Lưu ý:** `root.key` đang nằm trong thư mục dự án, nên phải coi là đã lộ nếu thư mục này bị chia sẻ. Khi triển khai thật phải sinh CA mới.
7. **Đồng hồ:** chrony trên server vẫn là nguồn giờ.
   - Agent không seal khi chưa đồng bộ (`CLOCK_UNTRUSTED`), máy vẫn bán.
   - Server không có internet nên giờ của chính server là gốc tin cậy. Chấp nhận việc giờ trôi.
8. **R5 có những phần nặng cần cân nhắc bỏ hoặc hoãn cho server mẹ:**
   - Manifest + root offline: có thể thay bằng ghim khoá server lúc enroll.
   - Witness chống restore lùi.
   - Operation ticket cho thao tác của trình duyệt.
   - Chờ agent B đánh giá.

## 3. Kết quả agent A (Opus): điểm triển khai

Bản đầy đủ: `crypto_A_diem_trien_khai.md`. Những ý chính:

- **R5 đã chốt ngày 07/10, nhưng hai trang HTML trong `docs/cryptography` chưa cập nhật theo:**
  - Suite C1-A: X25519 / HKDF-SHA256 / **AES-128-GCM**.
  - Chữ ký: **ECDSA P-256** (C2-B).
  - Thư viện: **PyHPKE** (C3-A).
  - Route được bảo vệ **không dùng GET hay query string**.
- **Envelope chỉ dùng cho kênh agent `/api/agent/*`.** Trình duyệt dùng TLS + session như admin_gui, thêm ticket cho lệnh vật lý. Lý do: JS do chính server giao, nên ai MITM được TLS thì thay được cả JS, envelope trong trình duyệt không thêm bảo đảm. Ngoài ra WebCrypto chỉ chạy được trong secure context.
- **Waitress không làm TLS.** Phải đặt nginx ở localhost phía trước, hoặc đổi sang cheroot.
- **Khoá máy:** bỏ HMAC + `secret_enc`.
  - Khoá ký sinh ngay trên Pi.
  - Enroll bằng mã dùng một lần do trang Máy tạo.
  - Agent tự xoay khoá; admin thu hồi.
- **Lệnh vật lý:** K2 và L2 bắt buộc có ticket + ledger. L4 cần `intent_deadline` cộng đồng hồ đơn điệu.
- **Đổi tên và thêm bảng:**
  - `agent_nonce` → `packet_claim`.
  - Thêm `machine_credential`, `enrollment_code`, `operation`, `server_state`.
  - Trên máy: `agent_command_done` → `agent_ledger`.
- **routing.py:**
  - `AGENT_COMMANDS_PATH` và `AGENT_MENU_PATH` chuyển sang **POST**.
  - Bỏ `AGENT_HEARTBEAT_PATH`.
  - Thêm các route enroll, trust bundle, xoay khoá, thu hồi, `OPERATION_PREPARE`, kèm bảng `ROUTE_POLICY`.
- **Lộ trình P0–P7:** P0 chốt câu hỏi và chạy vector/benchmark → P1 TLS → P2 khoá → P3 middleware → P4 ticket/ledger → P5 đồng hồ → P6 kiểm thử → P7 tuỳ chọn.
- **8 câu cần user chốt:** xem mục 10 của file đầy đủ.

## 4. Kết quả agent B (Opus): lỗi và cải tiến giao thức

Bản đầy đủ: `crypto_B_kiem_dinh.md`. Những ý chính:

### Lỗi trong thiết kế server mẹ hiện tại

- **Mức Cao:**
  - **B1:** chữ ký phản hồi giống chữ ký request và không có nonce của request, nên phản chiếu hoặc phát lại được.
  - **B2:** NTP giả kết hợp với việc dọn dedup sau 7 ngày làm `add_gram` chạy lại được.
  - **B3:** restore DB làm `command_id` trùng.
  - **B4:** delivered/expired gộp chung "máy chưa nhận" với "máy đã chạy mà mất kết quả", nên người dùng bấm lại là nạp hai lần.
- **Mức Trung bình:**
  - **B5:** một gói 401 giả làm máy ngừng đồng bộ.
  - **B6:** chuỗi ký thiếu query và status.
  - **B7:** secret đọc được từ tiến trình kiosk.
  - **B8:** clone thẻ SD.
  - **B9:** máy này ghi được kết quả cho lệnh của máy khác.
  - **B10:** XSS xuyên máy lấy được token owner.
  - **B11:** cạn thread của waitress.
  - **B12:** đổi vé `used→unused` từ xa.
  - **B13:** media không giới hạn kích thước.
- **Mức Thấp:**
  - **B14:** thứ tự kiểm nonce và HMAC, và lỗi múi giờ khi thu hồi phiên.

### Lỗi trong R5 hoặc khi ghép R5 vào server mẹ

- **Mức Cao:**
  - **A1:** khoá và nonce của phản hồi suy tất định từ Export. Seal hai lần là lặp nonce GCM.
    - Cách sửa: trộn một `response_nonce` ngẫu nhiên vào (RFC 9458).
  - **G2:** đem D2-C (khoá khi lệch giờ) vào LAN không có internet sẽ khoá oan cả hệ thống.
- **Mức Trung bình:**
  - **A2:** verify ECDSA chạy trước các phép kiểm rẻ.
  - **G1:** waitress không làm TLS, phải thêm proxy, mà proxy lại là một A1 theo đúng định nghĩa của R5.
  - **G3:** phần độ bền R5 viết cho SQLite, còn ở đây là MySQL.
  - **G4:** mọi lệnh mất phản hồi đều thành unknown thì Wi-Fi chập chờn sẽ bắt đối soát tay liên tục.

### Nhận định lớn của B

- **HPKE + chữ ký chỉ có giá trị khi có một bên khác server kết thúc TLS** (gọi là A1). Trong LAN dùng TLS trực tiếp có pin thì lớp này thừa.
- **B đề xuất giao thức gọn hơn, FM-1:**
  - TLS 1.3 + pin SPKI.
  - HMAC với khoá tách theo chiều (HKDF m2s/s2m).
  - Phản hồi ký trên nonce của request.
  - `command_id` 128-bit + fingerprint + outbox + trạng thái unknown.
  - `server_epoch` đổi khi restore.
  - Tuỳ chọn khoá Ed25519 do máy tự sinh.
- **Ý kiến phiên chính:** nhận định này **mâu thuẫn với ý user** muốn có middleware mã hoá. Đưa vào tranh luận architect để cân nhắc: nếu TLS kết thúc ở nginx thì A1 có tồn tại (dù proxy nằm trên chính máy server), và user muốn bảo vệ cả trước proxy.

## 5. Tranh luận architect và thiết kế cuối

Đã chạy hai architect Opus song song, mỗi người một thiên hướng:

- **X:** trung thành với R5 và với yêu cầu của user.
- **Y:** đơn giản, dễ vận hành trên Pi, sửa triệt để các lỗi B tìm ra.

Đề bài của cả hai giống nhau: D1–D10, kèm đặc tả cho HTML mới. Ràng buộc cứng: **phải có lớp mã hoá nội dung bên trong TLS**, vì user đã nói rõ.

Quy trình: vòng 1 mỗi bên đề xuất độc lập → các vòng sau phản biện chéo cho tới khi không còn bất đồng chặn → phiên chính hợp nhất → dựng HTML mới.

### Kết quả

Diễn biến từng vòng ghi ở `crypto_tranh_luan.md`. Tóm tắt:

- **Vòng 1:**
  - X đề xuất R5 gần nguyên bản.
  - Y đề xuất "FM1", một bản lai gọn hơn.
- **Vòng 2:** X chấp nhận 8/9 điểm của Y. Y chấp nhận nhiều điểm của X. Kết quả là hai bên **đổi chéo** ở 4 điểm.
- **Vòng 3:** hai bên lại đổi chéo đúng 4 điểm đó, tuy cả hai cùng ghi "CHỐT".
- **Operator chốt 4 điểm còn dao động**, mỗi điểm theo kịch bản mạnh nhất. Lý do chi tiết ở `crypto_tranh_luan.md`.
  1. Chữ ký: Ed25519.
  2. Helper: unix socket.
  3. Credential bị thu hồi: seal thông báo, có giới hạn tần suất.
  4. Xoay khoá máy: chưa làm ở pha đầu.
- **Thiết kế cuối:** HTTPS (cheroot, CA nội bộ) + **FM1** chỉ cho kênh máy.
  - Request: HPKE X25519 / HKDF-SHA256 / AES-128-GCM, ký Ed25519.
  - Response: AES-GCM bằng `resp_key` máy gửi kèm trong request.
  - Trình duyệt: TLS + cookie phiên + CSP.
  - Lệnh: vòng đời có trạng thái unknown.
  - Restore: tự phát hiện qua `server_epoch`.
- **HTML mới:** `server/docs/thiet_ke_server_me_v2.html`.
  - Chạy offline: Mermaid đã tải về `docs/vendor/`, font lấy từ `docs/cryptography/fonts`.
  - 12 sơ đồ tuần tự dựng sẵn, 20 sơ đồ khối và trạng thái. Đã render thử bằng Chrome headless: 0 lỗi.

## 6. Việc khi user dậy

1. **Đọc** `server/docs/thiet_ke_server_me_v2.html`. Bản 1 vẫn giữ ở `thiet_ke_server_me.html`.
2. **Chốt các mục ở mục 13 của HTML.** Quan trọng nhất:
   - **Lệch R5:**
     - `cryptography` + `resp_key` thay PyHPKE + Export.
     - Ed25519 thay P-256.
     - Idempotency key gắn epoch thay operation ticket.
     - W + high-water thay khoá theo giờ.
     - Hoãn manifest và root offline.
     - Media đi ngoài FM1.
     - Seal thông báo revoked có giới hạn.
   - **Cài root CA** lên điện thoại và máy tính quản trị.
   - **B12:** bắt nhập lại mật khẩu khi đổi vé `used→unused`.
   - **Các tham số:** W, TTL mã ghép, hạn cert, N giờ gửi lại ledger, số cổng.
3. **Duyệt 4 điểm operator đã chốt thay** (mục 5 ở trên). Có thể đổi; mỗi điểm đã có sẵn phương án còn lại.
4. **Câu hỏi mở từ agent kiểm định B:**
   - Máy đang bind Tailscale, vậy thực tế có internet không?
   - Có proxy hay middlebox nào kết thúc TLS không?
   - Server có RTC không?
   - App Android theo R5 có nói chuyện trực tiếp với server mẹ không?
5. **Việc nhỏ cần user quyết:**
   - `server/routing.py` và `server/server/config/routing.py` đang trùng nhau, nên giữ một.
   - routing.py cần sửa theo mục 7 của HTML v2. **Chưa sửa code.**
   - Hai file trong `docs/cryptography/` vẫn ghi suite cũ (lỗi A3). Đây là bản chép từ androidv0.1, nên chưa sửa.
   - **Bảo mật:** `InternProj/.caddy-data/pki/authorities/local/root.key` là khoá riêng của một CA đang nằm trong thư mục dự án. Không dùng lại CA này. Cân nhắc xoá hoặc chuyển ra khỏi thư mục.
6. **Bước kỹ thuật kế tiếp khi đã chốt (P0):**
   - Spike kiểm liên thông HPKE giữa `cryptography` và PyHPKE (cần `pip install pyhpke`, máy dev chưa có).
   - Test âm.
   - Benchmark trên Pi thật.
   - Kiểm phiên bản `cryptography` trên Pi.
