# C0.3 · Định dạng gói FM1

> **Bản nháp, chờ user chốt Q1 (các chỗ lệch R5).** Các lệch R5 liên quan trực tiếp tới file này:
> - `cryptography` + `resp_key` thay PyHPKE + Export;
> - Ed25519 thay P-256;
> - media đi ngoài FM1;
> - seal thông báo thu hồi có giới hạn.
>
> Q1 đổi thì file này đổi theo.

- **Nguồn:** thiết kế mục 4.2–4.5, M4; `agents/memory/crypto_tranh_luan.md` (thiết kế cuối).
- **Bản tham chiếu:** `spike/fm1_ref.py`. Đã qua G0.1–G0.5 (`internal/plan/bang_chung/G0.md`).
- **Bộ vector:** `tests/vectors/fm1/*.json`, sinh bằng `spike/gen_fm1_vectors.py`, kiểm bằng `tests/c0/test_fm1_vectors.py`.

## Ai ghi, ai đọc

| Khối | Vai |
|---|---|
| S-FM1 | Giữ bản gốc `fm1_encoding.py` (LP, Tuple, M) và `fm1_crypto.py`. Mở request, seal response |
| A-NET | Chép `fm1_encoding.py` từ S-FM1 kèm commit nguồn; test so sha256 hai bản. Seal request, mở response |
| M-KEY | Dùng `fm1-bundle`, `fm1-proof` (M1); cấp `kid` |
| M-CMD, A-RUN | Dùng `fm1-cmd` cho fingerprint lệnh (C0.6) |

Module nghiệp vụ không đọc gói FM1. Module chỉ nhận `(machine_id, body)` (xem `interfaces.md`).

## 1. Khối dựng

### LP

`LP(x) = uint32 big-endian của len(x) ‖ x`.

- Đọc LP phải kiểm: còn đủ 4 byte; độ dài không vượt trần của trường; còn đủ byte.
- Đọc xong mọi trường mà còn byte thừa thì từ chối.

### Tuple

`Tuple(nhãn, f1, …, fn) = LP(nhãn) ‖ LP(f1) ‖ … ‖ LP(fn)`.

- Mỗi nhãn có số trường cố định, nên ghép là đơn ánh.
- **Chưa chốt:** có thêm số trường vào Tuple hay không. Đề xuất không thêm, vì số trường của mỗi nhãn đã cố định.

### Sáu nhãn

Mọi nhãn là ASCII, không có byte kết thúc.

| Nhãn | Dùng ở | Trường |
|---|---|---|
| `fm1-req` | `info` của HPKE | `SHA256(M)`. Tổng 47 byte, dưới trần 64 |
| `fm1-sig` | Chuỗi được ký Ed25519 | `M, enc, ct` |
| `fm1-resp` | AAD của response | `SHA256(M)` |
| `fm1-cmd` | Fingerprint lệnh: `SHA256(Tuple("fm1-cmd", machine_id, kind, args_bytes))` | Xem C0.6 |
| `fm1-bundle` | HMAC của trust bundle (M1) | **Chưa chốt**, việc của M-KEY. Đề xuất: `HMAC-SHA256(k_bundle, Tuple("fm1-bundle", bundle_json_bytes))` |
| `fm1-proof` | Proof khi enroll (M1) | `HMAC(khoá dẫn từ mã, Tuple("fm1-proof", pubkey, machine_id, install_uuid))`. Thiết kế ghi `Tuple(pubkey, machine_id, install_uuid)` không nhãn; đề xuất thêm nhãn `fm1-proof` cho đúng bảng nhãn. **Chưa chốt** |

## 2. M: phần rõ, được ký

M là 11 trường LP nối nhau, đúng thứ tự dưới. Đổi thứ tự hay thêm trường thì phải tăng `version`.

