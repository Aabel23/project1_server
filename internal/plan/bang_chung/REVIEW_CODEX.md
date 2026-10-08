# Review độc lập các khối đã thực thi

Ngày 08/10/2026 (Bangkok). User giao agent review lại các khối.
Ba reviewer mới kiểm S-DB, S-NET và C0/UI-SHELL; không giao lại cho coder cũ.
Parent tái hiện riêng cả ba phát hiện trên file hiện có trong working tree chính.
Lượt review ban đầu chỉ đọc code. User sau đó yêu cầu sửa; kết quả sửa lỗi
và kiểm lại ghi ở phần cuối, giữ bằng chứng lỗi ban đầu bên dưới.

## Kết quả

| Khối | Kết luận |
|---|---|
| S-DB SQLite tạm | Đã sửa P2 thứ tự migration bổ sung; hồi quy và review lại đạt |
| S-NET | Đã sửa P2 shutdown và P3 redirect; hồi quy và review lại đạt |
| C0 và vector FM1/spike | Không có lỗi mới đủ bằng chứng; hợp đồng vẫn đề xuất/chờ các quyết định đã ghi |
| UI-SHELL | Không có lỗi mới đủ bằng chứng trong code và test stub; chưa nghiệm thu trình duyệt/backend thật |

P2 = cần sửa trước khi nghiệm thu khối; P3 = lỗi phạm vi hẹp cần sửa.
Không coi các phép kiểm hiện có xanh là chứng minh không còn lỗi.

## P2 · Migration bổ sung đứng trước lịch sử đã áp

Vị trí: `server/core/db/migrations.py:88`.
Runner bỏ qua migration đã áp rồi chạy mọi số còn thiếu, không kiểm số mới
có thấp hơn lịch sử đã commit. Một nhánh mang số cũ có thể chạy sai thứ tự.

Parent tái hiện bằng SQLite thật trong thư mục tạm, không dùng `var/flexmix.db`:

1. `0001_base.sql` tạo config với value=0; `0003_last.sql` đặt value=3.
2. Áp vào DB hiện có; sau đó thêm `0002_middle.sql` đặt value=2.
3. Chạy lại DB đó, rồi áp cùng ba file vào DB mới.

```text
first: [1, 3]
upgrade: [2]
fresh: [1, 2, 3]
existing: [{'value': 2}]
fresh: [{'value': 3}]
same_journal: True
```

Cùng source và journal nhưng kết quả DB khác nhau. DB hiện tại chưa có
migration nghiệp vụ, nên chưa có bằng chứng dữ liệu dự án đã bị sai.
Sửa tối thiểu: kiểm mọi migration chưa áp trước thực thi; số <= max(applied)
thì từ chối và yêu cầu cấp số mới. Không tự rollback dữ liệu đã commit.
Check bổ sung phải bắt trường hợp trên và giữ nguyên value=3/journal [1,3]
khi migration sai thứ tự bị từ chối.

## P2 · Poll mới bỏ lỡ tín hiệu shutdown

Vị trí: `server/core/net/main.py:155`, `server/core/net/wake.py:20`.
`stop()` cancel waiter hiện tại, sau đó dừng HTTP → agent → admin.
Trong lúc HTTP đang drain, agent vẫn nhận poll mới. Waiter mới lấy generation
shutdown đã tăng và chờ hết timeout, nên không nhận tín hiệu cancel trước đó.

Tái hiện với cert tạm và server loopback, không cài service:

- NetSettings shutdown_timeout=0.5 s, timeout=2 s.
- Client HTTP gửi header chưa kết thúc để giữ worker HTTP trong lúc drain.
- Mở TLS tới agent; sau khi cancel_waiters thực sự chạy, gửi GET /poll.
- Handler gọi wake.wait(machine_id,3). Hook cancel chỉ phát Event để xác định
  thứ tự, không trì hoãn stop hoặc thay hành vi cancel.

```text
reviewer: stop_seconds = 3.083; poll = SSLError
parent:   stop_seconds = 3.0494266; poll = SSLError
```

Poll bắt đầu trong lúc dừng không bị cancel, làm tắt server chậm và response
bị cắt. Đây là race nhận waiter mới, không phải khẳng định shutdown_timeout
có thể ngắt bất kỳ handler Python nào.
Sửa tối thiểu: đánh dấu đang dừng trước cancellation, ngăn nhận request mới
và cho waiter tới trong giai đoạn drain kết thúc ngay; reset lifecycle khi start.
Check thêm: poll tới sau cancel không chờ hết 3 s và không để lại worker/poll.

## P3 · Redirect thay đổi path percent-encode

Vị trí: `server/core/net/main.py:104`.
`quote(PATH_INFO, safe="/%:@")` encode chuỗi WSGI bằng UTF-8 một lần nữa,
đồng thời giữ nguyên dấu % đã decode. Parent gửi HTTP thật và nhận:

```text
/caf%C3%A9  -> https://127.0.0.1:<port>/caf%C3%83%C2%A9
/a%252Fb    -> https://127.0.0.1:<port>/a%2Fb
```

