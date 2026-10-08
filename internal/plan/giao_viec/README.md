# Phân việc theo khối

Một khối, một agent. Agent nào cũng chỉ sửa thư mục của khối mình, làm trên nhánh `khoi/<khối>` trong worktree riêng. Operator review rồi mới merge vào `main`.

| Khối | Đợt | Ai làm | Cách giao | Trạng thái |
|---|---|---|---|---|
| G0, C0 | 0 | Opus (agent nền) | Operator giao trực tiếp | → đang làm |
| S-DB | 1 | GPT Sol high (Codex) | Dán [S-DB.md](S-DB.md) vào Codex | ⏸ chờ C0 |
| S-NET | 1 | GPT Sol high (Codex) | Dán [S-NET.md](S-NET.md) vào Codex | ⏸ chờ C0, G0.7 |
| UI-SHELL | 1 | Opus | Operator giao trực tiếp | ⏸ chờ C0 |
| Khối phía máy | 1–3 | chưa phân | | ⏸ chờ Q6 |

Lý do chia như vậy:

- S-DB và S-NET nặng về hạ tầng và logic: transaction, migration, TLS, đa luồng.
- UI-SHELL là phần trang web chép từ admin_gui.
- Không khối nào được giao cho hai agent.
