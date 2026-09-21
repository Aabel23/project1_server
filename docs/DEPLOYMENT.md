# Triển khai và vận hành

> Nguồn: [Kiến trúc đội máy FlexMix](../Kien_Truc_Doi_May.html), đề xuất bản 3 ngày 10/09/2026, tham chiếu `version1.0 @ ce17f05`. Tài liệu này được tách từ HTML; chưa đối chiếu mã nguồn ứng dụng và không xác nhận chức năng đã triển khai. “Yêu cầu” là mục tiêu trong đề xuất, “hiện trạng” là mô tả của nguồn, “đề xuất bổ sung” cần được duyệt. Các điểm chưa chốt nằm trong [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

## Cập nhật từ OWNER — DRAFT, 17/09/2026

DEC-005 (DRAFT): mở cửa 08:00–22:00 mỗi ngày; quản lý cửa hàng nhận cảnh báo; không có người trực ngoài giờ; cảnh báo ngoài giờ “xử lý trong ngày”. Chưa chốt múi giờ, SLA hoặc cách xử lý cảnh báo cuối ngày; không tự chuyển thành ngày làm việc kế tiếp.

DEC-009 (DRAFT): MID là số nguyên dương 1–999999, đã cấp không tái sử dụng kể cả decommission hoặc thay thế. Giới hạn QR còn mở tại Q-27; MID/UUID/machine_id/credential vẫn mở tại Q-12.

Theo DEC-006 (DRAFT), recipe được ghim tại thời điểm tạo ticket; recipe mới chỉ áp dụng cho ticket tạo sau khi version mới được publish, không đổi ticket đang tồn tại. C-17 vẫn giữ yêu cầu cửa sổ yên tĩnh cho thay đổi mã nguyên liệu; điều kiện chính xác và quy tắc xóa mềm vẫn mở tại Q-11. Pin recipe không bãi bỏ C-17 hoặc cho phép áp chúng ngay. Quan hệ publish tại Hub với apply tại máy offline và cách lưu recipe chưa chốt.

DEC-004 (DRAFT): thu tiền lúc in nhãn. Báo cáo used/completed_at chỉ phản ánh vé pha xong, không đủ đại diện tiền thực thu. OWNER chưa chọn schema thanh toán/hoàn tiền hoặc công thức báo cáo thay thế (Q-07, Q-17).

Các DEC được ghi tại [06_decisions.md](06_decisions.md), chưa ACCEPTED và chưa là căn cứ triển khai. Phần nguồn/hiện trạng được giữ để truy nguyên.

## Nền tảng

Giữ `deploy/install.sh` làm nền tảng cài đặt theo nguồn: 12 pha chạy lại được và pha `verify` chỉ đọc. Không có script ứng dụng trong workspace để liệt kê/kiểm chứng 12 pha; tài liệu này không cung cấp lệnh triển khai sản xuất giả định.

Máy: Pi 5, Ubuntu 24.04, MySQL cục bộ, backend và agent là hai systemd unit riêng. Hub: VM/MySQL 8/kho assets/Tailscale là phương án khuyến nghị, chờ Q-06; baseline stack đã được OWNER trả lời ở DEC-008 (DRAFT); chi tiết Q-24 còn mở.

## Lộ trình và cổng hoàn thành

Cột "Rủi ro cho tiệm" chép nguyên từ nguồn. Nguồn dùng cột này để giải thích vì sao pha 06 để cuối và vì sao pha 00/00b đúng kể cả khi không làm đội máy.

| Pha | Nội dung | Rủi ro cho tiệm (nguồn) | Cổng hoàn thành |
|---|---|---|---|
| 00 | Runtime khỏi git, machine profile, thời gian, schema ledger, backup | Không — và gỡ được hai rủi ro đang tồn tại | Máy có đường cập nhật an toàn và phục hồi thử thành công |
| 00b | Timeout chờ người, tiền kiểm món, kiểm tồn lúc issue, 409 lệch giá, từ chối món rút lịch sự | Thấp — mỗi việc lùi được riêng | Xử lý từng tình huống tại máy, không cần Hub |
| 01 | Registry, fleet.env, MID Hub cấp, Tailscale ACL/tag | Không — không đổi đường chạy nào | Không trùng MID, kết nối bảo trì đúng quyền |
| 02 | Agent chỉ đọc, beat/vé/lỗi/tồn/khe/backup; updated_at; giờ mở cửa | Gần như không — agent chỉ đọc | Đồng bộ lặp an toàn, đủ 17 cảnh báo |
| 03 | Danh mục chuẩn và đối chiếu có người duyệt | Không — vẫn chỉ đọc | So thực đơn hiện hữu, chưa ghi xuống máy |
| 04 | Snapshot, ghim máy, rollback catalogue | Có thật — bản chụp sai là đổi thực đơn | Giá/tên/ảnh/published theo nguồn; recipe ghim vào ticket theo DEC-006 (DRAFT); mã/xóa mềm còn chờ Q-11 |
| 05 | Tài khoản theo điểm, phân quyền, audit | Bị khóa ngoài. Luôn giữ `auth.py --set-password` chạy được tại máy | Offline login và khôi phục tại chỗ không bị khóa ngoài |
| 06 | Lệnh, chẩn đoán, release theo vòng | Cao nhất — bắt buộc có vòng máy thử | Chữ ký độc lập, bảo vệ API, chốt máy và tự rollback đã kiểm thử |

Năm việc của pha 00b, theo nguồn:

1. Hạn giờ cho các cổng chờ người: hết giờ thì tự hủy, trả vé, ghi "khách bỏ đi".
2. Tiền kiểm tính bán được khi lưu công thức: ≤ 24 mã lựa chọn, ≤ 12 lựa chọn mỗi đơn, mọi nguyên liệu PUMP đều có khe. Trường hợp nguyên liệu PUMP thiếu khai `gpio`: Q-29.
3. Kiểm tồn kho và trạng thái bán lúc phát hành vé, trong câu `INSERT ... SELECT` đang có.
4. Báo lại giá khi lệch: màn hình gửi kèm giá đang hiển thị, lệch thì 409.
5. Món bị rút khỏi thực đơn trả lời bằng lời từ chối lịch sự, **không phải một lỗi máy ghi vào `error_log`**. Quan hệ với cảnh báo "tỉ lệ pha hỏng": Q-28.

Có điểm cần làm rõ: pha 00 nói chưa có Hub nhưng cấp MID qua Hub là một trong năm lỗi chặn và nằm ở pha 01. Xem Q-21; không coi pha 00 tự nó đã giải quyết cấp phát tập trung.

## Tách trạng thái khỏi release

Nguồn liệt kê các đường dẫn cần rà soát: `configuration/pump_calib.json`, `configuration/calib_loadcell.json`, `configuration/display_mode.json`, `configuration/machine.py`, `store_gui/menu-data.js`, `order/current_recipe.json`, `scan/raw_qr.json`, `scan/qr_codes/index.json`.

Hai file hiệu chuẩn có thể dùng `.example` cho máy mới. Tách giá trị GPIO/I2C/máy in khỏi `machine.py` sang `/etc/flexmix/machine_profile.json`; giữ module đọc profile/fallback là hướng sửa trong nguồn. Không máy móc loại cả module mã nguồn khỏi release vì cách đếm file chưa nhất quán.

Không `git pull` trên cây đang bán hoặc dùng `reset --hard` để xóa runtime. Checkout tag vào thư mục release mới, trạng thái bền vững ở ngoài cây đó, rồi đổi symlink. Bỏ user/working directory hardcode trong systemd unit. Layout chính xác và cơ chế chuyển dữ liệu hiện hữu cần thiết kế trước khi sửa máy.

## Quy trình phát hành mục tiêu

1. Tạo tag đã ký bằng khóa ngoại tuyến; khai báo pha installer/migration cần chạy.
2. Hub gán bản cho một máy thử có thể đến trực tiếp.
3. Agent tải và xác minh chữ ký; kiểm máy rảnh và điều kiện thời gian/schema.
4. Backup trước `database.main update`, giữ ba bản gần nhất; lỗi backup phải được báo và chính sách chặn release cần chốt.
5. Chạy migration idempotent, ghi ledger sau từng thành công; checkout release mới, đổi symlink và restart theo quy trình đã kiểm tra.
6. Kiểm sức khỏe; nếu lỗi, lùi mã về release trước. Schema không lùi: migration phải thêm trước, xóa ở bản sau khi mã cũ không còn cần.
7. Chỉ mở vòng một điểm bán rồi toàn đội khi vòng trước khỏe đủ lâu. Bộ tiêu chí và thời gian theo dõi chưa chốt Q-20.

Rollback code không khôi phục được schema bị thay đổi không tương thích. Snapshot có rollback riêng; chỉ bản máy từng áp thành công, vẫn phải bảo vệ vé đang lưu hành.

## Thời gian, sao lưu và phục hồi

Nguồn đề xuất `systemd-timesyncd`, `After=time-sync.target` và `Wants=time-sync.target` cho backend. Đây là yêu cầu thứ tự khởi động trong nguồn; cần kiểm chứng cơ chế chờ đồng bộ thực sự và chính sách boot offline, không coi riêng hai directive là bằng chứng giờ đã đúng. Agent báo lệch >5 giây. DEC-007 (DRAFT, nguồn ô Q-22; mapping sang Q-21 là đề nghị biên tập, chờ OWNER xác nhận): không cho Machine nhận order khi khởi động offline và chưa sync clock. Không suy ra RTC bắt buộc hoặc cơ chế xác nhận sync; Q-21 vẫn còn phần mở, Q-22 chưa được trả lời. RTC chỉ là đề xuất nguồn, chưa có lựa chọn bắt buộc.

`flexmix-backup.timer` chạy hằng đêm: `mysqldump --single-transaction` cộng hiệu chuẩn và profile, giữ 7 gói trên ổ khác. Không tính bản cùng thẻ SD là bảo vệ mất thẻ. Khi có agent, gửi gói được phép lên Hub; Hub giữ N bản/máy và báo quá 36 giờ. Quy tắc lọc note/bí mật, mã hóa backup và tính nhất quán DB/files còn cần chốt.

Diễn tập phục hồi trên máy thử: phục hồi dữ liệu/profile/hiệu chuẩn, kiểm phần cứng thực tế, đối chiếu dữ liệu và khả năng bán. Máy thay thế nhận MID mới; lịch sử vẫn gắn MID cũ, không tự kích hoạt vé máy cũ. DEC-002 (DRAFT) chọn chấp nhận mất khóa QR; không đặt bước ký gửi Hub hoặc cất két thành lựa chọn đã duyệt. RPO/RTO chưa xác định.

## Vòng đời máy

Cấp registry/MID/auth key một lần → hiệu chuẩn tại chỗ, khai khe và backup đầu → đối chiếu danh mục có người duyệt nếu máy cũ → vận hành → thay thế theo quy trình phục hồi → thu hồi khóa/tag khi thanh lý, giữ lịch sử, không tái cấp MID.

## Danh mục 17 cảnh báo từ nguồn

Ngưỡng và mức dưới đây là đề xuất vận hành trong HTML, chưa được hiệu chỉnh theo lưu lượng thực tế. DEC-005 (DRAFT) ghi riêng cảnh báo ngoài giờ xử lý trong ngày; bảng không hứa có người trực ngoài giờ. Nếu chưa có người trực thì nguồn yêu cầu hạ “gọi ngay” thành “trong ngày”, không hứa có phản ứng tức thì.

| Cảnh báo | Ngưỡng | Mức | Hành động |
|---|---|---|---|
| Không bán trong giờ mở cửa | Không vé phát hành 2 giờ | Gọi ngay | Hỏi tiệm, kiểm kiosk/test/in/quét |
| Quên test mode | >30 phút | Gọi ngay | Kiểm tại chỗ, tắt test khi an toàn |
| Cổng chờ người kẹt | >10 phút không tương tác | Gọi ngay | Timeout tại máy hoặc cancel-current-order |
| Mất tín hiệu | Không beat 10 phút | Gọi ngay | Phân biệt điện/mạng/máy qua tiệm |
| MySQL không nối được | 2 phút | Gọi ngay | SSH kiểm dịch vụ và lưu trữ |
| Pha hỏng | >10% trong 20 đơn gần nhất | Gọi ngay | Xem step_label; tách hết nguyên liệu với bơm/cân. Từ chối món đã rút có tính vào đây không: Q-28 |
| Vé in_progress kẹt | >30 phút | Trong ngày | release-stranded chỉ lúc máy rảnh |
| Nguyên liệu thấp | amount < threshold_gram | Trong ngày | Châm nguyên liệu |
| Kiosk khởi động lại | >3 lần/giờ | Trong ngày | Kiểm RAM/V3D/độ phân giải |
| Lệch thời gian | >5 giây | Trong ngày | Kiểm NTP |
| CPU nóng | >80°C trong 10 phút | Trong ngày | Kiểm quạt/bụi |
| Snapshot áp lỗi | 2 lần liên tiếp | Trong ngày | Xem nhật ký áp, giữ menu cũ |
| Vé chưa từng quét | >15% vé trong ngày | Trong ngày | Kiểm in/quét/quy trình giao hàng; định nghĩa Q-17 |
| Backup cũ | >36 giờ | Trong ngày | Kiểm timer, ổ đích và upload |
| Đĩa trống thấp | <15% | Trong ngày | Kiểm journal, ảnh, clip; không xóa dữ liệu chưa gửi |
| Release tụt lại | Sau đội >2 bản | Tuần này | Kiểm máy offline/rollout |
| Schema tụt lại | Thiếu migration snapshot cần | Tuần này | Nâng schema qua release an toàn |

## Kiểm thử trước mở rộng

Chạy 20–30 máy giả dùng MySQL cùng schema, không GPIO: triển khai theo vòng, trùng serial, mất beat, mất ACK, offline rồi bắt kịp và lỗi snapshot. Máy thật dùng `test_gui`, `hx711_diag.py` cho phần cứng, cùng thử timeout, mất điện, rollback và khôi phục backup. Ngừng mở vòng nếu kiểm tra sức khỏe không đạt. Chưa có kết quả thực nghiệm trong bộ tài liệu này.
