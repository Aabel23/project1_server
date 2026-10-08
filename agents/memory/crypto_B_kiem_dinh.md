# Agent B (Opus): kiểm định giao thức R5 và server mẹ

Ngày 2026-10-08. Agent chỉ đọc, không chạy code, không đo. Đây là báo cáo gốc, phiên chính chỉ định dạng lại.

## Ký hiệu

- **Đ**: đã đối chiếu tới số dòng.
- **S**: suy luận.

## Viết tắt áp dụng

- **A**: giao thức R5.
- **B**: thiết kế server mẹ.
- **ghép**: khi đưa R5 vào server mẹ.

`thiet_ke` = `server/docs/thiet_ke_server_me.html`, số dòng theo bản trước đợt sửa đêm 08/10.

## 1. Bảng phát hiện

| ID | Mức | Áp | Kịch bản → hậu quả | Đề xuất | Nguồn |
|---|---|---|---|---|---|
| B1 | Cao | B | **Phản hồi ký "cùng cách" với request:** cùng secret, cùng chuỗi, không chứa nonce của request, không tách chiều.<br><br>**(a) Phản chiếu:** chữ ký của phản hồi `GET /api/agent/commands` đem gửi lại như một request thì HMAC vẫn khớp. Server coi đó là máy đang poll: trao lệnh queued cho kẻ tấn công, đánh dấu delivered, cập nhật `last_seen`. Chiều ngược: trả lại cho agent chính chữ ký request `POST …/stock` hoặc `…/result` → agent tin đã gửi xong.<br><br>**(b)** Phản hồi cũ phát lại được trong 120 s, hoặc sau khi agent khởi động lại (nonce chỉ nằm trong RAM). | Tách khoá theo chiều (HKDF, nhãn m2s/s2m). Phản hồi ký trên nonce của request, status, `server_epoch` và `sha256(body)`. Agent chỉ nhận phản hồi khớp nonce của request đang chờ. | Đ thiet_ke:826–829, 1488–1491 |
| B2 | Cao trên HTTP, TB khi có TLS | B | NTP trong LAN không có xác thực. Agent kiểm `ts` của phản hồi bằng đồng hồ máy, và `agent_command_done` bị dọn sau 7 ngày. Ghi lại một phản hồi `add_gram`, sau 7 ngày giả NTP lùi giờ máy rồi phát lại → kho bị cộng ảo. `order_mode.set` không có dedup. Phía server cũng vậy: chỉnh giờ lùi quá cửa sổ → request cũ hợp lệ trở lại. | Freshness của phản hồi lấy từ nonce request, không từ giờ. Dedup giữ theo epoch chứ không theo tuổi. Dọn `agent_nonce` theo high-water `ts` của từng máy. Chỉnh giờ lùi lớn thì đổi generation khoá. | Đ thiet_ke:653, 658, 669, 747, 829, 1521, 1670 |
| B3 | Cao | B | Restore hoặc khởi tạo lại DB server. Nếu `command_id` là AUTO_INCREMENT thì id mới trùng id máy đã ghi → máy trả kết quả cũ, server báo thành công nhưng không có gì xảy ra. `menu_version` lùi, `secret_enc` cũ quay lại. | `command_id` là 16 byte CSPRNG. Máy so fingerprint; trùng id mà khác nội dung là conflict. `server_epoch` ngẫu nhiên đổi mỗi lần restore, menu so theo (epoch, version). Viết checklist restore. | Đ thiet_ke:1187–1189, 1548, 1660; review-r1:93 |
| B4 | Cao | B | Server ghi delivered trước khi biết máy đã nhận, và lệnh delivered không được giao lại. Sau 30 s lệnh thành expired, gộp chung hai ca khác nhau: "máy chưa nhận" và "máy đã chạy nhưng mất kết quả". Người dùng bấm lại → `command_id` mới → `add_gram` chạy hai lần. | Trạng thái queued → offered → done / failed / unknown. Giao lại cùng id tới khi hết hạn. Agent giữ outbox kết quả tới khi nhận ack có ký. UI hiện "chưa rõ" kèm nút kiểm theo id. | Đ thiet_ke:770, 777, 1204; phuong_an:28 |
| B5 | TB | B | Agent hiểu 401 là "secret đã đổi" nên ngừng đồng bộ. Trên HTTP, một gói 401 giả là đủ làm máy mất đồng bộ lâu dài. | Lỗi không có chữ ký chỉ là lỗi vận chuyển: lùi rồi thử lại. Chỉ dừng khi nhận phản hồi đã ký báo "revoked". | Đ thiet_ke:850–852; design.md:243–244, 270–272 |
| B6 | TB | B | Chuỗi ký thiếu query (`wait`, `since`), status, version, `server_id`, và nối trường bằng "\|". MITM đổi `wait=0` → quay vòng liên tục; đổi status 200↔500. | Dùng tuple LP gồm version, `server_id`, `machine_id`, gen, method, path+query thô, ts, nonce, `sha256(body)`. Server giới hạn giá trị `wait`. | Đ thiet_ke:826, 1500–1502 |
| B7 | TB | B | `agent.env` để root 600, nhưng agent phải chạy cùng user kiosk để gọi xrandr. Secret nằm trong env tiến trình; Chromium hoặc store_gui chạy cùng user đọc được qua `/proc/<pid>/environ`. | Tách daemon mạng (user riêng, giữ secret) với helper hiển thị chạy cùng user kiosk; hai bên nói qua socket cục bộ với tập lệnh cố định. | Đ thiet_ke:656, 670, 1455, 1580, 1673 |
| B8 | TB | B | Secret 64 hex đi qua tay người, dễ lọt vào chat. Clone thẻ SD chép luôn `agent_state` → hai máy trùng `machine_id`, secret, `install_uuid`; trùng cả `QRPROTO_KEY` nên nhãn dùng chéo được giữa hai máy. | Mã ghép một lần, hoặc khoá do máy tự sinh rồi xác nhận vân tay. Báo động khi có hai long-poll đồng thời cho cùng `machine_id`. | Đ thiet_ke:657, 698–700, 723; qrproto_config.py:12–19 |
| B9 | TB | B | `POST …/result` và bước upsert bản sao không kiểm lệnh đó thuộc máy đã ký. Một Pi bị chiếm có thể ghi kết quả cho lệnh của máy khác. | `machine_id` luôn lấy từ danh tính đã xác thực. Chỉ nhận kết quả khi lệnh thuộc đúng máy, đang ở trạng thái offered và fingerprint khớp. | Đ thiet_ke:1157–1158, 1361–1362 |
| B10 | TB | B | XSS xuyên máy: chuỗi do máy gửi lên (`agent_version`, lý do excluded, lỗi, note) hiển thị cho owner. Token Bearer nằm trong `sessionStorage`, và JS đang dùng `innerHTML` ở nhiều chỗ. Một Pi bị chiếm lấy được token owner → điều khiển mọi máy. | CSP `script-src 'self'`, mặc định dùng `textContent`, kiểm dữ liệu lúc ingest. | Đ admin-guard.js:16; tickets.js:55, 242–254 |
| B11 | TB | B | Số thread = số máy + 8, không giới hạn long-poll mỗi máy, login PBKDF2 không có rate-limit. Flood login hoặc secret bị lộ làm cạn thread → máy bị coi là offline → K2 bị từ chối. | Mỗi máy một long-poll (cái mới huỷ cái cũ). Rate-limit theo user+IP. Dành riêng thread cho agent. | Đ thiet_ke:794, 1674; auth.py:80 |
| B12 | TB | B+QR | admin_gui cho đổi vé `used→unused`. Qua server mẹ, đây thành lệnh từ xa trên nhiều máy, lại không có nhật ký. Lộ token → mở lại vé đã dùng → pha thêm ly. | Khu vực quyền riêng, bắt xác thực lại, có nhật ký tối thiểu cho thao tác dính tới tiền. | Đ admin_gui/serve.py:2786–2795; thiet_ke:1358, 1653 |
| B13 | TB | B | Agent tải media xong mới so sha256. MITM gửi thân vô hạn làm đầy thẻ SD → MySQL lỗi → ngừng bán. | Giới hạn theo kích thước ghi trong snapshot đã ký và theo Content-Length; thư mục tạm có quota. | Đ thiet_ke:1073, 1100 |
| B14 | Thấp | B | M4 tra nonce trước khi kiểm HMAC; bước "ghi nonce" không phải INSERT UNIQUE nguyên tử; không nêu dùng `compare_digest`; mỗi bước trả lỗi khác nhau. Thu hồi phiên so DATETIME naive với `time.time()`, lệch múi giờ sẽ làm thu hồi lệch hàng giờ. | `compare_digest` trước, rồi INSERT nonce làm claim. 401 thân đồng nhất. Mốc thu hồi lưu dạng epoch nguyên. | Đ thiet_ke:804–815; auth.py:717 |
| A1 | Cao | A/ghép | Khoá và nonce của phản hồi suy tất định từ Export. Bất kỳ lỗi Seal hai lần nào (nhánh lỗi, retry nội bộ, crash, khôi phục snapshot VM) đều lặp cặp (key, nonce) của GCM → lộ XOR hai plaintext và khoá GHASH → giả được phản hồi poll chứa lệnh. Vì vậy R5 buộc phải CAS bền trước mọi phản hồi, kể cả đọc. | Trộn một `response_nonce` ngẫu nhiên vào HKDF như RFC 9458 §4.4 (F04). Single-outcome chỉ cần giữ trong ledger cho mutation. | Đ design.md:246–265, 276–278; FINDINGS F04 |
| A2 | TB | A | Verify ECDSA đứng trước các phép kiểm rẻ (freshness, epoch, tra claim). Phát lại một gói hợp lệ buộc server verify + decap mỗi lần. | Chạy các phép kiểm chỉ-để-từ-chối trước: kích thước, version, kid còn active, route, cửa sổ giờ, epoch, tra read-only claim; sau đó mới verify. | Đ design.md:321–322, 471 |
| A3 | Thấp | A | Hai file HTML vẫn ghi "suite chưa chốt", trong khi design §0 đã chốt P-256 + AES-128-GCM. `info` chứa nguyên M, trùng với AAD và chữ ký. | Đồng bộ tài liệu. `info` = nhãn + audience. | Đ packet-security.html:47, 81, 97, 105; crypto-primer.html:8, 129, 138; design.md:18–20, 200 |
| G1 | TB | ghép | Waitress không làm TLS, phải thêm proxy, trái với D5-A (TLS terminator khác server bị coi là A1). `last_seen_ip` thành IP proxy; timeout của proxy cắt long-poll; proxy có thể tự retry GET poll. | Dùng WSGI server có TLS, hoặc proxy loopback với cấu hình cố định. Poll bằng POST. Timeout proxy phải lớn hơn `wait`. | Đ design.md:25, 46–50; thiet_ke:1597 |
| G2 | Cao | ghép | Áp D2-C (so giờ OS với giờ server ký, lệch thì khoá Seal) vào LAN không có internet, giờ trôi, chỉnh được bằng tay. Lệch vượt ngưỡng → mọi thiết bị dùng giờ nhà mạng bị khoá. Hạn manifest và cert cũng phụ thuộc giờ. | Không dùng giờ tuyệt đối để ra quyết định bảo mật trong LAN; freshness lấy từ nonce/challenge. Cert để hạn dài và pin. | Đ design.md:284–290, 299–318; thiet_ke:752, 1670 |
| G3 | TB | ghép | Phần độ bền của R5 viết cho SQLite FULL, còn server mẹ dùng MySQL InnoDB ở cả hai đầu. | `innodb_flush_log_at_trx_commit=1`, `sync_binlog`, thử mất điện trên thẻ SD. | Đ design.md:572–577; F01; thiet_ke:318, 635 |
| G4 | TB | ghép | R5 đẩy mọi lệnh mất phản hồi sang unknown, và cần recovery phê duyệt mới giao lại. Wi-Fi chập chờn → đối soát tay liên tục. | Máy đã claim bền theo `command_id` + fingerprint trước executor, nên tự giao lại cùng id trong hạn và cùng epoch là an toàn. Chỉ chuyển unknown khi hết hạn, đổi epoch, hoặc mất ledger máy. | Đ design.md:370–386, 446–452 |

