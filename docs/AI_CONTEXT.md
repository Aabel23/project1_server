# FlexMix Fleet — AI Context

> **SUMMARY / INDEX, không thay thế source-of-truth.** Tổng hợp ngày 17/09/2026 từ 12 tài liệu cuối file. Đọc file này trước, rồi đọc phần spec liên quan trước khi triển khai; không cần đọc lại mọi tài liệu cho mỗi tác vụ.
>
> **Trạng thái hiện tại:** DEC-001 đến DEC-009 đều `DRAFT`, **chưa có `ACCEPTED`**. Theo sổ quyết định, DRAFT chưa là căn cứ triển khai. Q-01 đến Q-31 đều `OPEN` về phê duyệt, dù một số đã có câu trả lời. Phase 00 hiện chỉ có foundation Hub (app/config/MySQL development/ORM/Alembic/test), không có nghiệp vụ hay schema Hub; mã máy `version1.0 @ ce17f05` chưa có trong workspace để kiểm chứng.
>
> Tra cứu chuẩn: [06_decisions.md](06_decisions.md) cho DEC/trạng thái; [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) cho Q/phần còn thiếu; [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) cho C/ràng buộc, A/giả định, D/câu hỏi lịch sử; [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md) cho REQ/nghiệm thu. Không nâng ASSUMPTION hoặc khuyến nghị nguồn thành quyết định OWNER.

## 1. Project purpose

Quản lý đội máy pha đồ uống FlexMix bằng Hub: danh mục, tài khoản theo điểm bán, giám sát, backup, lệnh vận hành và rollout phần mềm. Mỗi máy vẫn bán/pha bằng dữ liệu tại chỗ; Hub không nằm trên đường bán. Phạm vi hiện tại không gồm cổng thanh toán, ghi nhận tiền mặt, vé liên máy, điều phối khách sang máy rảnh hoặc mở rộng QR. Thu tiền ngoài phần mềm khác với báo cáo vé (REQ-01, REQ-12, DEC-003/DEC-004 DRAFT).

## 2. Architecture overview

- **Hub:** quản lý trạng thái mong muốn, danh mục, tài khoản, quan sát đội máy, lệnh, release đã ký và metadata backup; có MySQL riêng.
- **Máy:** Raspberry Pi 5 / Ubuntu 24.04 / MySQL `beveragepos` theo nguồn; backend phục vụ kiosk/store `:8080`, `sync_menu`, `run_flow` và phần cứng. Mỗi máy pha một ly tại một thời điểm; vé hạn 24 giờ.
- **Agent:** `flexmix-agent.service` riêng với `flexmix-backend.service`; chủ động kết nối Hub, áp cột Hub sở hữu và gửi dữ liệu máy lên. Lỗi agent/mạng không kéo backend chết theo.
- **Hai chiều khác nhau:** Hub → máy là snapshot danh mục; máy → Hub là sự kiện tăng dần và ảnh chụp sức khỏe/tồn/khe. Không replication MySQL, không máy client mỏng (C-01..C-04, C-30).

## 3. Non-negotiable architecture invariants

Các bất biến của thiết kế nguồn phải được giữ; chúng không chứng minh cơ chế đã triển khai. Phần thiếu/chưa thống nhất vẫn theo Q, không tự điền giải pháp.

