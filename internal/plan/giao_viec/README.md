# Phân việc theo khối

Một khối, một agent. Agent nào cũng chỉ sửa thư mục của khối mình, làm trên nhánh `khoi/<khối>` trong worktree riêng. Operator review rồi mới merge vào `main`.

| Khối | Đợt | Ai làm | Cách giao | Trạng thái |
|---|---|---|---|---|
| G0, C0 | 0 | Codex tiếp quản Opus | User giao tiếp khi Claude hết token | → review C0 không có lỗi mới; bản nháp/Q1 và G0.6 còn chờ |
| S-DB | 1 | Codex, agent S-DB | [S-DB.md](S-DB.md), đổi sang SQLite tạm theo user | → P2 migration đã sửa, hồi quy và review lại đạt; chờ MySQL/R1 |
| S-NET | 1 | Codex, agent S-NET | [S-NET.md](S-NET.md) | → P2 shutdown/P3 redirect đã sửa, hồi quy và review lại đạt; chờ Linux/Pi/R1 |
| UI-SHELL | 1 | Codex tiếp quản Opus | User giao tiếp khi Claude hết token | → review không có lỗi mới trong stub; chờ R1 |
| Khối phía máy | 1–3 | chưa phân | | ⏸ chờ Q6 |

Lý do chia như vậy:

- S-DB và S-NET nặng về hạ tầng và logic: transaction, migration, TLS, đa luồng.
- UI-SHELL là phần trang web chép từ admin_gui.
- Không khối nào được giao cho hai agent.

Chỉ đạo mới và kế hoạch chuyển SQLite sang MySQL ghi ở
[CODEX_SQLITE_THONG_BAO_CLAUDE.md](CODEX_SQLITE_THONG_BAO_CLAUDE.md).
Hợp đồng nháp không đồng nghĩa Q1 đã được duyệt. Bằng chứng kiểm từng khối
ở `../bang_chung/`; chưa đánh ✓ khi còn bước nghiệm thu hoặc review chưa đạt.

Review độc lập mới nhất:
[REVIEW_CODEX.md](../bang_chung/REVIEW_CODEX.md) — đã sửa 2 lỗi P2, 1 lỗi P3
theo yêu cầu tiếp của user; 161 test Python và kiểm UI đạt. Hai reviewer kiểm lại đạt.
