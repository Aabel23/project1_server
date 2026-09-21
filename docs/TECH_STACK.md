# Tech stack đề xuất cho FlexMix Hub

Nguồn kiến trúc: [Kien_Truc_Doi_May.html](../Kien_Truc_Doi_May.html), bản 3, 10/09/2026, tham chiếu `version1.0 @ ce17f05`. Chưa kiểm chứng mã nguồn ứng dụng. Tài liệu ghi baseline OWNER đã trả lời ở DEC-008 (DRAFT), các giả định còn lại và phần chưa chốt; không xác nhận đã triển khai hoặc DEC đã ACCEPTED.

Tài liệu liên quan: [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md), [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) (sổ theo dõi chuẩn; baseline có DEC-008 DRAFT; chi tiết Q-24 còn mở), [06_decisions.md](06_decisions.md).

## Cập nhật từ OWNER — DRAFT, 17/09/2026

DEC-008 (DRAFT): OWNER chọn Python, FastAPI, Pydantic, Uvicorn, MySQL 8, SQLAlchemy, PyMySQL, Alembic, Jinja2, long-poll, Nginx, systemd, pytest và MySQL container cho development. Phiên bản cụ thể và đóng gói còn mở; không suy ra VM, worker/hàng đợi, volume assets hay repo đã được duyệt.

Các DEC được ghi tại [06_decisions.md](06_decisions.md), chưa ACCEPTED và chưa là căn cứ triển khai. Phần nguồn/hiện trạng được giữ để truy nguyên.

## Phân loại

- **REQUIREMENT**: ràng buộc được nêu rõ trong tài liệu kiến trúc; không có nghĩa đã được triển khai.
- **ASSUMPTION**: giả định hoặc lựa chọn công nghệ đề xuất, gồm cả khuyến nghị chưa chốt trong nguồn.
- **OPEN QUESTION**: quyết định còn thiếu hoặc điểm nguồn chưa nhất quán.

**DRAFT DEC-008 (chỉ công nghệ):** tên công nghệ OWNER nêu đã có câu trả lời; các mô tả worker, topology, cơ chế proxy và lựa chọn triển khai trong cùng dòng vẫn là đề xuất, không tự được duyệt.

## Phương án đề xuất

**ASSUMPTION —** Hub là một ứng dụng Python tổ chức theo module, chạy trên một VM Linux; API/web và tác vụ nền dùng chung codebase, có thể chạy thành hai tiến trình. MySQL giữ dữ liệu nghiệp vụ và hàng đợi lệnh; file assets/backup nằm trên volume bền vững ngoài repository. Đây là lựa chọn ban đầu khi quy mô đội máy chưa chốt, không phải yêu cầu bắt buộc từ HTML.

| Thành phần | Nhãn | Lựa chọn | Căn cứ và giới hạn |
|---|---|---|---|
| Ngôn ngữ Hub | DRAFT DEC-008 (chỉ công nghệ) | Python | Mã máy được nguồn mô tả chủ yếu là Python; thuận lợi dùng cùng kỹ năng, nhưng Hub không import backend điều khiển phần cứng |
| HTTP API | DRAFT DEC-008 (chỉ công nghệ) | FastAPI + Pydantic + Uvicorn | Phục vụ state/events/beat/lệnh và kiểm payload; FastAPI hỗ trợ OpenAPI và mô hình Pydantic [1]. Schema vẫn phải tuân theo contract đã chốt |
| CSDL Hub | DRAFT DEC-008 (chỉ công nghệ) | MySQL dòng 8, chọn phiên bản cụ thể trước triển khai | MySQL 8 đã được OWNER chọn trong DEC-008 (DRAFT); VM vẫn là khuyến nghị, phiên bản cụ thể chưa chốt |
| Truy cập CSDL | DRAFT DEC-008 (chỉ công nghệ) | SQLAlchemy + PyMySQL | SQLAlchemy có dialect MySQL [2]; dùng transaction/upsert rõ ràng, không đồng bộ nguyên bảng hai chiều |
| Migration Hub | DRAFT DEC-008 (chỉ công nghệ) | Alembic | Công cụ migration cho SQLAlchemy [3]; chỉ áp dụng schema Hub, không thay cơ chế migration hiện có ở máy |
| Giao diện Hub | DRAFT DEC-008 (chỉ công nghệ) | HTML render phía server bằng Jinja2, CSS và JavaScript cho tương tác cần thiết | Đủ làm danh mục, đối chiếu mã, giám sát, tài khoản và lệnh đã nêu; chưa có yêu cầu SPA |
| Tác vụ nền | ASSUMPTION | Tiến trình Python riêng, trạng thái công việc trong MySQL | Xử lý nhận dữ liệu, cảnh báo, trạng thái lệnh và vòng release; cách chia worker còn phụ thuộc quy mô |
| Nhận lệnh | DRAFT DEC-008 (chỉ công nghệ) | HTTPS long-poll, agent mở kết nối | Nguồn cho phép long-poll hoặc WebSocket; OWNER chọn long-poll trong DEC-008 (DRAFT), chưa chốt timeout/chu kỳ |
| Mạng đồng bộ | REQUIREMENT | HTTPS qua Tailscale, máy chủ động gọi ra | Theo sơ đồ “Cái gì đi qua ranh giới”; không mở dịch vụ lên LAN tiệm |
| Xác thực kết nối/request | REQUIREMENT | mTLS và khóa Ed25519 thiết bị | Cả hai xuất hiện trong nguồn; nhãn REQUIREMENT là truy nguyên nguồn, không phải OWNER đã chốt cách dùng hoặc bắt buộc phối hợp cả hai. Q-15 vẫn OPEN |
| TLS reverse proxy | DRAFT DEC-008 (chỉ công nghệ) | Nginx | Có cơ chế xác minh chứng thư client [4]; nếu terminate mTLS tại proxy thì ứng dụng chỉ tin metadata từ proxy được kiểm soát |
| Assets và backup Hub | ASSUMPTION | Filesystem trên volume bền vững; metadata trong MySQL | Đáp ứng kho ảnh/clip theo hash và backup theo máy; chưa có cơ sở bắt buộc object storage |
| Triển khai Hub | DRAFT DEC-008 (chỉ công nghệ) | systemd quản lý API và worker, Nginx phía trước | Cách vận hành gọn trên một VM; nguồn bắt buộc unit riêng ở máy, không bắt buộc systemd cho Hub |
| Release máy | REQUIREMENT | Git tag ký ngoài Hub, agent xác minh, dùng `deploy/install.sh` | Hub chỉ phân phối/chọn bản đã ký; không giữ khóa ký release và không tự build/ký release |
| Kiểm thử | DRAFT DEC-008 (chỉ công nghệ) | pytest; MySQL container cho development theo DEC-008 (DRAFT); phạm vi kiểm thử container là đề xuất nguồn | Phục vụ ý tưởng máy giả trong nguồn; không thay MySQL bằng SQLite để kiểm transaction/DDL |

