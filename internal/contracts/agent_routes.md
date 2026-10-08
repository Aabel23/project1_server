# C0.4 · Body route agent

**Đề xuất để review, chưa duyệt.** Codex tiếp quản phần Claude ngày 08/10/2026
theo chỉ đạo user. Nguồn: thiết kế mục 7, M1/M3/N5/D1/D2/K3/L0 và C0.3.
Tên, method, mode và trần byte lấy duy nhất từ `server/config/routing.py`.
Những giới hạn/field bổ sung dưới đây là đề xuất C0, không coi là user đã chốt.

## Quy ước chung

- Body là JSON UTF-8 object, không key trùng, không NaN/Infinity; reject field
  ngoài schema. Không nhận `machine_id` trong body: handler dùng id từ credential.
- `hex32`: 16 byte dưới dạng 32 ký tự hex thường; `hex64`: 32 byte / 64 ký tự.
  Epoch và command_id dùng hex32, sha256/fingerprint/payload_hash dùng hex64.
- Số id/version/serial/error_id là integer (không bool), không âm; id > 0.
  Version 0 biểu thị chưa có menu, không phải snapshot có thể áp.
- Tiền/gram dạng chuỗi decimal cố định hai chữ số lẻ, không scientific notation;
  miền `0.00..99999999.99`. Mốc thời gian dạng Unix milliseconds integer >= 0;
  chuyển timezone DB máy tại A-UP, không diễn giải giờ máy là giờ host server.
- Chuỗi dữ liệu không chứa NUL, giới hạn theo số ký tự (trần body theo byte).
  UI luôn hiện bằng textContent. Không thực thi HTML, đường dẫn hay SQL từ body.
- Status đã xác thực nằm trong response seal C0.3: `ok`, `bad_request`,
  `not_found`, `conflict`, `epoch_changed`, `error`, `revoked`. HTTP 4xx trước
  claim chỉ là lỗi vận chuyển; không được dùng để kết luận máy đã thu hồi.
- `attempt_id`, `resp_key`, `server_epoch_seen` thuộc FM1, không lặp trong body.
  Response inner luôn có epoch; body epoch chỉ xuất hiện nơi bảng thiết kế yêu cầu.

## Từng route

| Route / khối ghi, khối đọc | Request | Response khi `ok` | Trần request / response |
|---|---|---|---|
| `AGENT_TRUST_PATH` / A-NET → M-KEY | `{code_id}`; ASCII base32 16–32 ký tự (>=80 bit); chưa FM1 | `{ca_pem, server_keys, audience, server_epoch, hmac}`; ca_pem <=8 KiB; server_keys <=2 mục `{kid,alg,pubkey}`; X25519 pubkey base64 chuẩn 32 byte; hmac hex64 | 1 / 16 KiB |
| `AGENT_ENROLL_PATH` / A-NET → M-KEY | `{pubkey,install_uuid,proof}`; Ed25519 pubkey base64 chuẩn 32 byte, install_uuid UUID chuẩn thường, proof hex64; code/machine lấy từ enrollment context | `{kid,generation}`; kid theo C0.3, generation >0 | 4 / 4 KiB |
| `AGENT_HELLO_PATH` / A-NET → M-MAC | `{agent_version,applied,results}`; agent_version <=64; applied = null hoặc `{epoch,version,sha256}`; results <=200 mục theo C0.6 | `{target_menu_version,server_epoch,server_time}`; target_menu_version null hoặc `{server_epoch,version,sha256}`; server_time milliseconds chẩn đoán | 256 / 4 KiB |
| `AGENT_COMMANDS_PATH` / A-NET → M-MAC | `{wait}` integer 0..25 giây | `{commands,target_menu_version}`; commands <=100 theo C0.6; target như hello, null khi chưa gán menu | 1 / 64 KiB |
| `AGENT_RESULTS_PATH` / A-RUN → M-CMD | `{results}` <=200 mục C0.6 | `{accepted}` danh sách command_id đã lưu bền; chỉ ACK mục đúng máy/fingerprint và state cho phép | 256 / 16 KiB |
| `AGENT_MENU_PATH` / A-APPLY → M-PUB | `{since}` version >=0; epoch_seen ở M nên since chỉ so trong cùng epoch | `{server_epoch,version,sha256,snapshot,media}` theo C0.5; khi không đổi snapshot=null, media=[] và tuple target vẫn trả | 1 KiB / 2 MiB |
| `AGENT_MENU_ACK_PATH` / A-APPLY → M-PUB | `{server_epoch,version,sha256,ok,excluded}`; ok bool; excluded <=999 mục `{sku,reason,ingredient_id}`; reason enum dưới | `{received:true}` sau commit | 64 / 1 KiB |
| `AGENT_ORDERS_PATH` / A-UP → M-ING | `{tickets}` <=200 vé theo bảng dưới | `{received:N}`; N là số mục được nhận hợp lệ (kể cả upsert trùng), ACK cả batch sau transaction | 256 / 1 KiB |
| `AGENT_ERRORS_PATH` / A-UP → M-ING | `{install_uuid,errors}`; UUID chuẩn; <=200 lỗi theo bảng dưới | `{received:N}` cùng ngữ nghĩa orders | 256 / 1 KiB |
| `AGENT_STOCK_PATH` / A-STOCK → M-ING | `{stock,out_of_stock}`; stock <=24 mục, out_of_stock <=999 mục | `{received:true}` sau commit; reported_at do server tự ghi | 16 / 1 KiB |
| `AGENT_MEDIA_PATH` / M-CAT → A-APPLY | GET hash trong URL đúng hex64; không body, không FM1 | Bytes đúng sha256; dừng tải ngay vượt size đã xác thực trong snapshot, đủ byte phải đúng size và hash | 0 / 10 MiB |