- **C-01/C-02/C-03:** Hub ngoài đường bán/pha; `order_ticket` và `claim()` nguyên tử tại máy là thẩm quyền vé. In lại cùng vé không tạo quyền pha thêm. Agent là tiến trình riêng.
- **C-04/C-06/C-07:** máy mở kết nối ra; không mở backend trên LAN/Wi-Fi tiệm. Một chủ ghi cho mỗi cột; không ghi đè dữ liệu máy bằng snapshot. Dữ liệu dẫn xuất phải tính/dựng lại.
- **C-08/C-09/C-12:** snapshot đầy đủ, kiểm đích/chữ ký/schema/assets; `recipe` và `recipe_action` cùng transaction. Không áp DDL trong transaction danh mục; không hứa rollback transaction đã commit (Q-22).
- **C-10/C-11:** at-least-once, ghi lặp vô hại; không thêm outbox trên đường bán. Cursor chỉ tiến sau HTTP 200 **và** ACK đúng `cursor_to` đã ghi; không dọn dữ liệu chưa ACK.
- **C-05/C-13/C-15/C-17:** MID không tái sử dụng; không đánh số lại/đổi nghĩa/tái cấp mã nguyên liệu đã cấp. Thay mã nguyên liệu vẫn qua cửa sổ yên tĩnh; pin recipe không bãi bỏ C-17 (Q-11).
- **C-14/C-16:** tối đa 10 PUMP, 16 MANUAL, 12 lựa chọn/đơn, 9999 g/chỉ thị. Tiền kiểm tại trình soạn và Hub; món thiếu năng lực phần cứng bị lọc khỏi snapshot bán được. Phạm vi kiểm `gpio` còn Q-29.
- **C-17/C-18, REQ-10/11:** chụp `price`/`drink_name` lúc phát hành; không tính lại vé theo giá mới. Issue kiểm `available`/`in_stock`; giá/menu lệch trả 409 để khách xác nhận trước in. Không đồng nghĩa giữ chỗ tồn kho.
- **C-20/C-21/C-23/C-24:** giữ bí mật máy, phạm vi tài khoản, chốt phần cứng tại máy và xác minh release độc lập; chi tiết §6.
- **C-25/C-26/C-28:** runtime/profile/hiệu chuẩn ngoài cây mã; release mới + đổi symlink, không `git pull` trên cây đang bán hoặc `reset --hard` xóa runtime. Ledger chỉ ghi migration thành công; rollback code không rollback schema. Rollout máy thử → điểm bán → toàn đội qua cổng sức khỏe.
- **C-12/C-19/C-27/C-29:** UTC ISO-8601 qua dây; đồng bộ giờ trước nhận đơn; timeout cổng chờ 10 phút; backup/restore và 17 cảnh báo khả năng bán. Giữ các phần chưa chốt tại §9, §10, §14.
- **C-30:** không replication, client mỏng, QR key chung cả đội hoặc dùng chung hiệu chuẩn. Hiệu lực lâu dài của toàn bộ danh sách “hướng bị loại” vẫn là Q-31.

## 4. Data ownership

Nguồn chi tiết: [DATABASE_SPEC.md](DATABASE_SPEC.md), C-06/C-07. Không dùng bảng tóm tắt này thay DDL; physical schema còn Q-23.

| Chủ ghi / loại | Dữ liệu và giới hạn |
|---|---|
| Hub | `drink`, `recipe`, `recipe_action`, `glass`, `drink_type`, `category`, mapping phân loại, assets; trừ cột máy/dẫn xuất. `deleted_at` là tombstone, cách áp còn Q-11. |
| Hub | `ingredient.id/name/type/data_type` qua ánh xạ giữ mã cũ; `drink.published`; `store_setting`; `admin_user`, `role_permission` đúng điểm bán. Override máy > điểm > đội là mô hình nguồn, chưa được DEC-001 duyệt toàn bộ A-01. |
| Máy | `order_ticket`, `error_log`, `ingredient.amount/in_stock/max_gram/gpio`, `drink.available`, hiệu chuẩn bơm/cân, `machine_profile.json`, ledger migration. Hub nhận bản sao/trạng thái. |
| Máy, riêng tư | `order_ticket.note` không vào telemetry; `QRPROTO_KEY`, `admin_account.json` không gửi Hub. |
| Dẫn xuất | `ingredient.threshold_gram` = 110% lượng dùng lớn nhất theo công thức nguồn; `drink.in_stock` từ trigger/tồn; `menu-data.js` dựng bằng `sync_menu`. Tác động recipe ghim còn Q-11. |
| Máy áp lệnh | `order_mode.json`, `display_mode.json`; Hub không ghi file tùy tiện. |
| Audit | Máy ghi, Hub gộp theo nguồn. Audit thao tác Hub là đề xuất; chủ ghi, bảng/khóa/source và bằng chứng tin cậy còn Q-30. |