## Các ràng buộc chi phối stack

| Nhãn | Ràng buộc | Hệ quả lựa chọn công nghệ |
|---|---|---|
| REQUIREMENT | Hub không tham gia đường bán/pha | API, worker và database Hub không là phụ thuộc runtime của đơn hàng tại máy |
| REQUIREMENT | Snapshot đầy đủ, transaction dữ liệu nguyên tử; chỉ ghi cột Hub sở hữu; recovery sau commit còn mở Q-22 | Cần validation và transaction; không dùng replication để giải bài toán đồng bộ |
| REQUIREMENT | Giao ít nhất một lần, ACK cursor, upsert vé theo máy + serial | Tính bền vững/idempotency nằm trong contract và dữ liệu, không được giao phó cho framework |
| REQUIREMENT | Hub không giữ khóa QR hoặc khóa ký release | Secret của máy và khâu ký release nằm ngoài dịch vụ Hub |
| REQUIREMENT | Agent riêng, không làm thread của backend | Repository/module dùng chung không được tạo phụ thuộc tiến trình giữa Hub, agent và bộ pha |
| REQUIREMENT | Máy offline vẫn đăng nhập bằng bản sao tài khoản tại máy | Không thêm xác thực tập trung bắt buộc cho mỗi lần đăng nhập máy |

**ASSUMPTION —** Chưa đưa Redis, Kafka, Celery, Kubernetes hoặc microservices vào baseline: tài liệu chưa đặt yêu cầu khiến những thành phần này cần thiết. Đây là giới hạn của đề xuất, không phải lệnh cấm dùng chúng trong tương lai.

**ASSUMPTION —** Giám sát nghiệp vụ được thực hiện từ heartbeat, vé, lỗi và các ngưỡng đã có trong nguồn; không thêm sản phẩm analytics hoặc chức năng ngoài tài liệu.

## OPEN QUESTION cần chốt trước chọn phiên bản và triển khai

1. Quy mô máy, tốc độ events, số người vận hành và nơi đặt Hub là gì? (Q-02, Q-06; tốc độ events và số người vận hành chưa có Q-*, xem OPEN_QUESTIONS M-02)
2. Baseline đã có câu trả lời DEC-008 (DRAFT); còn phiên bản, đóng gói và phần giả định ngoài danh sách OWNER (Q-24).
3. Long-poll được chọn trong DEC-008 (DRAFT); chu kỳ, timeout và kích thước batch vẫn cần chốt. (Q-15, Q-20; batch xem M-01)
4. mTLS và chữ ký Ed25519 bổ trợ nhau thế nào; khóa ký snapshot thuộc ai? (Q-15; Q-26)
5. Dung lượng/retention assets và backup bao nhiêu; gói gửi Hub xử lý `note` thế nào? (Q-16; assets xem M-03)
6. Chọn phiên bản cụ thể của Python, MySQL và thư viện tương thích sau khi chốt môi trường; tài liệu này không gắn nhãn “latest” hoặc cam kết vòng đời hỗ trợ. (Q-24)

Chi tiết quyết định nằm trong [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md); tổ chức module trong [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

## Nguồn kỹ thuật đối chiếu

Các nguồn này chỉ hỗ trợ đánh giá công nghệ, không tạo thêm REQUIREMENT cho FlexMix.

1. [FastAPI — Features](https://github.com/fastapi/fastapi/blob/master/docs/en/docs/features.md): OpenAPI, JSON Schema và Pydantic.
2. [SQLAlchemy — MySQL dialect](https://docs.sqlalchemy.org/en/21/dialects/mysql.html): hỗ trợ MySQL và các driver.
3. [Alembic — Documentation](https://alembic.sqlalchemy.org/en/latest/): migration trong hệ SQLAlchemy.
4. [Nginx — SSL module](https://nginx.org/en/docs/http/ngx_http_ssl_module.html): TLS và xác minh chứng thư client.