Giới hạn response FM1 là JSON body đã giải mã; envelope có overhead C0.3.
Nếu batch hợp lệ theo số dòng nhưng quá trần byte, agent chia batch nhỏ hơn.
Trần stock 16 KiB cũng áp dụng out_of_stock; danh sách lớn phải chia hoặc nâng
hợp đồng sau review, không gửi response vượt trần. Hello có results chưa ACK
phục vụ L0 bình thường; **ledger N giờ sau restore vẫn chưa chốt route Q10**,
không tự thêm trường ledger_replay hay coi hello đã được duyệt cho M6.

## Schema dữ liệu máy

| Dữ liệu | Trường |
|---|---|
| Ticket | `payload_hash` hex64, `serial` 1..999999, `drink_id` 1001..1999; `drink_name` null hoặc <=100; `price` null hoặc decimal; `note` null hoặc <=200; `status` = unused/in_progress/used/expired/noqr_err; `created_at`, `updated_at` milliseconds; `scanned_at`, `completed_at` null hoặc milliseconds |
| Error | `error_id` >0, `created_at` milliseconds, `severity` info/warning/error; `drink_id` null hoặc SKU; `drink_name` null hoặc <=100; `step_label`, `step_type` null hoặc <=16; `message` <=2048 ký tự (đề xuất để batch có trần) |
| Stock | `ingredient_id` 1..24, `ingredient_name` 1..100; `type` PUMP/MANUAL; `data_type` boolean/percentage/weight; `amount`, `threshold_gram` decimal >=0; `max_gram` null hoặc decimal >0; `in_stock` bool |
| Out-of-stock / excluded | `sku` 1001..1999, `ingredient_id` 1..24; reason missing_ingredient/below_threshold/ingredient_mismatch. below_threshold dùng báo tồn; mismatch/missing dùng áp menu |

**Cấm `payload` QR**, kể cả khi đi cùng payload_hash. Upsert vé theo
`(machine_id,payload_hash)`, chỉ ghi khi updated_at >= bản cũ; lỗi theo
`(machine_id,install_uuid,error_id)`. Agent chỉ tiến con trỏ sau response
`ok` mở được và ACK đủ batch; gửi lại không làm tăng số bản ghi.

## Nhánh lỗi và ví dụ

- `bad_request`: field sai/thừa, id ngoài miền, batch vượt số dòng, payload QR.
  Không ghi một phần batch; vượt byte trước claim trả HTTP 413 C0.3.
- `not_found`: version/hash không có hoặc không thuộc menu được gán.
  Media ngoài FM1 trả HTTP 404, hash không đúng ngữ pháp trả 400.
- `conflict`: ACK tuple không khớp snapshot đã phát, kết quả lệnh sai fingerprint.
  Kết quả máy khác không ACK và không sửa bảng.
- `epoch_changed`: xử lý qua S-FM1 trước nghiệp vụ, không áp/menu ACK đời cũ.
- Trust/enroll thất bại dùng lỗi cố định C0.3; không log code/proof/key. HMAC/KDF,
  binding code_id vào enroll và các nhãn cụ thể còn đề xuất ở C0.3/M-KEY.
  M hiện tại với credential_kid=enroll chưa tự xác định code/machine cụ thể:
  reviewer M-KEY phải chốt handle/context ràng buộc cho server chọn mã ghép,
  không giả định POST trust và POST enroll dùng cùng connection/session.

Hợp lệ: `POST AGENT_COMMANDS_PATH` body `{"wait":25}`; results rỗng trả
`{"accepted":[]}`; stock rỗng để báo chưa có nguyên liệu.
Từ chối: `{"wait":26}`, `{"wait":true}`, `{"wait":10,"machine_id":2}`;
tickets có `payload`, 201 vé, fingerprint 63 ký tự, ACK khác epoch.