| # | Trường | Kiểu khi mã hoá | Giới hạn | Ghi chú |
|---|---|---|---|---|
| 1 | `domain` | ASCII | đúng `flexmix-fm1` | Hằng; không phải một trong sáu nhãn |
| 2 | `version` | uint16 BE | đúng 1 | |
| 3 | `suite` | ASCII | đúng `X25519-HKDF-SHA256-AES-128-GCM/Ed25519` | Chống hạ cấp |
| 4 | `audience` | ASCII `[a-z0-9][a-z0-9._-]{0,63}` | 1–64 byte | Mã của server mẹ này, lấy từ cấu hình (C0.9 `fm1.audience`) |
| 5 | `server_kid` | ASCII `[a-z0-9]{1,32}` | 1–32 | Kid khoá KEM server mà máy nhắm tới |
| 6 | `credential_kid` | ASCII `[a-z0-9]{1,32}` | 1–32 | Kid của máy, hoặc đúng `enroll` |
| 7 | `method` | ASCII | đúng `POST` | Route FM1 luôn POST |
| 8 | `route_id` | ASCII `AGENT_[A-Z0-9_]+_PATH` | ≤ 64 | Tên hằng trong `routing.py`; phải là khoá của `ROUTE_POLICY` |
| 9 | `attempt_id` | byte | đúng 16 | Ngẫu nhiên mỗi lần gửi |
| 10 | `issued_at` | uint64 BE, mili giây Unix | 8 byte | Giờ máy, đã đồng bộ về server |
| 11 | `server_epoch_seen` | byte | 0 hoặc 16 | Rỗng khi máy chưa biết epoch (enroll) |

- **Trần |M|:** 512 byte. M thực tế khoảng 230–260 byte.
- **Chưa chốt, kèm đề xuất:**
  - Định dạng `kid`: 16 ký tự hex thường, lấy từ `SHA256(pubkey)[:8]`.
  - Đơn vị `issued_at`: mili giây. Thiết kế không ghi đơn vị; W vẫn tính bằng giây trong cấu hình.

## 3. Request

```
request = ver ‖ LP(M) ‖ LP(enc) ‖ LP(ct) ‖ LP(sig)
ver     = 0x00 0x01
enc, ct = HPKE Base single-shot X25519 / HKDF-SHA256 / AES-128-GCM
          tới khoá KEM server, info = Tuple("fm1-req", SHA256(M)), aad rỗng
pt      = LP(resp_key) ‖ LP(body)        (resp_key 16 byte; body là JSON UTF-8)
sig     = Ed25519(khoá máy, Tuple("fm1-sig", M, enc, ct))
```

| Phần | Byte | Giới hạn |
|---|---|---|
| `ver` | 2 | đúng `0x0001` |
| `LP(M)` | 4 + \|M\| | \|M\| ≤ 512 |
| `LP(enc)` | 4 + 32 | đúng 32 |
| `LP(ct)` | 4 + 4 + 16 + 4 + \|body\| + 16 | \|body\| ≤ `ROUTE_POLICY[route].max_request` |
| `LP(sig)` | 4 + 64 | đúng 64 |

- **Lệch nhỏ so với thiết kế:** bảng 4.2 ghi ct là `4 + 20 + |body| + 16`. Vì body cũng bọc LP, ct thật dài thêm 4 byte: `4 + 20 + 4 + |body| + 16`. Không đổi ý thiết kế, chỉ sửa phép đếm.
- Với `cryptography`: `Suite.encrypt` trả `enc ‖ ct`; tách 32 byte đầu là `enc`.
- **Body:**
  - JSON UTF-8, gốc là object;
  - không khoá trùng, không NaN hay Infinity;
  - không vượt `max_request` của route.
- **Không đọc từ body:** server không bao giờ lấy `machine_id` từ body (B9).

## 4. Response

```
response = ver ‖ LP(nonce) ‖ LP(ct)
nonce    = 12 byte ngẫu nhiên mỗi lần seal
ct       = AES-128-GCM(resp_key, nonce, inner, AAD = Tuple("fm1-resp", SHA256(M)))
inner    = JSON UTF-8 {"attempt_id", "status", "server_epoch", "body"}
```

| Trường của inner | Kiểu | Ghi chú |
|---|---|---|
| `attempt_id` | chuỗi hex thường, 32 ký tự | Phải bằng `attempt_id` của attempt đang chờ |
| `status` | chuỗi | Xem bảng dưới |
| `server_epoch` | chuỗi hex thường, 32 ký tự | Epoch hiện tại của server |
| `body` | object | Thân nghiệp vụ, theo C0.4 |