Phân biệt bốn khái niệm: **pha được ở máy này** (capability), **published** (Hub), **available** (quầy), **in_stock** (dẫn xuất). Tắt bán không tự vô hiệu vé đã in.

## 5. Communication model

Theo [API_PROTOCOL.md](API_PROTOCOL.md), C-04/C-08/C-12/C-22:

| Gói | Đường và nội dung |
|---|---|
| Snapshot | `GET /v1/state?have=<version>` → 304 hoặc snapshot đầy đủ theo máy; `contract`, `version`, `min_schema`, `generated_at`, `machine_id`, danh mục, assets/hash/size, `signature`. |
| Events | `POST /v1/events`; `kind` ticket/error/audit, `machine_id`, `cursor_from`, `rows[]`, `cursor_to`. |
| Heartbeat | `POST /v1/beat`; version/schema, sức khỏe, clock/timezone, khả năng bán, tồn đọng. Key/type/tần suất và dữ liệu đủ cho 17 cảnh báo chưa hoàn chỉnh. |
| Commands/ACK | Máy mở kết nối; long-poll trong DEC-008 DRAFT. Envelope có ID, kind/args, người phát, thời điểm/hạn; ACK `accepted`, `refused`, `done`, `failed`. URL/schema chi tiết còn mở. |

HTTPS/Tailscale được mô tả trong nguồn; phối hợp mTLS/Ed25519 chưa chốt Q-15. UTC ISO-8601 qua dây; ngày kinh doanh dùng timezone máy, không coi DATETIME tự chứa timezone. Bỏ qua trường bổ sung chưa hiểu, không xóa/đổi nghĩa trường contract; thiếu schema phải từ chối snapshot. Backup/assets/diagnostics và vị trí gói tồn/khe còn Q-15. Đây chưa phải OpenAPI hoàn chỉnh.

## 6. Security rules

Nguồn: [SECURITY_SPEC.md](SECURITY_SPEC.md), C-20..C-24.

- Khóa QR riêng từng máy, không dùng chung hoặc gửi Hub; khóa phiên máy riêng. Không gộp khóa thiết bị, QR, phiên, release và snapshot theo suy đoán.
- **Private key ký release ở ngoài Hub, ngoại tuyến.** Hub chỉ chọn release đã ký. Máy verify bằng public key tin cậy cài sẵn **trước** chạy mã/installer/migration. Chủ khóa snapshot là Q-26, không suy rộng invariant release sang snapshot.
- UUID/cặp Ed25519 thiết bị trong `/etc/flexmix/fleet.env` quyền 0600 theo nguồn; nhận diện bằng credential, không bằng IP. Cách sử dụng/kết hợp mTLS/Ed25519, replay, rotate/revoke và proxy trust vẫn Q-12/Q-15. Chọn Nginx không chốt TLS termination.
- Backend chỉ loopback/Tailscale theo nguồn; API ticket/print/start/relay/test còn phải siết trước pha 06. **Chưa chọn** loopback-only hay token (Q-19). Giữ allowlist file; không phục vụ bí mật.
- Hardware test luôn cần test mode xác nhận tại máy (panel 15), kể cả backend chết. Restart/release từ chối khi đang pha; display mode hợp lệ và tự hoàn tác 20 giây; không tắt cả printQR và runDirect.
- Tài khoản đúng điểm bán, PBKDF2 hash/salt/rounds, không password thô; login offline bằng bản sao. Thu hồi qua `sessions_valid_from` chỉ có hiệu lực sau sync, không tức thì khi offline. Vai vận hành đội chỉ ở Hub; quyền chi tiết/hai người duyệt còn Q-09.
- Note chỉ lấy cho khiếu nại cụ thể qua diagnostics có chủ đích/audit; log không chứa mật khẩu/private key/token thô. Policy backup vẫn Q-16, ownership/toàn vẹn audit vẫn Q-30.
- Hub bị chiếm quyền vẫn có thể sửa giá/công thức, downgrade release đã ký hoặc lạm dụng lệnh hợp lệ. Không tuyên bố Hub vô hại; giới hạn quyền và ứng phó còn Q-19/Q-20.

