# C0.6 · Lệnh và ledger

**Đề xuất để review, chưa duyệt.** Codex tiếp quản Claude ngày 08/10/2026.
M-CMD là nơi ghi machine_command; A-RUN ghi agent_ledger. M-MAC chỉ gọi API
M-CMD khi poll; M-ING nhận thay đổi bản sao qua API, không bị M-CMD ghi SQL.
Nguồn: thiết kế mục 7, L0/K1/K2/L1–L4 và `version1.0` validators/schema.

## Khung và fingerprint

Poll trả `{command_id,kind,args,fingerprint,ttl_ms}`. command_id hex32 ngẫu
nhiên; fingerprint hex64; ttl_ms integer >0 không vượt hạn kind. Trong DB/API
Python dùng bytes 16/32; args là object, args_bytes là UTF-8 JSON chuẩn
`sort_keys=True, separators=(",",":"), ensure_ascii=False, allow_nan=False`.
Không tự serialize lại args khác chuẩn khi fingerprint. Trần args_bytes 16 KiB.

`fingerprint = SHA256(Tuple("fm1-cmd", machine_id_bytes, kind_bytes, args_bytes))`.
machine_id_bytes uint32 big-endian (id 1..2^32-1) theo spike/fm1_ref.py và vector
C0.3, kind ASCII đúng enum;
Tuple/LP theo C0.3. command_id/epoch không vào fingerprint theo thiết kế.
Server lưu args_bytes và fingerprint một lần; agent canonicalize args theo đúng
quy tắc rồi so hash, không chạy nếu khác. Command trong vector C0.3 là minh họa
wire; định dạng uint32 vẫn là đề xuất C0.3 cần reviewer chốt trước S-FM1/M-CMD.

## Loại lệnh

| kind | args bắt buộc (không field khác) | Hạn mặc định / chống lặp |
|---|---|---|
| `ingredients.read` | `{}` | 5 s, đọc; không tác dụng phụ |
| `ledger.query` | `{command_id:hex32}` | 5 s, đọc; không có ledger trả found=false |
| `ingredient.refill` | `{ingredient_id:1..24,mode:fill|set_gram|add_gram,value:decimal}`; fill dùng value=null, set/add >=0 | 30 s; tác dụng+ledger done cùng transaction |
| `ingredient.refill_all` | `{}` | 30 s; như refill, thao tác mọi nguyên liệu trong một transaction; tên bổ sung từ route refill-all |
| `ingredient.save` | `{ingredient_id:1..24,ingredient_name:1..100,type:PUMP|MANUAL,data_type:boolean|percentage|weight,amount:decimal>=0,threshold_gram:decimal>=0,max_gram:null hoặc decimal>0,gpio:null hoặc [GP][0-9]+ <=8}` | 30 s; tên/id/data_type phải khớp sổ server, type/GPIO và uniqueness validate bằng hàm máy; ledger cùng transaction |
| `ingredient.delete` | `{ingredient_id:1..24}` | 30 s; FK/công thức đang dùng thì conflict, không force-delete; ledger cùng transaction |
| `ticket.set_status` | `{payload_hash:hex64,status:unused|used}` | 30 s; không sửa trạng thái locked/noqr_err, timestamp giữ nguyên; ledger cùng transaction |
| `error.delete` | `{error_ids:[int>0]}` <=200 id khác nhau | 30 s; chỉ DB máy này, ledger cùng transaction |
| `ticket.reprint` | `{payload_hash:hex64}` | 120 s; ledger claimed trước khi gọi helper |
| `order_mode.set` | `{printQR:bool,runDirect:bool}` ít nhất một true | 30 s; claimed trước gọi helper, ghi file nguyên tử |
| `display.apply` | `{mode:str ASCII ^[0-9]{2,5}x[0-9]{2,5}$}` <=11; phải mode màn hình hỗ trợ | 10 s; claimed trước helper; helper tự revert sau 20 s |
| `display.keep` | `{}` | 10 s; chỉ trial còn sống, helper lưu mode qua reboot |

Tiền/gram theo C0.4, không boolean thay integer; không shell string. Biên an
toàn khi offer đề xuất 2 s, `horizon` tính giây; chỉ offer khi còn hạn >horizon+2.
Lệnh đọc 5 s: nếu đã có lệnh thì dùng horizon=0 và trả ngay, không chờ đủ 25 s;
không làm quy tắc poll loại mọi lệnh đọc. TTL bắt đầu từ lúc nhận/mở response
và đo bằng BOOTTIME, không bằng giờ tường. Nếu hiệu chỉnh thời gian mạng cần
đổi quy tắc TTL thì review cùng A-NET, không mở rộng deadline khi retry.

## Trạng thái

Server có đúng bảy state:

- queued → offered khi đưa response ngay trước seal; queued → expired khi hết
  hạn chưa giao; queued → cancelled khi hủy/thu hồi.
- offered → offered: giao lại **cùng id/fingerprint** trong hạn.
- offered → done/failed chỉ bởi kết quả đúng máy+fingerprint.
- offered → unknown khi hết hạn chưa có kết quả hoặc epoch đổi/thu hồi.
- unknown → done/failed bởi kết quả muộn, unknown → expired khi ledger.query
  xác thực báo không tìm thấy. Không suy expired chỉ từ lỗi mạng.

Máy có bốn state logic `claimed`, `done`, `failed`, `acked`.
DB lưu claimed/done/failed và cột acked bool; acked vẫn giữ kết quả cũ.
claimed sau crash nghĩa chưa rõ, không chạy tác dụng ngoài DB lần nữa; báo
result state=unknown. DB effects và ledger done phải commit cùng transaction,
không có khoảng claimed riêng rồi mới ghi DB. Ngoại lệ rollback không để ledger
done còn mà tác dụng mất. Ledger chưa đối soát không bị cleanup dù quá 30 ngày.

`results[]` mỗi mục `{command_id,fingerprint,state,result}`, state = done,
failed hoặc unknown (unknown biểu thị ledger claimed sau crash), result object
<=16 KiB. Unknown không đổi thành failed; response `{accepted:[command_id]}`
chỉ gồm kết quả đã lưu bền đúng máy, đúng fingerprint, trạng thái offered/unknown
hoặc bản replay trùng đã lưu. Kết quả trùng cùng hash không tạo tác dụng mới;
kết quả trùng khác nội dung thì conflict, không ghi đè done/failed.
Done/failed chỉ sang acked sau response mở được xác nhận id; claimed unknown
vẫn phải được giữ lại để đối soát. Q4 (N giờ) và Q10 (route replay) còn chờ.

## Lỗi và ví dụ

Body/args sai → bad_request; không có vé/nguyên liệu → not_found; cùng id khác
fingerprint → conflict; offline hoặc epoch form cũ → HTTP 409 trước tạo lệnh.
request_key unique theo người tạo: cùng key+cùng body trả lệnh cũ, khác body
409. Commit rồi mới wake.notify; không tạo id mới để retry mất response.
Q3 xác thực lại khi used→unused còn chờ, chưa mở thao tác đó bằng suy đoán.

Hợp lệ: `order_mode.set` args `{"printQR":true,"runDirect":false}`;
`ingredient.refill` args `{"ingredient_id":2,"mode":"add_gram","value":"100.00"}`.
Từ chối: cả hai mode false, `ingredient_id:25`, amount âm, kind lạ,
fingerprint khác cho cùng id, result của máy A gửi id thuộc máy B.
