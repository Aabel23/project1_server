# Thông báo cho Claude: S-DB tạm dùng SQLite, S-NET làm riêng

Ngày 08/10/2026 (Bangkok), user yêu cầu Codex chia hai agent thực thi:

- Agent S-DB bổ sung lưu trữ tạm bằng SQLite `.db`.
- Agent S-NET thực thi TLS, các cổng và tín hiệu đánh thức.

## Quyết định áp dụng

SQLite dùng thư viện chuẩn `sqlite3`, không cài MySQL trên máy dev. Đây là
thay đổi tạm theo yêu cầu trực tiếp của user so với phiếu S-DB ban đầu.
S-DB cung cấp transaction, query và migration đánh số; không tạo bảng nghiệp vụ.
File mặc định nằm ở `var/flexmix.db` (đã bị gitignore), không commit dữ liệu.
SQLite bật foreign keys và synchronous FULL; kiểm transaction và rollback thật.
Các phép kiểm InnoDB và sync_binlog chưa áp dụng cho backend SQLite.

**Sẽ migrate sang MySQL sau**, khi C0 chốt hợp đồng và môi trường MySQL sẵn sàng.
Việc chuyển bao gồm schema/SQL theo dialect MySQL, chuyển dữ liệu có đối chiếu
số dòng và ràng buộc, rồi chạy lại test MySQL. Không coi SQLite là bằng chứng
đạt tiêu chí MySQL hay nghiệm thu trên Pi. Chưa viết công cụ chuyển dữ liệu khi
chưa có schema nghiệp vụ để chuyển.

## Phối hợp với C0

Lúc bắt đầu, repo có commit C0.1/C0.2 và G0.7 đạt với giả định N=10,
nhưng chưa có interfaces.md, db_ownership.md, settings.py, contracts/ hoặc
test_isolation.py. Theo chỉ đạo mới của user, hai agent được làm phần độc lập
của khối ngay, nhận cấu hình trực tiếp qua tham số và test bằng stub.
Các interface tạm được ghi trong báo cáo khối; chưa tự đánh C0 đã xong.

Claude giữ quyền sửa các file C0 và wiring. Codex không tạo hoặc ghi đè các file
đó trong lượt này. Khi C0 sẵn sàng, cần đối chiếu interface tạm và nối qua wiring.
S-NET không import spike hoặc module nghiệp vụ; CA/key không vào repo;
ngày hết hạn leaf bắt buộc truyền, LAN và hostname do vận hành cấu hình.

## Phạm vi ghi

- S-DB: `server/core/db/`, `server/manage.py`, `tests/s_db/`, bằng chứng S-DB.
- S-NET: `server/core/net/`, `deploy/server/`, `tests/s_net/`, bằng chứng S-NET.
- Mỗi agent làm nhánh/worktree riêng; không merge vào main.
- Codex đọc lại diff và chạy kiểm chung trước khi bàn giao cho operator.

Trạng thái khối vẫn là đang thực hiện/chờ review, không tự đánh dấu ✓.

## Tiếp quản phần Claude

Trong cùng lượt làm việc, user thông báo Claude hết token và giao Codex làm tiếp
phần Claude. Codex giữ nguyên các file C0.3 đang viết dở, kiểm bộ vector FM1,
hoàn thiện C0.4–C0.11 bằng agent thứ ba và tự làm UI-SHELL.
Các file C0/settings/wiring lúc này thuộc phạm vi được user giao tiếp quản.

G0.6 vẫn cần Pi thật; không thay số đo Windows thành số đo Pi. Q1 và các câu
hỏi vận hành chưa được user trả lời vẫn giữ trạng thái chờ. Hợp đồng mật mã
và các phần lệch R5 chỉ là bản đề xuất, không tự coi việc tiếp quản là duyệt Q1.
Các khối được làm và kiểm trên máy dev; bước ráp và triển khai thật chưa mở.

## Kết quả bàn giao

- S-DB commit `52f71ec` trên `khoi/s-db`; S-NET commit `feffd3c` trên
  `khoi/s-net`. Parent đã đọc diff và chép các file khối vào working tree chính
  để tiếp tục cùng C0/UI, không merge nhánh hoặc commit thay đổi sẵn có của user.
- Đã tạo `var/flexmix.db` bằng `python -m server.manage migrate`; hiện chỉ có
  sổ migration rỗng, chưa có bảng nghiệp vụ. DB và journal bị gitignore.
- Kiểm cuối `.venv/Scripts/python -m pytest tests spike -q`:
  **159 passed in 33.06s**, exit code 0. Bao gồm C0 isolation, SQLite thật,
  TLS thật và 10 poll/25 giây dưới flood trên Windows.
- `node tests/ui_shell/check_shell.cjs` đạt. Review độc lập phát hiện và đã sửa
  race whoami/401; test mới đỏ trước sửa và xanh sau sửa.
- C0.3 giữ nền Claude, đồng bộ body vector với C0.4 và sinh lại 37 vector;
  C0.4–C0.11 và UI-SHELL đã có file/code/kiểm. Hợp đồng vẫn là đề xuất;
  Q1, binding enroll và các quyết định vận hành chưa tự duyệt.
- Chưa nghiệm thu Pi/G0.6, mất điện, Linux/systemd/chrony, điện thoại/CSP thật
  hoặc ráp R1–R6. Unit service còn placeholder entrypoint vì wiring hiện là khung.

Bằng chứng chi tiết: `../bang_chung/C0.md`, `C0.3-CODEX.md`, `S-DB.md`,
`S-NET.md`, `UI-SHELL.md`. Chuyển schema và dữ liệu sang MySQL vẫn là bước sau.

## Sửa lỗi sau review độc lập · 08/10/2026

User giao reviewer độc lập kiểm lại, rồi yêu cầu Codex sửa các phát hiện:

- S-DB từ chối migration bổ sung có số không lớn hơn lịch sử đã commit.
- S-NET hủy cả poll đến muộn trong lúc shutdown; start mở lại cơ chế wait.
- Redirect giữ đúng bytes đường dẫn WSGI và dấu % qua percent-encoding.

Regression đỏ trước sửa, xanh sau sửa. Kiểm đầy đủ trên working tree chính:
`.venv/Scripts/python -m pytest tests spike -q` **161 passed in 34.11s**;
`node tests/ui_shell/check_shell.cjs` đạt. Hai reviewer kiểm lại phần sửa đạt,
chưa thấy lỗi còn sót đủ bằng chứng trong phạm vi này.
Các sửa này chưa nằm trong commit `52f71ec`/`feffd3c` của worktree ban đầu;
chưa commit/merge working tree chính. Không tác động `var/flexmix.db`.
Theo dõi kết quả tại [REVIEW_CODEX.md](../bang_chung/REVIEW_CODEX.md).
SQLite vẫn tạm thời; migrate MySQL và các gate nghiệm thu thật giữ nguyên.

Doc và `docs/server_plan.html` đã đồng bộ với kết quả này. Trang đọc tiến độ
từ bảng trong `index.md`; Q8 đã xử lý, còn 9 câu hỏi. Dựng/kiểm lại bằng
`node internal/plan/cong_cu/dung_trang_plan.js` và
`node internal/plan/cong_cu/check_trang_plan.cjs`.