## 7. Important IDs and identity rules

- **ID tài liệu:** REQ = yêu cầu/nghiệm thu; C = ràng buộc nguồn; A = giả định; Q = câu hỏi chuẩn; DEC = nhật ký quyết định; D = câu hỏi lịch sử được map về Q. Không đổi số/tái cấp ID. NQ đã gộp vào Q, không dùng làm câu hỏi độc lập.
- **MID:** Hub cấp duy nhất, không mặc định nhập tay 1; thanh lý giữ lịch sử, thay máy cấp MID mới. DEC-009/Q-27 DRAFT chọn số nguyên dương **1–999999**, không tái sử dụng kể cả thay thế. Payload QR còn cần xác minh.
- **MID ≠ mặc định UUID ≠ mặc định wire `machine_id`.** Quan hệ với credential, đăng ký lại/cấp đồng thời và kiểm danh tính còn Q-12; không cho request tự khai máy khác.
- Vé Hub có khóa `(machine_id, serial)`, không sửa serial/lịch sử để gộp máy. `(machine_id, error_id)` mới là khóa lỗi gợi ý; khóa audit/dedup còn Q-14/Q-30.
- Nguyên liệu ánh xạ theo máy; lựa chọn boolean/percentage mới dùng **1–24**, weight mới từ **100**; giữ mã đã ngừng dùng, hết mã thì từ chối cấp, không renumber. Collision drink/glass/SKU khi onboarding còn Q-13; các khoảng ID hiện trạng không phải DDL Hub đã duyệt.

## 8. Sync/event rules

- Snapshot kiểm contract, đích, `min_schema`, chữ ký và asset hash/size trước apply; chỉ upsert cột Hub sở hữu. `recipe`/`recipe_action` cùng transaction/dãy `step_no`. Không xóa vật lý lịch sử hoặc suy ra món thiếu trong snapshot được phép xóa tùy ý.
- C-17 vẫn yêu cầu cửa sổ yên tĩnh cho mã nguyên liệu. DEC-006/Q-11 DRAFT chọn pin recipe lúc tạo ticket, recipe mới chỉ cho ticket sau publish, không đổi ticket cũ; schema pin/publish-apply offline/xóa mềm còn mở.
- Lỗi trước commit rollback; lỗi `sync_menu` sau commit cần recovery chưa chốt Q-22. Ghi version trong cùng transaction mới là đề xuất. DDL/migration riêng; ledger máy và migration Hub không phải cùng version.
- Máy đọc lỗi theo `error_id`, vé theo `updated_at` có overlap. Mất ACK gửi lại; Hub upsert không nhân vé và không để payload cũ ghi đè mới. Độ dài overlap, tie-breaker, partial batch, retry/backoff, retention/dedup còn Q-14.
- Catalogue rollback chỉ đến snapshot từng áp thành công, bảo vệ vé/schema/assets. Version cũ hay version mới chứa nội dung cũ và số bản giữ còn Q-18.
- Lệnh hết hạn từ chối; lặp phải an toàn. Lưu command ID/trạng thái bền là đề xuất, chưa đủ giải crash giữa side effect và commit (Q-20).

## 9. Failure/offline rules

