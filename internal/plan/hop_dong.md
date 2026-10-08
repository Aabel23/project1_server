# Tầng 0 · Cổng mật mã và hợp đồng

- **Trạng thái:** CHƯA THỰC HIỆN.
- **Chưa xong tầng 0 thì không khối nào bắt đầu code.** Khối chỉ dựa vào hợp đồng đã được reviewer duyệt.

Hợp đồng nằm ở `server/internal/contracts/`. Mỗi file ghi:

- tên hằng, trường, kiểu, giới hạn;
- nhánh lỗi;
- khối nào ghi, khối nào đọc;
- ví dụ hợp lệ và ví dụ phải bị từ chối.

## G0 · Cổng mật mã

**Cổng chặn:** không đạt thì dừng và hỏi user. Không tự đổi thư viện, không tự ghép primitive khác (`crypto_tranh_luan.md:339-346`).

| ID | Việc | Đạt khi |
|---|---|---|
| G0.1 | Chạy vector RFC 9180 đầy đủ trên PyHPKE, suite X25519 / HKDF-SHA256 / AES-128-GCM, mode Base | Mọi vector của suite khớp |
| G0.2 | Liên thông byte-exact: seal bằng `cryptography`, open bằng PyHPKE và ngược lại. `info = Tuple("fm1-req", SHA256(M))`, aad rỗng | 1.000 lần mỗi chiều khớp từng byte |
| G0.3 | Test âm: đổi 1 bit trong M, `enc`, `ct`; cắt cụt `ct`; đổi nhãn | Mọi ca mở thất bại, không ném lỗi lạ |
| G0.4 | Ghi lại upstream `cryptography` có chạy vector HPKE trong CI không | Có link nguồn |
| G0.5 | Ed25519 trên `Tuple("fm1-sig", M, enc, ct)`; AES-128-GCM response, nonce ngẫu nhiên, AAD `Tuple("fm1-resp", SHA256(M))` | Đổi 1 byte là verify sai; 10.000 lần seal không lặp nonce |
| G0.6 | Benchmark trên Pi thật: một vòng agent (sinh khoá, seal, ký, mở) và một vòng server (verify, open, seal), 1.000 vòng | Có p50, p95, max, CPU; ghi model Pi, OS, phiên bản Python và `cryptography` |
| G0.7 | Long-poll qua TLS 1.3 của cheroot: hai cổng, hai pool, treo 25 s, đánh thức bằng `threading.Condition`; flood cổng quản trị trong lúc treo N poll | Không poll nào bị cắt; N = số máy (Q9) + 8, chưa có Q9 thì đo với 10 và ghi là giả định |

- **File:** `server/spike/` (không trộn với code chạy thật).
- **Báo cáo:** `server/internal/plan/bang_chung/G0.md`.
- **Phương án lùi** đã xét trong thiết kế: PyHPKE + Export + nonce ngẫu nhiên. Chỉ dùng khi user chọn.

## C0 · Hợp đồng chung

