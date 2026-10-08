# Server mẹ FlexMix

Server quản lý nhiều máy FlexMix trong LAN. Server này thay `admin_gui` trên từng máy.

- **Thiết kế (bản 2):** `docs/server_architect.html`.
- **Kế hoạch theo khối:** `internal/plan/index.md`. Trang HTML dựng từ đó: `docs/server_plan.html`.
- **Hợp đồng giữa các khối:** `internal/contracts/`.
- **Bằng chứng từng bước:** `internal/plan/bang_chung/`.

## Thư mục

| Thư mục | Làm gì |
|---|---|
| `server/` | Code chạy thật: `config/` (routing, settings), `contracts/` (Protocol cho các mối nối), `wiring.py` (điểm nối duy nhất), sau này có `core/`, `security/`, `modules/` |
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
```

Khoá, cert và `server.toml` không bao giờ vào repo (xem `.gitignore`).
