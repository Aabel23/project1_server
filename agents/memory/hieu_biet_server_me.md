# Server mẹ FlexMix: bối cảnh để tiếp tục làm việc

Cập nhật 08/10/2026. Thay bản tóm tắt 07/10 còn chứa đề xuất HTTP/HMAC,
waitress, routing cũ và “chưa có git”. Tiến độ chi tiết đọc từ plan, không suy
ra trạng thái hiện tại từ hồ sơ architect cũ.

## Mục tiêu và ranh giới

- Server mẹ quản lý nhiều máy trong LAN, thay phần quản trị `admin_gui` trên
  từng máy. Giữ chức năng quản lý hiện có; thư viện món dùng chung, menu riêng
  và máy được gán menu theo thiết kế bản 2.
- Máy offline vẫn bán với bản menu cuối đã áp. Khi server sập, máy tiếp tục
  bán; thao tác quản trị từ xa cần server/kết nối.
- Nguyên liệu/tồn kho thực nằm ở máy. Server giữ bản đệm để xem và gửi lệnh
  xuống; không biến bản đệm thành nguồn dữ liệu chính.
- `version1.0/admin_gui`, `store_gui`, `database/admin_functions` là nguồn
  tham chiếu hành vi. Nhánh sửa phía máy còn chờ Q6, không tự chọn version1.0
  hay version1.1. Dự án này không phải server của app Android khác.

## Hướng đã triển khai hoặc đang theo plan

- Python/Flask, cheroot; TLS 1.3 với cổng quản trị và agent/pool riêng.
  CA nội bộ là phương án LAN hiện tại, root giữ offline, key/cert ngoài repo.
  User hỏi về CA bên thứ ba chưa đồng nghĩa đã chọn chuyển sang public CA.
- User cho phép **SQLite `.db` tạm**, sẽ migrate MySQL sau. Dùng sqlite3,
  SQL tham số hóa, transaction và migration đánh số. Số bổ sung phải lớn hơn
  mọi số đã áp. MySQL/InnoDB và chuyển dữ liệu phải kiểm khi migrate.
- Máy chủ động kết nối tới server; long-poll nhận lệnh/thay đổi menu. Không
  tự mở cổng nhận điều khiển vào máy. Notify không phải hàng đợi lệnh; trạng
  thái bền nằm trong DB.
- FM1/HPKE/Ed25519/AES-GCM đã có spike/vector và hợp đồng đề xuất. Q1,
  binding enroll và review mật mã chưa được duyệt; chưa suy ra middleware
  S-FM1/A-NET production hoặc claim/high-water đã chạy thật.
- UI dùng lại HTML/JS/CSS vanilla, cookie phiên, chữ an toàn và hủy request
  khi 401. Backend tài khoản/CSP và nghiệm thu trình duyệt thuộc bước ráp.
- Mỗi khối cô lập; `server/contracts/` chứa hợp đồng dạng code;
  `server/wiring.py` là điểm nối duy nhất, hiện còn khung. Không import ruột
  module khác. Khối DB không tự định nghĩa/ghi bảng nghiệp vụ của module.

## Nguồn đọc đúng lúc

- [Cách phối hợp](cach_phoi_hop.md): quy trình user/Codex, agent, kiểm và bàn giao.
- [Plan/tiến độ](../../internal/plan/index.md) và
  [phân việc](../../internal/plan/giao_viec/README.md): đọc đầu phiên.
- [Thiết kế bản 2](../../docs/server_architect.html), `internal/contracts/`
  và `server/config/routing.py`: đối chiếu khi sửa luồng/hợp đồng.
- [Bằng chứng review](../../internal/plan/bang_chung/REVIEW_CODEX.md) và
  [ghi chú Claude](../../internal/plan/giao_viec/CODEX_SQLITE_THONG_BAO_CLAUDE.md):
  kết quả thực thi/sửa lỗi, việc chưa kiểm, quyết định tạm và bàn giao.
- [Quy ước sơ đồ](quy_uoc_so_do.md): đọc khi dựng sơ đồ. `phuong_an_kien_truc.md`
  và `crypto_*.md` là lịch sử đề xuất/phản biện; không dùng để ghi đè plan,
  chỉ đạo mới hoặc hợp đồng đã cập nhật.

Không đánh ✓ chỉ vì test dev xanh. Pi/G0.6, Linux/chrony/systemd/LAN,
trình duyệt/backend và R1–R6 cần bằng chứng riêng; các câu hỏi còn chờ xem plan.