| ID | Hợp đồng | File | Nội dung chính | Chờ user |
|---|---|---|---|---|
| C0.1 | Khởi tạo repo | `server/.git`, `.gitignore`, `README.md` | `git init`; bỏ bản trùng `server/routing.py`, chỉ giữ `server/server/config/routing.py` | Q8 |
| C0.2 | Routing bản 2 và `ROUTE_POLICY` | `server/server/config/routing.py` | Theo mục 7 "Cần sửa routing.py": đổi POST, đổi `AGENT_RESULTS_PATH`, media theo sha256, bỏ heartbeat và token rotate, thêm route ghép, thu hồi, lệnh, màn hình, xác thực lại, giờ, CA. Thêm `INGREDIENT_REGISTRY_PATH`, `MENU_BULK_PATH` (thiết kế ghi "cần thêm"). `ROUTE_POLICY`: mỗi route agent một chế độ `trust` / `enroll` / `fm1` / `tls_only` | |
| C0.3 | Gói FM1 | `contracts/fm1_wire.md`, `tests/vectors/fm1/*.json` | Trường M theo mục 4.2; LP, Tuple, sáu nhãn; khung request và response; thân lỗi 4xx cố định; bộ vector dùng chung cho server và máy | Q1 |
| C0.4 | Body route agent | `contracts/agent_routes.md` | Từng route ở bảng mục 7: trường máy gửi, trường server trả, giới hạn kích thước, mã trạng thái nghiệp vụ | |
| C0.5 | Snapshot menu | `contracts/menu_snapshot.md` | Trường, thứ tự sắp để sha256 ổn định, `media[]` (sha256, size), `server_epoch`, `version`, trần kích thước | |
| C0.6 | Loại lệnh | `contracts/commands.md` | Theo bảng loại lệnh ở mục 7: `kind`, `args`, cách chống chạy lặp, hạn; fingerprint `fm1-cmd`; bảy trạng thái L0 phía server và bốn trạng thái ledger phía máy | |
| C0.7 | Ngữ pháp helper | `contracts/helper.md` | `display apply\|keep\|revert\|status`, `order-mode set`, `menu publish`, `print <hex64>`; mã lỗi; định dạng output | |
| C0.8 | Chủ sở hữu bảng | `contracts/db_ownership.md` | Mỗi bảng server và máy do đúng một khối ghi. Khối khác chỉ đọc hoặc gọi hàm của khối chủ (nguyên tắc "một nơi ghi" ở mục 6 của thiết kế) | |
| C0.9 | Cấu hình và tham số | `server/server/config/settings.py`, file mẫu | Đọc cấu hình; thiếu khoá bắt buộc thì dừng; mặc định theo bảng ở `index.md` | |
| C0.10 | Hàm nối giữa các khối | `contracts/interfaces.md` | Chữ ký các hàm ở bảng "Mối nối" của `index.md`, kèm nhánh lỗi | |
| C0.11 | Khung module cô lập | `server/server/contracts/*.py`, `server/server/wiring.py`, `tests/c0/test_isolation.py` | `Protocol` cho từng mối nối; `wiring.py` khung rỗng ghi thứ tự nối; test quét import để không module nào import module khác. Nguyên tắc ở mục "Module cô lập" của `index.md` | |

**Kiểm tầng 0:**

- Reviewer duyệt từng file hợp đồng.
- Test tự động cho C0.2: mọi hằng `_PATH` khác nhau, bắt đầu bằng `/api/`; mọi hằng `AGENT_*` có trong `ROUTE_POLICY`.
- Vector C0.3 chạy được bằng code spike của G0.

**Đổi hợp đồng sau khi đã duyệt:** ghi lý do vào file hợp đồng, liệt kê khối bị ảnh hưởng, đưa các khối đó về → cho tới khi test lại đạt.

### Bảng chủ sở hữu (bản nháp cho C0.8)

| Bảng (server) | Khối ghi |
|---|---|
| `schema_migration` | S-DB |
| `admin_user`, `role_permission`, `user_machine` | M-ACC |
| `machine` | M-MAC |
| `server_key`, `machine_credential`, `enrollment_code` | M-KEY |
| `packet_claim` | S-FM1 |
| `glass`, `drink_type`, `category`, `drink`, `recipe`, `recipe_action`, `media_file`, `ingredient_registry` | M-CAT |
| `menu`, `menu_item`, `menu_item_category`, `menu_setting`, `menu_version` | M-MENU |
| `machine_menu_apply` | M-PUB |
| `sale`, `fault`, `machine_ingredient_cache` | M-ING |
| `machine_command` | M-CMD |
| `server_state` | S-EPOCH |

| Bảng (máy) | Khối ghi |
|---|---|
| `agent_ledger` | A-RUN |
| `agent_state`: phần kid, epoch | A-NET |
| `agent_state`: phần applied | A-APPLY |
| `agent_state`: phần con trỏ | A-UP |
| `agent_state`: phần hash tồn kho | A-STOCK |
| Bảng menu, món, công thức trên máy | A-APPLY |
| `ingredient`, `order_ticket`, `error_log` (do lệnh) | A-RUN |

`agent_state` có nhiều khối ghi, mỗi khối một nhóm cột riêng. Reviewer C0.8 quyết định giữ một bảng hay tách thành các bảng nhỏ. Nếu tách thì cập nhật A-DB.
