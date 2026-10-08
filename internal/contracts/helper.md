# C0.7 · Ngữ pháp helper kiosk

**Đề xuất để review, chưa duyệt.** Codex tiếp quản Claude ngày 08/10/2026.
H-LOCAL ghi cấu hình kiosk/màn hình/in; A-APPLY và A-RUN chỉ gọi client.
Q6 chưa chốt nhánh máy; đây là hợp đồng, chưa sửa/cài helper lên Pi.

## Framing và grammar

Unix socket cục bộ; SO_PEERCRED chỉ uid flexmix-agent được kết nối. Một request
một connection: đúng một dòng ASCII LF, <=256 byte kể cả LF, không CR/NUL,
không khoảng trắng đầu/cuối, không dữ liệu sau LF. Deadline đọc đề xuất 5 s.
Các từ cách nhau đúng một space; không quote, escape, shell, đường dẫn, URL.

```text
display apply <mode>
display keep
display revert
display status
order-mode set <printQR> <runDirect>
menu publish
print <hex64>
```

mode đúng `[0-9]{2,5}x[0-9]{2,5}` và phải có trong modes do xrandr báo; helper
gọi executable với argv riêng, không shell=True. printQR/runDirect là `0` hoặc
`1`, ít nhất một bằng 1. hex64 đúng lowercase hash payload của vé, helper tự
lookup vé từ DB máy, không nhận payload QR/path từ agent.

Apply nhớ mode cũ và trial trong helper, timer BOOTTIME 20 s tự revert kể cả
agent chết. Apply khi trial còn sống → conflict, không chồng timer. Keep chỉ
trial còn hạn, ghi mode bền qua reboot trước trả success. Revert không trial
là success vô hại; status chỉ đọc. Menu publish gọi publish_menu() hiện có
sau transaction A-APPLY, không ghi SQL menu bằng helper. Order-mode ghi file
nguyên tử qua hàm hiện có, không làm POS phụ thuộc server.

## Output và mã lỗi

Đúng một dòng JSON UTF-8 kết thúc LF, <=4 KiB, object không key trùng/NaN,
đúng `{ok,code,data}`; ok bool, code enum, data object. Không trace/backtrace,
stderr, đường dẫn nhạy cảm hay output xrandr thô trong reply. Agent coi output
là không tin cậy, parse schema trước khi dùng. Helper không nhận lệnh tiếp trên
cùng connection. UID sai đóng connection, không cấp thông tin.

| code | ok | data |
|---|---|---|
| `ok` | true | schema theo loại dưới |
| `bad_request` | false | `{}`; grammar/type/framing sai |
| `unsupported_mode` | false | `{}`; đúng grammar nhưng không mode màn hình |
| `not_found` | false | `{}`; vé hash không có |
| `conflict` | false | `{}`; trial khác đang chạy hoặc keep đã quá hạn |
| `io_error` | false | `{}`; không ghi file/in/xrandr/publish được |

Display apply/status/keep/revert data:
`{mode:str,previous:null|str,trial:bool,remaining_ms:int 0..20000}`.
Order-mode data `{printQR:bool,runDirect:bool}`;
menu publish data `{published:true}`; print data `{printed:true}`.
Response timeout/disconnect/JSON sai sau claimed → A-RUN báo unknown, **không
tự in lại**. Menu publish có thể retry vì dựng file vô hại; helper failure
không xóa transaction menu đã commit.

Hợp lệ: `display apply 1280x800\n`, `order-mode set 1 0\n`, `menu publish\n`.
Từ chối: `order-mode set 0 0\n`, `display apply 1280x800;reboot\n`,
`print ../../x\n`, `print` hash uppercase, thêm dòng lệnh thứ hai, uid kiosk.