## 2. Nên giữ khi ghép

### Từ R5

- **Suite:** mỗi key record cố định một suite, không thương lượng, từ chối version cũ.
- **Định dạng:** tuple LP + nhãn miền; ký trên byte thô; từ chối khoá trùng và NaN.
- **Gắn phản hồi:** phản hồi gắn với attempt. Lệnh chỉ nhận trong lượt poll còn sống, hạn tính bằng CLOCK_BOOTTIME.
- **Status:** status và lỗi chưa xác thực chỉ là gợi ý về vận chuyển.
- **Lệnh:**
  - ID 128-bit, có fingerprint, claim bền trước executor, có trạng thái unknown, không hứa exactly-once.
  - Chỉ dispatch khi còn đủ hạn cộng margin.
- **Thứ tự kiểm:** quyền và thu hồi kiểm cùng transaction với claim. Chỉ claim nonce sau khi xác thực, không đuổi nonce còn sống, giới hạn ingress trước khi parse.
- **Token:** không dùng token làm khoá.

### Từ thiết kế server mẹ

- Menu là snapshot + sha256; media định danh theo nội dung.
- Máy luôn là bên mở kết nối.
- Máy offline thì trả 409 ngay.
- Ghi `command_id` trước khi in.
- Server không giữ payload vé hay `QRPROTO_KEY`.
- Upload được kiểm magic byte.

