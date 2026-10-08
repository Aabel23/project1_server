# C0.10/C0.11 · Mối nối và cấu hình

**Đề xuất để review, chưa duyệt.** Codex tiếp quản Claude ngày 08/10/2026.
`server/contracts/interfaces.py` chỉ Protocol, dataclass, alias và exception.
`server/wiring.py` chỉ khung thứ tự ráp, chưa chạy app/module nghiệp vụ.
Không import implementation của khối khác để lấy type; dùng contracts này.

## Data và lỗi chung

Body = dict[str,object]; Status enum theo C0.3; Handler nhận `(machine_id:int,
body:Body)` trả `(Status,Body)`. Dataclass không validate: boundary nhận dữ
liệu phải validate C0.4–C0.7 trước xây type. Trong Python epoch/id command là
bytes16, fingerprint bytes32, public key Ed25519/X25519 bytes32, hash hex64.
User: user_id>0, role owner/manager/staff, active bool, revoked_at Unix giây,
areas frozenset tên khu vực. Credential: kid C0.3, machine_id>0, alg=Ed25519,
status active/retiring/revoked, generation>0, hw_issued_at milliseconds >=0,
last_revoked_notice_at null hoặc milliseconds >=0. MenuTarget có server_epoch bytes16,
version>0, sha256 hex64; Snapshot chứa target, snapshot object và media tuple.
Command chứa command_id,kind,args,args_bytes,fingerprint,ttl_ms theo C0.6.

ContractError nhánh chung; NotFound → not_found (API admin HTTP404), Conflict →
conflict/HTTP409, Forbidden → HTTP403, EpochChanged → epoch_changed/HTTP409.
ValueError dữ liệu không hợp lệ → bad_request/HTTP400. Agent errors sau claim
đều được seal; trước claim theo C0.3. Exception DB/OS không được nuốt thành
success: rollback hoặc trả error; log metadata, không body/key/cookie.

## Signatures

