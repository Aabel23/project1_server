# Đặc tả bảo mật

> Nguồn: [Kiến trúc đội máy FlexMix](../Kien_Truc_Doi_May.html), đề xuất bản 3 ngày 10/09/2026, tham chiếu `version1.0 @ ce17f05`. Tài liệu này được tách từ HTML; chưa đối chiếu mã nguồn ứng dụng và không xác nhận chức năng đã triển khai. “Yêu cầu” là mục tiêu trong đề xuất, “hiện trạng” là mô tả của nguồn, “đề xuất bổ sung” cần được duyệt. Các điểm chưa chốt nằm trong [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

## Cập nhật từ OWNER — DRAFT, 17/09/2026

DEC-009 (DRAFT): MID là số nguyên dương 1–999999, đã cấp không tái sử dụng kể cả decommission hoặc thay thế. Giới hạn QR còn mở tại Q-27; MID/UUID/machine_id/credential vẫn mở tại Q-12.

DEC-007 (DRAFT, nguồn ô Q-22; mapping sang Q-21 là đề nghị biên tập, chờ OWNER xác nhận): không cho Machine nhận order khi khởi động offline và chưa sync clock. Không suy ra RTC bắt buộc hoặc cơ chế xác nhận sync; Q-21 vẫn còn phần mở, Q-22 chưa được trả lời.

Q-09 chỉ ghi “không” cho câu hỏi ghép: chưa xác định phủ định nào, không suy ra quyền đổi giá/công thức hay bỏ hai người duyệt.

Các DEC được ghi tại [06_decisions.md](06_decisions.md), chưa ACCEPTED và chưa là căn cứ triển khai. Phần nguồn/hiện trạng được giữ để truy nguyên.

## Mục tiêu và ranh giới tin cậy

Hub bị mất kết nối không làm mất khả năng bán khi phụ thuộc cục bộ đáp ứng điều kiện vận hành; trường hợp boot offline chưa sync clock xem DEC-007 DRAFT ở trên. Hub có quyền sửa danh mục, giá, tài khoản và gọi một tập lệnh; quyền đó vẫn có thể gây thiệt hại kinh doanh. Không mô tả Hub bị chiếm quyền là vô hại.

Chỉ khi máy kiểm chữ ký release độc lập, API cục bộ được bảo vệ và lệnh phần cứng có chốt tại chỗ thì Hub không thể tùy ý đưa mã chưa được tin cậy xuống máy. Chữ ký không ngăn Hub chọn lại một bản cũ đã ký hoặc lạm dụng lệnh hợp lệ (Q-19).

## Danh tính và khóa

| Tài sản | Nơi giữ/quy tắc |
|---|---|
| MID | Hub cấp duy nhất, không dùng lại |
| UUID và cặp khóa Ed25519 thiết bị | `/etc/flexmix/fleet.env`, quyền 0600; ký request |
| Khóa công khai thiết bị | Hub dùng xác thực, không tin địa chỉ IP làm danh tính |
| `QRPROTO_KEY` | Riêng mỗi máy, 64 hex theo nguồn; không gửi Hub |
| Khóa phiên trong `admin_account.json` | Riêng máy; token không dùng chéo máy |
| Khóa ký release riêng | Ngoại tuyến, Hub không giữ và không tự ký release |
| Khóa xác minh release | Cài sẵn tại máy; nguồn đặt trong `fleet.env` |
| Khóa ký snapshot, chứng thư mTLS | Bản chụp có trường `signature` nhưng nguồn không nêu ai giữ khóa ký; vòng đời chưa định nghĩa (Q-15, Q-26) |

Khóa thiết bị, khóa QR, khóa ký phiên và khóa ký release có mục đích khác nhau, không dùng chung theo suy đoán.

**Phạm vi của invariant "Hub không giữ khóa ký":** nguồn phát biểu cho **khóa ký bản phát hành**. Nguồn không nói invariant này có áp cho khóa ký snapshot hay không; đây là câu hỏi mở Q-26, không được suy ra từ cách nói tắt. Khi thanh lý: thu hồi danh tính/khóa thiết bị, gỡ tag Tailscale, giữ lịch sử và MID cũ.

## Mạng và API tại máy

- Backend chỉ nghe loopback và địa chỉ Tailscale theo thiết kế nguồn, không bind Wi-Fi tiệm.
- Agent chủ động kết nối ra; đồng bộ không đòi mở cổng mới vào máy. Bảo trì thủ công qua Tailscale SSH và ACL.
- HTTPS qua Tailscale và mTLS được nêu trong sơ đồ; request còn được ký Ed25519. Đây là mô tả thiết kế nguồn, không phải quyết định OWNER mới: cách sử dụng/kết hợp HTTPS/Tailscale/mTLS/Ed25519, chống phát lại, xoay/thu hồi khóa và cấp chứng thư vẫn OPEN tại Q-15. DEC-008 chọn Nginx không quyết định terminate mTLS hay tin metadata proxy.
- `served_paths.py` giữ allowlist file phục vụ; không phục vụ tùy ý file cấu hình/bí mật.
- Theo nguồn, `/api/admin/*` có `require_login()` nhưng ticket/print/start/relay/test còn thiếu xác thực trong ranh giới tailnet. Trước pha 06 phải chọn chỉ loopback hoặc token riêng của máy cho các API này.
- Hardware test luôn cần test mode được bật tại panel 15; không cho qua vì `run_flow` không chạy. Backend chết không phải lý do bỏ chốt.
- Bổ sung giới hạn thử sai đăng nhập khi mở rộng tailnet; ngưỡng chưa định nghĩa.

Tắt hết hạn khóa nút cho tag máy là hướng nguồn đề xuất. Auth key dùng đăng ký một lần và khóa nút đang vận hành là hai vòng đời cần cấu hình riêng, không mặc định một khóa sống mãi giải quyết cả hai.

## Phân quyền và phiên đăng nhập

Ba vai tại tiệm: chủ, quản lý, nhân viên. Thêm vai vận hành đội chỉ có ở Hub. Nguồn chưa có ma trận quyền chi tiết cho từng lệnh hoặc quy tắc hai người duyệt đổi giá/công thức (Q-09).

Hub nhân bản `admin_user`, `role_permission` đúng phạm vi điểm bán; PBKDF2 hash/salt/rounds truyền nguyên trạng, không truyền mật khẩu thô. Máy đăng nhập offline từ bản sao. `sessions_valid_from` được cập nhật khi đổi mật khẩu/khóa tài khoản; chỉ có hiệu lực tại máy sau lần đồng bộ tiếp theo, rồi request sau đó bị vô hiệu phiên theo nguồn. Không hứa thu hồi tức thì cho máy offline.

Quyền endpoint do `PATH_AREA`/mã máy chủ quyết định. Luôn giữ đường khôi phục tại chỗ `auth.py --set-password` theo lộ trình nguồn, đồng thời cần chốt phạm vi quyền vận hành cho đường này.

## Release, snapshot và lệnh

Agent xác minh chữ ký tag bằng khóa tin cậy cài trước, trước khi chạy installer/migration/mã tải về. Hub chỉ chọn bản đã ký. Không đồng nhất chữ ký release với chữ ký snapshot chưa được đặc tả.

Lệnh có ID, người yêu cầu, hạn dùng; chốt bận/rảnh và test mode kiểm tại máy, không chỉ trên UI Hub. Ghi audit cho hủy đơn và thao tác nhạy cảm. Restart/apply-release bị từ chối khi đang pha; display mode giữ tự hoàn tác 20 giây.

**Đề xuất bổ sung:** kiểm đường dẫn asset để không thoát thư mục đích; giới hạn kích thước gói; chỉ cho agent quyền hệ thống đủ cho các lệnh allowlist. Nguồn chưa định nghĩa sandbox agent, quyền sudo hay chính sách chống rollback về release có lỗ hổng.

## Dữ liệu riêng tư, backup và diagnostics

`order_ticket.note` tối đa 200 ký tự là dữ liệu khách tự nhập, không đưa vào telemetry thường lệ. Chỉ lấy cho một khiếu nại cụ thể bằng diagnostics có chủ đích và audit. Log chẩn đoán có thể chứa dữ liệu nhạy cảm, cần giới hạn dung lượng và lọc.

Không đưa `QRPROTO_KEY` hay `admin_account.json` vào gói gửi Hub. Sao lưu đầy đủ DB có thể chứa `note`, hash tài khoản hoặc dữ liệu phiên: nguồn chưa giải quyết mâu thuẫn này. Cần chốt gói phục hồi tại chỗ, gói được phép gửi Hub, mã hóa và quyền đọc ở Q-16; chưa thể tuyên bố tuân thủ chỉ nhờ loại `note` khỏi event payload.

DEC-002 (DRAFT): OWNER chọn chấp nhận mất khóa QR. Ký gửi Hub và cất két ngoại tuyến là các phương án nguồn từng nêu, không phải lựa chọn OWNER đã chọn. Không có bản khóa thì không khôi phục vé cũ; máy thay thế MID mới cũng cần quy trình riêng ngay cả khi còn khóa ngoại tuyến.

## Audit và xử lý sự cố

Audit cần người, thời gian, endpoint, đối tượng, trước/sau; móc `PATH_AREA` cho thao tác tại máy và gửi Hub. Thao tác tại Hub cũng cần ghi vết (đề xuất bổ sung; chủ sở hữu và tách khóa tại Q-30); không ghi mật khẩu, private key hoặc token thô vào trước/sau.

Khi nghi Hub bị chiếm quyền: cắt đồng bộ/điều khiển từ Hub, giữ máy phục vụ cục bộ nếu vẫn an toàn; đối chiếu release, snapshot và audit trước khi nối lại. Quy trình thay khóa, khôi phục Hub, bảo vệ backup và người có quyền quyết định cần chốt. Đây là kế hoạch mục tiêu, chưa phải runbook đã diễn tập.