## 3. Phần R5 quá nặng cho LAN + Pi + trình duyệt

- **HPKE + chữ ký ngoài:** lớp E chỉ có giá trị khi tồn tại A1, tức một bên khác server kết thúc TLS (review-r1:59, design §1:46–50). Trong LAN dùng TLS trực tiếp có pin thì không có A1.
  - Phương án gọn: AEAD với khoá tách chiều, dẫn từ secret, nonce ngẫu nhiên 96-bit, đổi generation khoá trước giới hạn SP 800-38D. Thư viện `cryptography` đã có sẵn trên máy.
  - Cả hai phương án đều không có forward secrecy; TLS 1.3 thì có.
- **Seal-một-lần bằng CAS bền cho mọi phản hồi:** thay bằng `response_nonce` ngẫu nhiên; chỉ mutation cần ledger.
- **Manifest + root air-gapped:** thay bằng pin SPKI (khoá hiện tại + khoá kế tiếp) lúc cài máy.
- **`recovery_epoch` ngoài rollback domain, witness, hash-chain, audit challenge:** thay bằng `server_epoch` do script restore sinh lại; khi epoch đổi, máy gửi tóm tắt ledger.
- **CLOCK_UNTRUSTED, NTS, kênh giờ có ký:** thay bằng freshness theo nonce.
- **Operation ticket:** trình duyệt và server cùng miền tin cậy. Server tự sinh `command_id`, chống bấm đúp bằng idempotency key của form với UNIQUE(user, key).
- **Keystore TEE:** không áp được cho trình duyệt. Thay bằng phiên ngắn, CSP, xác thực lại cho thao tác nhạy cảm.
- **Restore thủ công nhiều bước:** nhân viên sẽ bỏ qua, phải tự động hoá bằng script.