| Khối cung cấp → dùng | Protocol / chữ ký | Kết quả và nhánh lỗi |
|---|---|---|
| S-DB → các khối | Database.transaction(*,immediate:bool=False) -> ContextManager[sqlite3.Connection]; query(sql:str,parameters:tuple=()) -> list[dict] | transaction commit/rollback; sqlite3.Error/OSError; query thực thi một câu SQL tham số (ghi không RETURNING trả []). Constructor thực tế Database(path,*,timeout=10) |
| S-NET → M-MAC/M-MENU/M-CMD | Wake.notify(machine_id:int)->None; wait(machine_id:int,timeout:float)->bool | true khi signal tới waiter hiện tại, false timeout/cancel; id>0, timeout>=0 hữu hạn; không giữ signal cho waiter tương lai. M-MAC kiểm DB trước/sau chờ và mỗi 2 s theo thiết kế M3, Wake không tự query/poll DB |
| S-SECA → modules | Security.require(area:str,machine_id:int|None=None)->Decorator; require_stepup()->Decorator | đọc user hiện tại, Forbidden hoặc chưa auth HTTP401; không cache quyền vĩnh viễn |
| S-SECA → modules | Security.idempotent(request_key:str,body:Body)->ContextManager[Body] | nháp yield holder `{replayed:bool,response:Body|None}`; caller skip action nếu replayed, ghi response vào holder khi mới. Storage/transaction thuộc chủ bảng; same key khác hash Conflict. Cần review mechanics trước S-SECA |
| S-SECA → modules | Security.check_epoch(server_epoch:bytes)->None | epoch khác EpochChanged; thiếu/sai bytes ValueError |
| M-ACC → S-SECA | Accounts.load_user(user_id:int)->User|None; machines_of(user_id:int)->frozenset[int] | load_user không có trả None; machines_of chưa gán trả rỗng; owner bypass scope ở Security |
| M-KEY → S-FM1 | Keys.lookup_kid(kid:str)->Credential|None; server_kem_private()->bytes | không có kid trả None; private X25519 đúng32; file lỗi OSError, quyền sai fail startup; không log bytes |
| M-KEY → S-FM1 | Keys.advance_high_water(connection:sqlite3.Connection,kid:str,issued_at_ms:int)->Credential | cùng connection claim; kiểm lại active/retiring theo policy, absent/revoked Forbidden; M-KEY ghi max(mốc cũ,issued_at_ms), không giảm; trả credential mới; cơ chế khóa theo C0.8 |
| S-FM1 → modules agent | AgentGate.agent_route(route_id:str)->decorator Handler | chỉ route trong ROUTE_POLICY; machine_id luôn từ credential, không body |
| M-CMD → M-MAC | Commands.take_for_offer(machine_id:int,horizon:float)->list[Command] | horizon>=0 giây; rỗng nếu không lệnh đủ hạn; offered ghi ngay trước seal, horizon quy tắc C0.6 |
| M-CMD → M-KEY/S-EPOCH | cancel_for_revoke(machine_id)->None; mark_unknown_all()->None | queued cancel, offered unknown; idempotent, không phát lại tác dụng; DB error propagate |
| M-MENU → M-MAC/M-PUB | Menus.target_version(machine_id)->MenuTarget|None; snapshot(version:int)->Snapshot | chưa gán menu trả None; machine/version không tồn tại NotFound; version toàn server trong epoch hiện tại |
| M-CAT → M-MENU | Catalogue.drinks_for(menu_id:int)->list[Body] | schema dữ liệu C0.5; rỗng khi menu không món, menu không có NotFound |
| M-CAT → M-PUB | Media.path_of(sha256:str)->Path | path trong media root do khối tự lookup; thiếu NotFound; hash sai ValueError |
| M-PUB → M-MAC | Publish.applied_of(machine_id)->Body|None | tuple applied và excluded theo ACK C0.4; None chưa ACK |
| M-ING → M-CMD | Ingest.upsert_ticket(machine_id,row)->None; delete_faults(machine_id,ids:list[int])->None; stock_of(machine_id)->Body|None | upsert theo C0.4, id trùng delete vô hại; stock null nếu chưa báo; cached stock có reported_at server |
| S-EPOCH → S-FM1/S-SECA | Epoch.current()->bytes; check(connection:sqlite3.Connection)->None | check trong claim transaction; restore mismatch EpochChanged, gọi hệ quả đúng một lần; DB/file error fail closed |
| S-SECA → S-EPOCH | Session.rotate_key()->None | thay key và vô hiệu phiên; lỗi OS propagate, không còn phiên dùng key cũ |
| M-KEY → S-EPOCH | Keys.reapply_revoked()->None | danh sách ngoài backup làm revoked không sống lại; idempotent; file/DB lỗi propagate |
| A-NET → modules máy | AgentNet.call(route_id:str,body:Body)->(Status,Body) | đã mở/verify; lỗi transport/4xx/AEAD không trả status revoked, retry có backoff; Q6 còn chờ |
| H-LOCAL → A-APPLY/A-RUN | Helper.call(command:str)->Body | object output C0.7 đã parse; timeout/IO/grammar ValueError/OSError; không retry print tự động |
| module → wiring | Module.setup(deps:Body,registrar:Registrar)->None; Registrar.add(route_id:str,handler:Callable)->None | deps là object API conforming Protocol, thiếu dependency fail startup; route trùng Conflict |

Module handlers và route registration sau này cần binding Flask tại wiring,
không để Protocol tự tạo app. Security.idempotent là contract draft; chưa tạo
framework/store hay giả thành đã có S-SECA. Writer high-water giữ ở M-KEY qua
advance_high_water dùng connection claim S-FM1; đề xuất này cần crypto review.
API M-KEY ghi last_revoked_notice_at để throttle response revoked còn chờ
chốt ở M-KEY; không cho S-FM1 UPDATE credential trực tiếp.