- Đúng bốn trường; thừa hay thiếu là từ chối.
- **Phía máy:**
  - chỉ mở bằng `resp_key` của attempt đang chờ;
  - kiểm `attempt_id`;
  - kiểm hạn bằng BOOTTIME;
  - mở xong thì xoá `resp_key`.
- **Phía server:** không log `resp_key`.
- Thứ tự khoá trong inner không bắt buộc. Server seal bằng JSON gọn, sắp khoá (`sort_keys`, `separators=(",", ":")`), để vector ra đúng byte.

### `status` (chưa chốt, đề xuất)

Thiết kế chỉ nói "status nghiệp vụ nằm trong bản mã" và có `revoked`.

| status | Nghĩa | Agent làm gì |
|---|---|---|
| `ok` | Handler chạy xong | Dùng `body` |
| `revoked` | Credential đã thu hồi; seal tối đa 1 lần mỗi phút mỗi kid | Dừng gửi, hiện "cần ghép lại" |
| `bad_request` | Body sai hợp đồng C0.4 | Ghi log, không gửi lại cùng body |
| `not_found` | Đối tượng không có, ví dụ `since` lạ | Theo C0.4 |
| `conflict` | Xung đột nghiệp vụ, ví dụ fingerprint lệnh khác | Theo C0.4 |
| `epoch_changed` | `server_epoch_seen` khác epoch hiện tại | Chạy luồng M6 |
| `error` | Lỗi phía server sau khi claim | Lùi rồi gửi attempt mới |

## 5. Lỗi trước khi xác thực: 4xx thân cố định

Mọi lỗi trước bước claim (mục 4.4) trả HTTP 4xx, **không mã hoá**, thân cố định `{"e": gợi ý}`. Agent coi mọi 4xx là lỗi vận chuyển: lùi 1, 2, 5, 10, 30 s, gửi attempt mới, không bao giờ dừng hẳn (B5).

Gợi ý chưa chốt. Đề xuất ít mã để không thành oracle:

| HTTP | Thân | Khi nào |
|---|---|---|
| 404 | `{"e":"route"}` | Đường dẫn hoặc method không có trong `ROUTE_POLICY` |
| 413 | `{"e":"size"}` | Vượt trần kích thước của route |
| 400 | `{"e":"frame"}` | Khung, M, audience, route_id lệch đường dẫn, JSON sai |
| 401 | `{"e":"time"}` | `issued_at` ngoài W hoặc dưới high-water − W. Giờ là phần rõ nên gợi ý không lộ gì |
| 401 | `{"e":"auth"}` | Kid lạ hoặc đã thu hồi (khi hết suất thông báo), chữ ký sai, HPKE không mở được, claim trùng, credential không active |

- Thân là chuỗi byte cố định, không chứa dữ liệu từ request.
- Lỗi sau khi claim: response seal với `status` như mục 4.

## 6. Thứ tự kiểm phía server và tên bước

Tên bước dùng trong vector (`stage`) và trong log nội bộ.

| # | Bước | `stage` | Tốn CPU |
|---|---|---|---|
| 1 | Đường dẫn, method, kích thước theo `ROUTE_POLICY` | `route`, `size` | không |
| 2 | Khung LP, `ver`, M đủ trường và đúng ngữ pháp | `frame` | không |
| 3 | `audience`, `server_kid` đúng server này | `audience` | không |
| 4 | `route_id` có trong `ROUTE_POLICY` và khớp đường dẫn; `enroll` chỉ ở route chế độ `enroll` | `route` | không |
| 5 | `|issued_at − giờ server| ≤ W`; `issued_at ≥ high-water(kid) − W` | `time` | không |
| 6 | Kid active (hoặc đã thu hồi mà còn suất thông báo); tra claim chỉ-đọc | `auth` | tra bảng |
| 7 | Verify Ed25519 | `sig` | có |
| 8 | HPKE open | `open` | có |
| 9 | Tách `resp_key`, parse JSON chặt | `frame` | ít |
| 10 | Một transaction: claim `(kid, attempt_id)`, kiểm credential active, so epoch, cập nhật high-water | `auth` | DB |
| 11 | Gọi handler với `machine_id` lấy từ credential | — | |
| 12 | Seal response | — | |

Bước 6 và 10 cần DB, nên không có trong vector. S-FM1 test hai bước này bằng stub M-KEY.