Sau redirect client có thể tới path khác; namespace API hiện phần lớn ASCII,
nên xếp P3. Sửa tối thiểu: dùng quote_from_bytes với bytes WSGI Latin-1 và
không giữ % trong safe của path. QUERY_STRING là raw nên xử lý riêng.
Check thêm: hai URL trên giữ nguyên ý nghĩa path qua redirect.

## Phép kiểm độc lập

Các suite có phần giao nhau; không cộng số test thành một tổng mới.

| Reviewer | Lệnh | Kết quả |
|---|---|---|
| S-DB | `.venv/Scripts/python -m pytest tests/s_db tests/c0 -q` | 111 passed in 3.00s |
| S-NET | `.venv/Scripts/python -m pytest tests/s_net tests/c0 -q -k 'not longpoll_25s'` | 109 passed, 1 deselected in 4.39s |
| C0/UI | `.venv/Scripts/python -m pytest tests/c0 spike -q` | 120 passed in 4.43s |
| C0/UI | `node tests/ui_shell/check_shell.cjs` | đạt, exit 0 |

Phép tái hiện parent chạy bằng `.venv/Scripts/python -`, exit 0; dùng thư mục
tạm ngoài repo, SQLite tạm và socket loopback. Không ghi vào DB vận hành.
Không chạy lại flood 25 s vì phát hiện mới không liên quan cách ly hai pool;
bằng chứng flood trước đó vẫn nằm trong S-NET.md.

## Giới hạn giữ nguyên

SQLite tạm đã được user cho phép; thiếu MySQL không tính là lỗi mới.
MySQL/InnoDB và chuyển dữ liệu sẽ kiểm khi migrate. G0.6 cần Pi thật.
Q1, binding enroll và các câu hỏi vận hành chưa chốt vẫn là gate đã công bố.
UI dùng stub DOM/API; CSP/trình duyệt/backend tài khoản thật chờ R1.
Wiring là khung; chrony/systemd là mẫu chưa chạy Linux/Pi/LAN/reboot thật.
Vector FM1 kiểm spike, chưa chứng minh S-FM1/A-NET production hoặc claim/ledger.

Không đánh ✓ khối còn lỗi hoặc thiếu điều kiện nghiệm thu. Sau khi sửa,
coder thêm regression cho các ca trên rồi reviewer kiểm lại phần bị ảnh hưởng.

## Sửa lỗi theo yêu cầu tiếp của user · 08/10/2026

Parent sửa trong working tree chính, không thay các commit bàn giao ban đầu
trên nhánh/worktree S-DB/S-NET. Không sửa DB vận hành hoặc phần code máy có
thay đổi sẵn của user.

- S-DB kiểm số mới trước thực thi: migration chưa áp phải lớn hơn mọi số đã
  commit. Lỗi số cũ giữ nguyên dữ liệu và journal, kể cả khi có migration số mới
  khác trong cùng đợt. Sau khi cấp lại số lớn hơn, DB mới và DB nâng cấp khớp.
- S-NET giữ trạng thái dừng trong Wake: waiter hiện tại bị cancel, waiter đến
  trong lúc drain trả False ngay. NetServer.start mở lại wait trước khi chạy
  listener; generation cancel cũ vẫn giữ để không bỏ lỡ việc hủy waiter cũ.
  Không cố ngắt handler Python tùy ý; các handler vẫn cần tuân thủ lifecycle.
- Redirect dùng bytes Latin-1 của PATH_INFO với quote_from_bytes, không giữ
  dấu % đã decode. QUERY_STRING raw vẫn xử lý riêng và không bị decode thêm.

Regression nằm trong `tests/s_db/test_db.py` và `tests/s_net/test_net.py`.
Kiểm shutdown dùng agent TLS/server thật, giữ giai đoạn HTTP drain bằng Event;
poll đến sau cancel hoàn tất trong timeout client 1 s, không còn worker/poll.
Khởi động lại cùng server kiểm poll chờ và nhận notify bình thường.
Redirect kiểm `/caf%C3%A9`, `/a%252Fb` và path/query chứa dấu %.

```text
Trước sửa:
pytest tests/s_db/test_db.py tests/s_net/test_net.py -q
  -k 'migration_bo_sung or shutdown_cancels or tls_isolation_http'
3 failed, 38 deselected in 5.46s

Sau sửa, cùng lệnh:
3 passed, 38 deselected in 1.83s

.venv/Scripts/python -m pytest tests spike -q
161 passed in 34.11s

node tests/ui_shell/check_shell.cjs
đạt, exit 0
```

Hai reviewer cũ kiểm lại phần sửa S-DB/S-NET, chỉ đọc code, không thấy lỗi còn
sót đủ bằng chứng trong phạm vi sửa. Reviewer DB chạy độc lập
`.venv/Scripts/python -m pytest tests/s_db -q`: **21 passed in 0.83s**.
Reviewer NET chạy `.venv/Scripts/python -m pytest tests/s_net/test_net.py -q
-k "tls_isolation_http_and_safe_logs or shutdown or wake_isolation"`:
**4 passed, 16 deselected in 2.39s**. Các suite có phần giao nhau, không cộng
các số test này vào tổng 161.
Các giới hạn nghiệm thu MySQL, Linux/Pi, wiring/R1 và Q1 vẫn giữ nguyên.
