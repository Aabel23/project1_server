# Cấu trúc repository đề xuất

Nguồn: [Kien_Truc_Doi_May.html](../Kien_Truc_Doi_May.html), bản 3 ngày 10/09/2026. Sơ đồ toàn bộ vẫn là dự kiến. Phase 00 đã tạo foundation tối thiểu: `src/flexmix_hub/{api,infrastructure/database}`, `migrations/hub`, `tests/{unit,integration}`, manifest Python, Compose MySQL development và cấu hình mẫu. Foundation không tạo module nghiệp vụ, contract, schema nghiệp vụ hay implementation agent/máy.

Tài liệu liên quan: [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md), [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) (sổ theo dõi chuẩn; tổ chức repo đang chờ Q-25), [06_decisions.md](06_decisions.md).

**REQUIREMENT**: lấy từ tài liệu nguồn. **ASSUMPTION**: lựa chọn cấu trúc đề xuất. **OPEN QUESTION**: cần chốt trước khi mở rộng tổ chức mã thật. Phase 00 không giải quyết Q-25.

## Cập nhật từ OWNER — DRAFT, 17/09/2026

DEC-008 (DRAFT): OWNER chọn Python, FastAPI, Pydantic, Uvicorn, MySQL 8, SQLAlchemy, PyMySQL, Alembic, Jinja2, long-poll, Nginx, systemd, pytest và MySQL container cho development. Phiên bản cụ thể và đóng gói còn mở; không suy ra VM, worker/hàng đợi, volume assets hay repo đã được duyệt.

DEC-004 (DRAFT): thu tiền lúc in nhãn. Báo cáo used/completed_at chỉ phản ánh vé pha xong, không đủ đại diện tiền thực thu. OWNER chưa chọn schema thanh toán/hoàn tiền hoặc công thức báo cáo thay thế (Q-07, Q-17).

Q-25 chưa được trả lời; baseline công nghệ không phê duyệt cấu trúc repo.

Các DEC được ghi tại [06_decisions.md](06_decisions.md), chưa ACCEPTED và chưa là căn cứ triển khai. Phần nguồn/hiện trạng được giữ để truy nguyên.

## Phạm vi repository

**ASSUMPTION —** Giữ repository này cho Hub và hợp đồng Hub–agent. Backend máy, agent và `deploy/install.sh` nằm trong repository phần mềm máy hiện hữu. Nguồn mô tả mã máy `version1.0 @ ce17f05`, nhưng workspace hiện tại không có mã đó; không giả định đã có checkout hay đường dẫn repository máy.

**REQUIREMENT —** Hub và agent viết độc lập dựa trên bốn gói tin: snapshot, events, heartbeat, commands/ACK. Agent chạy riêng backend; cấu trúc repo không được làm mất ranh giới này.

## Cây thư mục Hub

**ASSUMPTION —** Toàn bộ tên thư mục/file chưa tồn tại dưới đây là đề xuất. Các file trong `docs/` và `ARCHITECTURE_REVIEW.md` đã tồn tại.

```text
Server_Flex_mix/
├── Kien_Truc_Doi_May.html
├── ARCHITECTURE_REVIEW.md
├── docs/
│   ├── 06_decisions.md
│   ├── API_PROTOCOL.md
│   ├── ARCHITECTURE.md
│   ├── ARCHITECTURE_CONSISTENCY_REVIEW.md
│   ├── ARCHITECTURE_DECISIONS.md
│   ├── DATABASE_SPEC.md
│   ├── DECISION_QUESTIONNAIRE.md
│   ├── DEPLOYMENT.md
│   ├── MASTER_REQUIREMENTS.md
│   ├── OPEN_QUESTIONS.md
│   ├── PROJECT_STRUCTURE.md
│   ├── SECURITY_SPEC.md
│   └── TECH_STACK.md
├── contracts/
│   ├── state/
│   ├── events/
│   ├── beat/
│   ├── commands/
│   └── examples/
├── src/
│   └── flexmix_hub/
│       ├── api/
│       ├── web/
│       │   ├── templates/
│       │   └── static/
│       ├── modules/
│       │   ├── fleet/
│       │   ├── catalogue/
│       │   ├── synchronization/
│       │   ├── reporting/
│       │   ├── monitoring/
│       │   ├── identity/
│       │   ├── audit/
│       │   ├── commands/
│       │   ├── releases/
│       │   └── backups/
│       ├── infrastructure/
│       │   ├── database/
│       │   ├── storage/
│       │   └── security/
│       └── workers/
├── migrations/
│   └── hub/
├── tests/
│   ├── unit/
│   ├── contracts/
│   ├── integration/
│   └── fleet_simulation/
├── deploy/
│   └── hub/
│       ├── systemd/
│       └── nginx/
└── config/
    └── examples/
```

## Trách nhiệm và truy nguyên phạm vi

**ASSUMPTION —** Cách chia thư mục/module là đề xuất. Cột “REQUIREMENT nguồn” mô tả chức năng đã có trong HTML mà thư mục phục vụ; không phải chức năng mới.