Phía máy khi mở response:

| Bước | `stage` |
|---|---|
| `ver`, khung LP, nonce 12 byte | `frame` |
| AES-GCM mở bằng `resp_key` với AAD của chính M đã gửi | `open` |
| JSON chặt, đúng bốn trường | `frame` |
| `attempt_id` khớp attempt đang chờ | `binding` |

## 7. Bộ vector

**Khoá trong vector là khoá test cố định**, dẫn từ `SHA256("fm1-vector/…")`. Không bao giờ dùng ngoài test.

- HPKE trong vector seal bằng PyHPKE với `ikm_e_hex` cố định để vector tất định. G0.2 đã chứng minh `cryptography` mở được đúng từng byte.
- Sinh lại: `.venv/Scripts/python spike/gen_fm1_vectors.py`. Test `spike/test_c0_3_vectors_repro.py` bảo đảm sinh lại ra đúng từng byte.

| Trường JSON | Nghĩa |
|---|---|
| `kind` | `request` hoặc `response` |
| `expect` | `accept` hoặc `reject` |
| `stage` | Bước phải từ chối (mục 6); `null` nếu nhận |
| `path` | Đường dẫn HTTP gói được gửi tới |
| `server_now_ms`, `window_ms` | Giờ server và W khi kiểm |
| `server_audience`, `server_kid` | Server đang kiểm là ai |
| `keys` | Khoá KEM server, khoá ký máy dùng để verify |
| `m_fields`, `m_hex`, `enc_hex`, `ct_hex`, `sig_hex`, `ikm_e_hex` | Các phần của request |
| `resp_key_hex`, `body_utf8`, `request_hex` | |
| `response` | Với vector `accept`: `nonce_hex`, `aad_hex`, `inner`, `response_hex` |
| `expected_attempt_id_hex`, `response_hex` | Với vector `response` |

### Ví dụ hợp lệ

| Vector | Nội dung |
|---|---|
| `ok_hello` | Hello của máy đã ghép; response `status: ok` |
| `ok_commands` | Long-poll `{"wait":25}`; response có một lệnh `ingredients.read` kèm fingerprint `fm1-cmd` |
| `ok_enroll` | `credential_kid = enroll`, ký bằng khoá mới, `server_epoch_seen` rỗng |
| `ok_revoked_notice` | Response `status: revoked` đã seal |

### Ví dụ phải bị từ chối

| Nhóm | Vector |
|---|---|
| `frame` | `rej_ver`, `rej_trailing_byte`, `rej_truncated`, `rej_lp_overflow`, `rej_route_id_lower`, `rej_method_get`, `rej_epoch_len`, `rej_resp_key_short`, `rej_inner_trailing`, `rej_json_dup_key`, `rej_json_nan`, `rej_json_array`, `rej_json_not_utf8` |
| `audience` | `rej_audience_other` |
| `route` | `rej_route_mismatch` (gói của route này đem dùng cho route khác), `rej_route_unknown` |
| `time` | `rej_time_old`, `rej_time_future` |
| `sig` | `rej_flip_m`, `rej_flip_enc`, `rej_flip_ct`, `rej_flip_sig`, `rej_sig_label`, `rej_wrong_signer` |
| `open` | `rej_info_other_m`: chữ ký đúng nhưng ct mã hoá với info của M khác |
| Response | `resp_rej_aad_other_m`, `resp_rej_other_key`, `resp_rej_flip_ct`, `resp_rej_flip_nonce` (`open`); `resp_rej_ver`, `resp_rej_extra_field`, `resp_rej_dup_key` (`frame`); `resp_rej_attempt` (`binding`) |

## 8. Còn chưa chốt

1. Q1: toàn bộ các lệch R5 ở đầu file.
2. Có thêm số trường vào Tuple không (đề xuất: không).
3. Giá trị `domain`, chuỗi `suite`, định dạng `kid`, đơn vị `issued_at`.
4. Danh sách `status` và gợi ý 4xx.
5. Nhãn trong `proof` và công thức HMAC bundle (thuộc M-KEY, nhưng dùng nhãn của file này).
6. Trần kích thước từng route: giá trị đề xuất nằm ở `ROUTE_POLICY` trong `routing.py`.