S-NET concrete API (không nhân đôi NetSettings trong contracts):
`NetSettings(cert_file,key_file,ca_file,hostname,host="0.0.0.0",admin_port=443,
agent_port=8443,http_port=80,admin_threads=8,agent_threads=18,http_threads=4,
timeout=60,shutdown_timeout=30)`; `NetServer.start()/stop()` và
`serve(admin_app,agent_app,settings)`. S-DB concrete migration API
`discover(root)`, `migrate(db,root)` và CLI migrate mặc định `var/flexmix.db`;
migration runner không chứa schema nghiệp vụ. Lỗi sửa migration đã áp/number
trùng làm startup fail, không chạy bù tự đoán.

## C0.9 · Cấu hình TOML

`server.config.settings.load_settings(path)->dict[str,dict]`; stdlib tomllib,
không mở network/DB. File mẫu `server.example.toml`, người vận hành tạo file
config riêng không commit key/dữ liệu. Required nonempty string:
`db.path`, `net.cert_file`, `net.key_file`, `net.ca_file`, `net.hostname`,
`fm1.audience`. audience ASCII `[a-z0-9][a-z0-9._-]{0,63}`; hostname là IP
hoặc DNS label hợp lệ theo S-NET. db.path không chấp nhận :memory:. Không default
hostname/LAN/cert lifetime/N giờ replay: Q4/Q9/Q10 vẫn chờ vận hành.
Path tương đối với cwd process; service phải set WorkingDirectory rõ ràng.

- db.timeout=10 giây integer>0; SQLite dùng stdlib tạm, sẽ migrate MySQL.
- net defaults đúng NetSettings ở trên; ports 1..65535 khác nhau, threads và
  timeout/shutdown_timeout integer>0; timeout phải lớn hơn poll_seconds.
- protocol defaults: window_seconds=120; enroll_seconds=600; enroll_attempts=5;
  revoked_notice_seconds=60; ledger_days=30; poll_seconds=25 (1..25);
  read_seconds=5; write_seconds=30; reprint_seconds=120; display_seconds=10.
  Các giá trị đều integer>0. wait request riêng vẫn cho 0 để poll ngay.
- Reject section/key lạ, thiếu required, bool thay int, range sai. Không clamp
  hoặc tiếp tục với fallback. TOML lỗi → TOMLDecodeError; file lỗi → OSError;
  schema/range → ValueError với tên key, không in giá trị bí mật.
- TLS file content, SAN và key0600 kiểm tại S-NET;
  reader không coi template certificate placeholders là cert chạy được.
- `agent_threads=18` chỉ giả định 10 máy+8 của G0.7; khi Q9 có số máy thì
  cấu hình đủ capacity, không coi 18 là kết quả benchmark triển khai.

Hợp lệ: file mẫu và tối thiểu `[db] path="test.db"`, `[net]` đủ bốn key,
`[fm1] audience="test"`; phần không ghi dùng defaults. Từ chối: thiếu hostname,
port 0/65536/trùng, timeout<=poll, audience="../x", threads=true, key viết sai.

## C0.11 · Cô lập và ráp

Module M-* chỉ import cùng subtree, core, security decorators, config.routing,
contracts. security/seca và security/fm1 độc lập, chỉ core/contracts/cùng nhóm.
core không import security hay nghiệp vụ; contracts/config không import core,
security hay modules. Mọi khối không import wiring/main. `wiring.py` là duy
nhất import nhiều module; main là entrypoint nhận app đã ráp, không nối riêng.
Test AST quét absolute và relative imports, có ca sai mô phỏng để kiểm scanner.
Test không phát hiện dynamic import/SQL writer: reviewer kiểm phần này.

Hợp lệ: modules/menu import `server.contracts.interfaces.Menus`, `.store`;
security/fm1 import core.db. Từ chối: menu import modules.keys, security/fm1
import security.seca, `from ... import wiring`, module import app/main.
R1–R6 mới inject dependencies và gọi setup theo thứ tự ở wiring; C0 hiện không
khởi chạy server hoặc thay cho review độc lập. Q1/Q3/Q4/Q6/Q9/Q10 vẫn chờ.