| Vị trí đề xuất | Trách nhiệm | REQUIREMENT nguồn |
|---|---|---|
| `contracts/` | Schema và mẫu dữ liệu có version, không logic phần cứng hoặc ORM | Bốn gói tin; UTC; min_schema; tương thích tiến |
| `api/` | HTTP adapters cho máy và giao diện Hub | Máy gọi ra, state/events/beat và hàng đợi lệnh |
| `web/` | Màn hình quản lý, đối chiếu, giám sát và lệnh | Hub có danh mục, dashboard, tài khoản và mặt phẳng điều khiển |
| `fleet/` | Registry MID, điểm bán, profile/khe do máy báo, ánh xạ danh tính | MID duy nhất, không tái dùng, vòng đời máy |
| `catalogue/` | Danh mục chuẩn, ánh xạ/cấp mã theo máy, capability và ghi đè | Giữ mã cũ, giới hạn 1–24, lọc món pha được |
| `synchronization/` | Sinh snapshot, tiếp nhận events, cursor/ACK và idempotency | Hai luồng dữ liệu khác hình dạng |
| `reporting/` | Tổng hợp vé theo máy/ngày; thu lúc in nhãn theo DEC-004 DRAFT, mô hình báo cáo còn mở Q-07/Q-17 | Báo cáo vé, completed_at và ngày địa phương |
| `monitoring/` | Beat, trạng thái máy và 17 cảnh báo nguồn nêu | Giám sát khả năng bán và sức khỏe |
| `identity/` | Tài khoản, phạm vi điểm bán, vai vận hành đội | Hub làm chủ admin_user/role_permission |
| `audit/` | Gộp audit theo nguồn và phục vụ truy vết | Ai thao tác, khi nào, endpoint, trước/sau |
| `commands/` | Hàng đợi, hạn dùng, người yêu cầu, ACK | Lệnh nhận qua kết nối agent và chạy lặp an toàn |
| `releases/` | Danh sách bản đã ký, phân vòng, trạng thái triển khai | Hub chọn release; không tạo/giữ khóa ký release |
| `backups/` | Nhận gói được phép, metadata/retention và trạng thái backup | Backup theo máy, cảnh báo >36 giờ |
| `infrastructure/` | Adapter MySQL, file storage và xác thực | Transaction, assets hash, HTTPS/mTLS/request signature |
| `workers/` | Chạy tác vụ nền của các module hiện có | Đồng bộ, giám sát, lệnh và tiến trình phát hành |
| `migrations/hub/` | Migration riêng schema Hub | Không thay ledger/migration tại máy |
| `tests/fleet_simulation/` | Mô phỏng nhiều máy với MySQL, không GPIO | Máy giả để thử rollout, serial trùng, mất beat |
| `deploy/hub/` | Cấu hình triển khai Hub theo stack được chốt | Phục vụ Hub; không thay deploy/install.sh ở máy |

## Ranh giới phụ thuộc

- **ASSUMPTION:** `api/`, `web/`, `workers/` gọi module nghiệp vụ; module sử dụng adapter trong `infrastructure/`. Không tách mỗi module thành microservice.
- **REQUIREMENT:** logic claim vé, điều khiển bơm, cân và timeout chờ người nằm tại máy; Hub chỉ gửi lệnh đã cho phép, máy kiểm chốt tại chỗ.
- **ASSUMPTION:** `contracts/` là nguồn hợp đồng chuẩn có version để repo agent sử dụng; không chia sẻ ORM hoặc import code Hub vào backend máy.
- **REQUIREMENT:** machine migrations và Hub migrations có vòng đời khác nhau; agent báo schema máy, Hub không được xem migration Hub là phiên bản schema máy.
- **REQUIREMENT:** ảnh/clip theo hash, backup, runtime và khóa thật không nằm trong cây source release. `config/examples/` chỉ chứa mẫu không có bí mật.
- **ASSUMPTION:** API và worker triển khai cùng phiên bản Hub, tiến trình riêng; cách bảo đảm worker không xử lý trùng dựa trên state bền vững trong MySQL sẽ được chốt cùng giao thức lệnh.

## Quan hệ với repository máy

| Nhãn | Nội dung |
|---|---|
| REQUIREMENT | Giữ backend hiện có và deploy/install.sh; agent phải là `flexmix-agent.service` riêng |
| ASSUMPTION | Module agent được bổ sung trong repo máy để đi cùng release/installer của máy; vị trí cụ thể chỉ chọn sau khi đọc repo đó |
| REQUIREMENT | Không đưa runtime, hiệu chuẩn và profile riêng của máy trở lại cây git khi tổ chức repo |
| ASSUMPTION | Kiểm tra contract giữa Hub và agent dùng phiên bản schema/mẫu dữ liệu tương ứng, không cần gom hai repo thành một |

## OPEN QUESTION trước khi mở rộng scaffold

1. Có chấp thuận repo Hub riêng như trên, hay muốn monorepo Hub + agent? Đây là D-11 trong [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md), theo dõi tại Q-25.
2. Repo máy thực tế ở đâu, quy tắc đóng gói và test hiện có thế nào? (chưa có Q-*, xem OPEN_QUESTIONS M-04)
3. Ai quản lý version contract và cách đưa contract sang repo agent? (Q-25)
4. Jinja2, systemd/Nginx đã nằm trong DEC-008 (DRAFT); cấu trúc web/deploy, topology và đóng gói chưa được chọn (Q-24, Q-25).
5. Sau khi chốt MID/UUID, menu theo điểm và wire schemas, module nào chịu trách nhiệm các bảng/transaction liên quan? Cây trên chưa phải thiết kế schema vật lý. (chưa có Q-*, xem OPEN_QUESTIONS M-05)