- Mất Hub/mạng hoặc agent lỗi không ngắt bán/in/pha/login khi phụ thuộc cục bộ còn đáp ứng; sync dừng/retry, giữ cursor. MySQL máy dừng thì bán/pha/in/login quản trị dừng, chỉ beat còn theo ma trận nguồn.
- **Không hứa bán offline vô điều kiện lúc boot.** DEC-007 DRAFT nói không nhận order khi boot offline chưa sync clock; nguồn ô Q-22, mapping sang Q-21 chưa xác nhận. Không suy ra RTC bắt buộc, Hub là nguồn giờ hoặc chỉ `After/Wants=time-sync.target` là đủ chứng minh sync.
- Snapshot lỗi không được để nửa transaction; DB mới/menu cũ sau commit vẫn Q-22. Ma trận suy giảm là mô tả nguồn, không bằng chứng lỗi đã sửa.
- Cổng chờ người timeout 10 phút và hủy an toàn (C-19). `release-stranded` chỉ khi rảnh; không dùng thay cancel khi runner bận. Nguồn trả vé về unused sau reboot, nhưng hủy/mất điện sau khi rót chưa đủ quy tắc vé/tồn (Q-20); không tự bảo đảm pha lại miễn phí là đúng.
- Tồn trừ khi hoàn tất hoặc xử lý pha hỏng, không reservation lúc in. `unused + expired` chỉ xấp xỉ “chưa từng quét”; báo cáo used/completed_at không đại diện đủ tiền thu lúc in (Q-07/Q-17).

## 10. Backup rules

Theo C-27 và [DEPLOYMENT.md](DEPLOYMENT.md): backup đêm `mysqldump --single-transaction` + hiệu chuẩn/profile, **7 bản trên ổ khác**; cùng thẻ SD không bảo vệ mất thẻ. Backup trước migration giữ **3 bản**. Có agent mới gửi gói được phép lên Hub; Hub giữ **N chưa chốt**, cảnh báo bản mới nhất **>36 giờ**. Diễn tập restore trên máy thử, kiểm phần cứng và khả năng bán.

**Q-16 vẫn OPEN:** note/bí mật trong dump, mã hóa ở đâu, quyền download/restore, retention, RPO/RTO, tính nhất quán DB/files và phục hồi sang máy mới. Không gửi `QRPROTO_KEY`/`admin_account.json` Hub. DEC-002/Q-04 DRAFT chọn chấp nhận mất khóa QR, không chọn ký gửi. Máy thay thế MID mới; lịch sử giữ MID cũ, không tự kích hoạt vé cũ. Chính sách chặn release khi backup lỗi cũng chưa chốt trong DEPLOYMENT.

## 11. Technology stack

**DEC-008/Q-24 DRAFT**, đúng danh sách OWNER: Python; FastAPI, Pydantic, Uvicorn; MySQL 8; SQLAlchemy, PyMySQL, Alembic; Jinja2; long-poll; Nginx, systemd; pytest và MySQL container **cho development**.

Phiên bản cụ thể/đóng gói còn Q-24. VM, worker riêng/cùng codebase, hàng đợi trong MySQL, assets trên volume là **ASSUMPTION A-02/A-03/A-04**, không tự coi được duyệt cùng stack. Repo là A-05/Q-25. Không suy ra Redis/Kafka/Celery/Kubernetes/microservices bị cấm vĩnh viễn vì chưa có trong baseline. Chi tiết: [TECH_STACK.md](TECH_STACK.md).

## 12. Project structure

[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) vẫn là **đề xuất** cho toàn bộ cây. Phase 00 mới scaffold `src/flexmix_hub/{api,infrastructure/database}`, `migrations/hub`, `tests/{unit,integration}` và `config/examples`; phần còn lại chưa được tạo hay triển khai.

Modules đề xuất: fleet, catalogue, synchronization, reporting, monitoring, identity, audit, commands, releases, backups. Giữ backend/agent/installer ở repo máy và Hub/contracts ở repo này mới là A-05; Q-25 chưa chọn mono/multi-repo hoặc owner contract. Không giả định repo máy đã checkout. Runtime, hiệu chuẩn, assets/backup và khóa thật ngoài cây release; không chia sẻ ORM/import backend phần cứng qua Hub theo cấu trúc đề xuất. Machine migrations và Hub migrations có vòng đời riêng.