## 4. Đề xuất giao thức FM-1 cho server mẹ

1. **Vận chuyển:** TLS 1.3, CA nội bộ (cân nhắc nameConstraints) hoặc cert tự ký. Agent pin SPKI (hiện tại + kế tiếp). Cert để hạn dài.
2. **Khoá:**
   - `k_req = HKDF(secret, salt = machine_id‖gen, info = "FM1 m2s")`; `k_resp` dẫn tương tự với nhãn `"s2m"`.
   - Tuỳ chọn: cặp khoá Ed25519 do máy tự sinh, để lộ DB server cũng không giả được máy.
3. **Request:**
   - Header: `X-FM-V`, `X-FM-Machine`, `X-FM-Gen`, `X-FM-Ts`, `X-FM-Nonce` (16 byte), `X-FM-Sig`.
   - `Sig = HMAC(k_req, LP("FM1-REQ", server_id, machine_id, gen, method, path+query thô, ts, nonce, SHA256(body)))`.
4. **Thứ tự kiểm ở server:**
   1. Framing và kích thước.
   2. Version, máy active, đúng gen.
   3. |ts − now| ≤ W, chỉ dùng để từ chối.
   4. HMAC bằng `compare_digest`.
   5. INSERT nonce UNIQUE làm claim, cùng transaction với side effect nếu được.
   6. Phân quyền theo route; `machine_id` lấy từ danh tính đã xác thực.
   7. Chạy handler.
   - Mọi lỗi trả 401 với thân đồng nhất.
5. **Phản hồi:** `HMAC(k_resp, LP("FM1-RESP", server_id, machine_id, gen, req_nonce, status, server_epoch, SHA256(body)))`. Agent chỉ nhận khi `req_nonce` khớp request đang chờ.
6. **Lệnh:**
   - Trường bắt buộc: `command_id` 16 byte, kind, args, fingerprint, `ttl_rel`.
   - Server chỉ dispatch khi hạn còn lớn hơn ttl + margin.
   - Máy chỉ chạy khi thời gian BOOTTIME kể từ lúc gửi poll còn dưới ttl, và claim ledger trước executor.
   - Outbox kết quả; giao lại cùng id; hết hạn thì chuyển unknown.
7. **Restore:** script sinh lại `server_epoch`, menu so theo (epoch, version), không bao giờ dùng lại id.
8. **Trình duyệt:** HTTPS; token gắn `user_id`, mốc thu hồi dạng epoch nguyên; rate-limit login; CSP; escape dữ liệu từ máy; xác thực lại khi đổi secret, đổi quyền, hoặc chuyển vé `used→unused`.
9. **Enroll và xoay khoá:** mã ghép một lần đi qua TLS đã pin; rotation bảo trì online hai pha; rotation khi nghi lộ làm thủ công.

## 5. Câu hỏi mở

1. Máy đang bind Tailscale, trong khi tài liệu nói LAN không có internet. Thực tế có internet không?
2. Có proxy hay middlebox nào kết thúc TLS không? Câu trả lời quyết định lớp mã hoá bên trong có cần hay không.
3. Server có RTC không? Ai restore DB, theo quy trình nào?
4. Điện thoại quản lý có cài được CA nội bộ không?
5. Mất Pi hoặc thẻ SD về mặt vật lý có phải rủi ro chấp nhận được không?
6. App Android theo R5 có cùng nói chuyện với server mẹ không? Nếu có, cần hai profile.
7. Có cho phép chuyển vé `used→unused` từ xa không?
8. Witness sentinel rỗng sau khi đổi epoch có được phép ở request đầu tiên không (design:193, 588–590)?
