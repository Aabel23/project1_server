# C0.5 · Snapshot menu

**Đề xuất để review, chưa duyệt.** Codex tiếp quản Claude ngày 08/10/2026.
Nguồn: mục 7/N5/N6, cấu trúc version1.0/database/database.sql. M-MENU ghi
snapshot bất biến trong cùng transaction với menu_version; M-PUB chỉ đọc/phát;
A-APPLY xác thực và ghi dữ liệu máy, H-LOCAL dựng menu-data.js sau commit.

## Bao ngoài

`{server_epoch,version,sha256,snapshot,media}`. Epoch hex32, version integer >0,
sha256 hex64. Version cấp duy nhất toàn server để `menus.snapshot(version)`
không mơ hồ giữa các menu; có thể reset sau restore nhưng epoch bắt buộc đổi.
Snapshot không đổi: snapshot=null, media=[], target vẫn đầy đủ; agent không
ghi applied chỉ từ thông báo target. Giới hạn JSON bao ngoài 2 MiB, mỗi media
<=10 MiB, tổng media của một snapshot <=100 MiB (trần đề xuất, chưa đo Pi).
Không nhận URL/path từ server; agent dựng URL theo hash từ routing.

## Snapshot schema

Tất cả field dưới bắt buộc; nullable chỉ nơi ghi null. Không chứa tồn kho,
GPIO, ngưỡng nguyên liệu hay payload QR. Các chuỗi không NUL.

| Field | Kiểu / giới hạn / thứ tự |
|---|---|
| `menu_id` | integer >0 |
| `drinks` | <=999 món; sort `sku`, không trùng SKU/tên; mỗi mục schema dưới |
| `categories` | <=100 mục `{category_id:int>0,category_name:str 1..255,description:null hoặc str<=2048}`; sort category_id |
| `item_categories` | <=5000 mục `{sku,category_id}`; sort (sku,category_id); không trùng, mọi FK tồn tại |
| `glasses` | <=100 mục `{glass_id:int>0,glass_name:str 1..60,art:str 1..40,capacity_ml:null hoặc int>0,sort_order:int}`; sort glass_id |
| `drink_types` | <=100 mục `{drink_type_id:int>0,type_name:str 1..60,art:str 1..40,method:null hoặc str<=60,detail:null hoặc str<=200,sort_order:int}`; sort drink_type_id |
| `settings` | <=64 mục `{setting_key:str 1..64,setting_value:str<=255}`; sort setting_key; chỉ các key UI menu đã hỗ trợ, không ghi config tùy ý |

Mỗi drink: `sku` 1001..1999, `drink_name` 1..100, `price` decimal string hai
chữ số lẻ trong miền C0.4, `available`/`featured` bool, `image_sha256` null
hoặc hex64, `glass_id`/`drink_type_id` null hoặc id tồn tại, `garnish` null
hoặc <=120; `recipe` và `actions` là danh sách có thể rỗng.

- Recipe <=100 bước mỗi món: `{step_no:int 1..100,ingredient_id:int 1..24,
  target_gram:decimal>0,expected_name:str 1..100,
  expected_data_type:boolean|percentage|weight}`; sort `(step_no,ingredient_id)`;
  không trùng key. Không FK tới tồn kho máy: missing/mismatch loại **toàn bộ**
  recipe của món và ghi excluded, không thay công thức bằng nguyên liệu khác.
- Actions <=100 mỗi món: `{step_no:int 1..100,media_sha256:hex64,
  title_vi:str<=120,title_en:str<=120,detail_vi:str<=400,detail_en:str<=400,
  confirm_vi:str<=40,confirm_en:str<=40,cup_returns:bool}`; sort step_no,
  không trùng step. Dùng hash thay media_src đường dẫn; không action và recipe
  cùng step_no để giữ một thứ tự chạy rõ ràng (đề xuất cần đối chiếu máy Q6).
- media: <=1000 mục `{sha256:hex64,size:int 1..10485760}`, sort sha256,
  không trùng hash; đủ mọi image/action hash đang tham chiếu, không file dư.
  Agent tải vào thư mục tạm có trần tổng 100 MiB, cleanup khi thất bại.

## Hash ổn định

Sau khi validate và sort các list theo khóa trên, tính UTF-8 của
`json.dumps({"snapshot": snapshot, "media": media}, ensure_ascii=False,
sort_keys=True, separators=(",", ":"), allow_nan=False)`; sha256 là hex của
SHA256(bytes). Hash bao gồm manifest media để size cũng được ràng buộc.
Không hash sha256/server_epoch/version để tránh vòng lặp và đổi hash khi chỉ
đổi metadata. Unicode giữ nguyên, không normalize; phía phát chuẩn hóa đầu
vào một lần nếu muốn đổi quy tắc thì đổi hợp đồng/version. Decimal dùng chuỗi
chuẩn hai chữ số lẻ, không JSON float. Receiver tính lại hash trước khi ghi.

## Nhánh lỗi và ví dụ

Schema/hash/FK/trùng key sai: bỏ snapshot, giữ menu cũ, ACK ok=false nếu có
tuple hợp lệ; không ghi một phần. Media vượt size, hash sai, thiếu file hoặc
vượt trần tạm: dừng tải/xóa tạm. Transaction fail: rollback cả menu/applied.
Commit thành công nhưng helper publish fail: applied DB giữ phiên bản đã ghi,
retry publish; chưa ACK thành công cho tới publish được. Món thiếu nguyên
liệu là áp thành công có excluded, không lỗi transaction.

Hợp lệ (snapshot rỗng): `{"menu_id":1,"drinks":[],"categories":[],
"item_categories":[],"glasses":[],"drink_types":[],"settings":[]}` với
media=[] và hash được tính theo công thức trên.
Từ chối: price=NaN, SKU=2000, ingredient_id=25, hai SKU giống nhau,
category_id không tồn tại, image hash không có trong media, size vượt 10 MiB.
Món bỏ khỏi snapshot: available=0, giữ recipe 24 giờ rồi deleted_at theo N6.