## 13. OWNER decisions — nội dung đã trả lời, chưa ACCEPTED

**Chưa có quyết định “đã chốt” theo trạng thái ACCEPTED.** Bảng sau chỉ tóm tắt câu trả lời được ghi trong [06_decisions.md](06_decisions.md); **tất cả DRAFT**. Không tự nâng trạng thái hoặc bổ sung phần thiếu.

| DEC / Q | Nội dung OWNER | Giới hạn quan trọng |
|---|---|---|
| DEC-001 / Q-01 | Một thực đơn chung cả đội | Override theo điểm chưa được xác nhận, không duyệt toàn bộ A-01. |
| DEC-002 / Q-04 | Chấp nhận mất khóa QR | Đủ lựa chọn; không giải policy backup Q-16. |
| DEC-003 / Q-05 | Không đặt máy này lấy máy khác | Đủ lựa chọn; giữ thẩm quyền vé tại máy. |
| DEC-004 / Q-07 | Thu tiền lúc in nhãn | Không tự thêm payment/refund/reservation hoặc chọn báo cáo thay thế. |
| DEC-005 / Q-08 | 08:00–22:00 mỗi ngày; quản lý cửa hàng nhận; không trực ngoài giờ; ngoài giờ xử lý trong ngày | Chưa rõ timezone/SLA/cuối ngày; không đổi thành ngày làm việc kế tiếp. |
| DEC-006 / Q-11 | Pin recipe tại tạo ticket; recipe mới chỉ cho ticket tạo sau publish; không đổi ticket cũ | Không giải mã nguyên liệu, xóa mềm, lưu trữ/migration, publish/apply offline. |
| DEC-007 / Q-21 đề nghị; nguồn Q-22 | Không nhận order khi boot offline chưa sync clock | Mapping biên tập chưa OWNER xác nhận; không trả lời sync_menu Q-22. |
| DEC-008 / Q-24 | Danh sách stack tại §11 | Không duyệt ngầm topology, repo, version, proxy trust. |
| DEC-009 / Q-27 | MID nguyên dương 1–999999; không tái dùng cả decommission/thay thế | Không chốt wire identity Q-12 hoặc giới hạn bit QR. |

## 14. OPEN QUESTION còn ảnh hưởng implementation

Sổ chuẩn: [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md). **Mọi Q vẫn OPEN về phê duyệt**; Q-04/Q-05 đủ lựa chọn nhưng DEC còn DRAFT. Những phần chưa có đáp án không được coi là mặc định hoặc “tạm chọn”.

| Q | Phần còn thiếu / nơi bị ảnh hưởng |
|---|---|
| Q-01, Q-02, Q-03, Q-06 | Override menu; quy mô/địa bàn; GPIO/khe giống hay khác; nơi đặt/người vận hành Hub. |
| Q-07, Q-08, Q-17 | Báo cáo tiền; timezone/SLA/cảnh báo cuối ngày; đo chưa từng quét, in lại/hủy/hoàn tiền và mẫu số. |
| Q-09 | OWNER chỉ ghi “không” cho câu hỏi ghép; không biết phủ định quyền đổi từ xa hay hai người duyệt. Chưa có DEC. |
| Q-10 | “7 file runtime” nhưng liệt kê 8 đường dẫn; cần repo thật/layout, không tự loại cả machine.py. |
| Q-11 | Cửa sổ mã nguyên liệu, xóa mềm, pin recipe nguyên tử/lưu trữ; publish/apply offline; threshold/in_stock/capability/assets của recipe ghim. |
| Q-12, Q-13, Q-27 | MID/UUID/machine_id/credential; onboarding collision drink/glass/SKU và mã cũ; giới hạn QR của MID. |
| Q-14 | Cursor/overlap/tie-breaker/clock/late commit, ACK/partial batch, dedup/thứ tự, retry/backoff/retention. |
| Q-15, Q-26 | Contract/type/min_schema/endpoints/upload; mTLS/Ed25519/canonicalization/replay/credential; owner/thuật toán/phân phối/rotation/compromise khóa snapshot. |
| Q-16 | Nội dung backup, note, mã hóa, ACL, retention, restore và RPO/RTO. |
| Q-18 | Rollback catalogue/version/have/N và bảo toàn recipe/tombstone/assets cho vé. |
| Q-19, Q-20 | Quyền Hub/API máy/OS/downgrade; command durability/timeout/retry/crash; health gate/rollback; cancel sau rót và xác nhận màn hình. |
| Q-21, Q-22 | Mapping DEC-007; clock/RTC/pha 00–01; recovery sync_menu sau commit, version nguyên tử, runtime nối release và phạm vi audit. |
| Q-23 | Physical DDL/index/FK/tiền/default/backfill/migration dở dang; heartbeat đủ 17 cảnh báo. |
| Q-24, Q-25 | Phiên bản/đóng gói và giả định ngoài stack đã liệt kê; repo/agent/owner/versioning contract. |
| Q-28, Q-29, Q-30, Q-31 | Mẫu số pha hỏng khi món rút; PUMP thiếu gpio; audit Hub/Machine/khóa/source/toàn vẹn; hiệu lực các hướng bị loại. |

