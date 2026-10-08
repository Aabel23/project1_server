# Server mẹ FlexMix

Server quản lý nhiều máy FlexMix trong LAN. Server này thay `admin_gui` trên từng máy.

- **Thiết kế (bản 2):** `docs/server_architect.html`.
- **Kế hoạch theo khối:** `internal/plan/index.md`. Trang HTML dựng từ đó: `docs/server_plan.html`.
- **Hợp đồng giữa các khối:** `internal/contracts/`.
- **Bằng chứng từng bước:** `internal/plan/bang_chung/`.
- **Bắt đầu phiên mới:** [AGENTS.md](AGENTS.md), [memory phối hợp](agents/memory/cach_phoi_hop.md)
  và [bối cảnh dự án](agents/memory/hieu_biet_server_me.md).

## Tiến độ hiện tại · 08/10/2026

Codex đã tiếp quản phần Claude: C0/vector/settings, S-DB SQLite tạm, S-NET
và UI-SHELL có code/kiểm trên Windows. Đã sửa 2 lỗi P2 và 1 lỗi P3, reviewer
kiểm lại đạt. **161 test Python đạt (34.11 s)**, kiểm UI bằng Node đạt.
Hợp đồng vẫn là đề xuất; chờ Q1, Pi/G0.6, Linux/LAN và ráp R1–R6.

- [Trang tiến độ](docs/server_plan.html) đọc trạng thái từ Markdown.
- [Phân việc](internal/plan/giao_viec/README.md) và [báo cáo review/sửa lỗi](internal/plan/bang_chung/REVIEW_CODEX.md).
- [Ghi chú bàn giao Claude](internal/plan/giao_viec/CODEX_SQLITE_THONG_BAO_CLAUDE.md): SQLite `.db` tạm, sẽ migrate MySQL sau.

Wiring hiện là khung; các module bảo mật/nghiệp vụ chưa triển khai, phía máy
chờ Q6. Thay đổi tiếp quản/sửa lỗi còn trong working tree, chưa commit/merge.

## Thư mục

| Thư mục | Làm gì |
|---|---|
| `server/` | `config/`, `contracts/`, `core/db/`, `core/net/`, `static/shell/`; `wiring.py` là điểm nối hiện còn khung. `security/`, `modules/` sẽ thêm khi triển khai nghiệp vụ |
| `tests/` | Test pytest. `tests/c0/` cho hợp đồng; `tests/vectors/fm1/` là bộ vector FM1 dùng chung cho server và máy |
| `spike/` | Spike G0: mã tham chiếu FM1, test mật mã, long-poll, benchmark. Không phải code chạy thật |
| `internal/` | Plan, hợp đồng, bằng chứng |
| `agents/` | Vai và hồ sơ của các agent (architect, reviewer…) |
| `docs/` | Thiết kế và trang plan dạng HTML, chạy offline |
| `machine/` | Ghi chép về DB phía máy |

## Chạy test

```
python -m venv .venv
.venv/Scripts/python -m pip install flask cheroot pyhpke pytest cryptography==50.0.1
.venv/Scripts/python -m pytest tests -q
.venv/Scripts/python -m pytest spike -q
node tests/ui_shell/check_shell.cjs
```

Khoá, cert và `server.toml` không bao giờ vào repo (xem `.gitignore`).
DB tạm mặc định `var/flexmix.db` cũng bị gitignore. Tạo/áp migration bằng
`.venv/Scripts/python -m server.manage migrate`; hiện chỉ có sổ migration rỗng.
Sau khi sửa Markdown, dựng lại trang tiến độ bằng
`node internal/plan/cong_cu/dung_trang_plan.js`.
Kiểm trang/đường dẫn bằng `node internal/plan/cong_cu/check_trang_plan.cjs`.