**Mapping chưa chắc chắn:** M-01 batch/retry của lệnh hay events; M-02 event rate/số người vận hành; M-03 retention assets; M-04 repo máy/đóng gói/test; M-05 owner module/bảng/transaction; M-06 ranh giới vị trí/vận hành/stack Hub. Không tự gộp thành Q mới hoặc coi đã giải.

**Contradiction/khoảng trống phải giữ rõ** ([review](ARCHITECTURE_CONSISTENCY_REVIEW.md)):

- Q-11: nguồn có hai cách diễn đạt cửa sổ yên tĩnh; pin recipe không tự chọn điều kiện mã nguyên liệu/xóa mềm. Publish trên Hub chưa định nghĩa hành vi máy offline chưa apply.
- Q-21: “luôn bán offline” không đúng vô điều kiện khi boot chưa có giờ; DEC-007 ghi điều kiện nhưng mapping/clock còn mở. Pha 00 nói chưa Hub, trong khi lỗi chặn MID cần Hub pha 01.
- Q-22: không thể rollback DB đã commit để xử lý sync_menu lỗi. Q-20: trả unused sau rót chưa giải quyền pha lại/tồn kho.
- Q-16: dump đầy đủ có thể mang note dù telemetry cấm; chưa có ngoại lệ backup được duyệt.
- Q-07/Q-17: thu tiền lúc in nhưng báo cáo nguồn chỉ used/completed_at. Q-08: không trực ngoài giờ nhưng “xử lý trong ngày” chưa có cách hiểu cuối ngày.
- Q-19: chữ ký release không làm Hub vô hại; quyền hợp lệ/downgrade vẫn gây thiệt hại. Q-09 mơ hồ và Q-10 lệch số runtime chưa được giải.

## 15. Phase roadmap

Tóm tắt [DEPLOYMENT.md](DEPLOYMENT.md); không phải xác nhận pha nào đã hoàn thành hoặc đã được phép vượt câu hỏi mở.

| Pha | Nội dung / cổng hoàn thành | Rủi ro theo nguồn |
|---|---|---|
| 00 | Tách runtime/profile, clock, schema ledger, backup; cập nhật an toàn và restore thử thành công | Gỡ rủi ro hiện có; trình tự MID còn Q-21 |
| 00b | Timeout, tiền kiểm món, kiểm tồn issue, 409 lệch giá, từ chối món rút lịch sự không ghi error_log; kiểm tại máy | Thấp, từng việc lùi riêng; Q-20/Q-28/Q-29 còn mở |
| 01 | Registry/fleet.env/MID/Tailscale ACL-tag; không trùng MID, đúng quyền bảo trì | Không đổi đường bán; identity/security chưa chốt |
| 02 | Agent chỉ đọc, beat/events/tồn/khe/backup/updated_at/giờ mở cửa; sync lặp an toàn, đủ 17 cảnh báo | Gần như không; Q-14/Q-15/Q-16/Q-23 chưa đủ |
| 03 | Danh mục chuẩn, đối chiếu có người duyệt, so menu hiện hữu; chưa ghi xuống | Chỉ đọc; Q-01/Q-03/Q-13 |
| 04 | Snapshot/pin máy/rollback; giá-tên-ảnh-published theo nguồn; bảo vệ vé với recipe/mã/xóa mềm | Có thật; DEC-006 DRAFT, Q-11/Q-18/Q-22/Q-26 |
| 05 | Tài khoản theo điểm, phân quyền/audit; login offline và khôi phục auth tại chỗ | Nguy cơ khóa ngoài; giữ auth.py --set-password; Q-09/Q-30 |
| 06 | Lệnh/diagnostics/release theo vòng; kiểm chữ ký, API, chốt máy và rollback | Cao nhất; máy thử bắt buộc, Q-19/Q-20 |

C-28: rollout máy thử → một điểm bán → toàn đội; không mở vòng nếu health chưa đạt. Tiêu chí/thời gian quan sát còn Q-20. Không dùng nhóm “CAN DECIDE LATER” để coi cảnh báo/validation/reporting chưa hoàn chỉnh đã đạt cổng.

## 16. Rules dành cho AI coding agent

1. Dùng file này để định hướng; trước khi sửa một phần, đọc source tương ứng và trạng thái Q/DEC hiện hành. Khi nguồn đổi, summary có thể lỗi thời; không để summary ghi đè nguồn.
2. Không tự tạo decision, nâng DRAFT thành ACCEPTED, đóng Q, đổi nghĩa ID hoặc biến giả định thành yêu cầu OWNER. “Chưa quyết định” không đồng nghĩa DEFERRED; không suy diễn câu trả lời mơ hồ.
3. Không quyết ngầm schema/auth/protocol/offline/backup thuộc Q còn mở bằng implementation. Nêu đúng Q, phần thiếu và ảnh hưởng; tiếp tục phần độc lập trong phạm vi đã được giao.
4. Giữ invariant/ownership/chốt bảo mật. Pin recipe, baseline framework hoặc summary này không cho phép phá C-17, đổi thẩm quyền vé hay nới quyền Hub.
5. Phân biệt hiện trạng nguồn, mục tiêu, đề xuất và kết quả kiểm chứng. Không giả định file/module trong cây đề xuất đã tồn tại, API đã đầy đủ hoặc DDL đã duyệt.
6. Gặp contradiction, ghi lại cả hai phát biểu và ID nguồn; không tự chọn nhánh. Khi có quyết định mới thật sự, theo quy trình 06_decisions → OPEN_QUESTIONS → spec bị ảnh hưởng; summary cập nhật theo sau.
7. Khi được giao implementation, kiểm theo tiêu chí nguồn: mất ACK/gửi lặp, serial trùng giữa máy, ownership, snapshot lỗi, offline/clock, migration/recovery, chốt lệnh và restore. Không báo hoàn thành pha chỉ vì test đơn vị chạy qua; bộ tài liệu hiện chưa có kết quả nghiệm thu.

## SOURCE DOCUMENTS

Toàn bộ tài liệu trực tiếp dùng tổng hợp bản context này:

- [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md)
- [06_decisions.md](06_decisions.md)
- [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)
- [TECH_STACK.md](TECH_STACK.md)
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- [SECURITY_SPEC.md](SECURITY_SPEC.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [API_PROTOCOL.md](API_PROTOCOL.md)
- [DATABASE_SPEC.md](DATABASE_SPEC.md)
- [ARCHITECTURE_CONSISTENCY_REVIEW.md](ARCHITECTURE_CONSISTENCY_REVIEW.md)
