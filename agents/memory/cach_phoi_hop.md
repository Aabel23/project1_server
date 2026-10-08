# Cách phối hợp giữa user và Codex

Cập nhật 08/10/2026. Đúc kết từ yêu cầu và cách làm trong phiên này, áp dụng
cho dự án server mẹ FlexMix. Yêu cầu mới của user được ưu tiên; không suy rộng
quyết định của dự án này sang dự án khác.

## Nhận việc và trao đổi

- Trao đổi bằng tiếng Việt, ngắn và thẳng. Nêu kết quả chính trước, kèm link
  để user xem code/doc/tiến độ. Khi user hỏi kiến thức, giải thích công dụng và
  liên hệ với dự án, nói rõ phần tạm, đề xuất và đã chốt.
- Câu ngắn như “sửa”, “cập nhật doc”, “làm phần Claude” là giao thực thi trong
  phạm vi đang trao đổi. Tiếp tục công việc đã giao, không dừng ở đề xuất hoặc
  hỏi lại phần đã được cho phép. Khi tiếp quản, ghi lại phần đã làm để Claude
  và phiên sau đọc được.
- Hỏi khi thiếu quyết định thật sự ảnh hưởng thiết kế/nghiệp vụ, môi trường
  hoặc quyền thực hiện; nêu đúng điều cần chốt và tiếp tục phần độc lập.
  Thời gian chờ không phải câu trả lời. Giải thích thuật ngữ không phải duyệt
  thay đổi kiến trúc.
- Khi làm việc lâu, báo ngắn điều vừa xác nhận và bước tiếp theo. Bàn giao có
  kết quả, lệnh kiểm/môi trường, phần còn chờ và link; không kể lại mọi thao tác.

## Nhịp làm việc

1. Đọc task, plan/phân việc, memory liên quan và trạng thái git. Lần theo luồng
   vào/ra và caller trước khi sửa; chỉ đọc thêm hồ sơ kỹ thuật khi task cần.
2. Thực thi phần được giao bằng thay đổi nhỏ nhất đủ đúng. Dùng lại code/stdlib;
   không thêm framework, abstraction, dependency hoặc tính năng để dành.
   Giữ kiểm đầu vào, bảo mật, transaction/rollback và khả năng tiếp cận.
   Thiết kế mới cần đối chiếu/phản biện, phân biệt đề xuất với đã chốt và để
   user chốt các quyết định còn mở trước khi triển khai phần phụ thuộc.
3. Với lỗi, tái hiện nguyên nhân và để lại kiểm hồi quy có ý nghĩa: lỗi cũ làm
   kiểm đỏ, bản sửa làm kiểm xanh. Chạy kiểm phù hợp; mở rộng khi có rủi ro
   tích hợp hoặc thay đổi mới, không lặp bộ nặng chỉ để tăng số lần chạy.
4. Khi user giao review: reviewer đọc độc lập, không sửa code; báo vị trí,
   kịch bản, hậu quả và bằng chứng. Yêu cầu review không tự trở thành lệnh sửa.
   Khi user giao sửa, sửa gốc lỗi, kiểm lại rồi cho reviewer kiểm phần ảnh hưởng.
5. Cập nhật trạng thái và bằng chứng cùng lượt bàn giao. Test trên dev không
   thay nghiệm thu Pi/LAN/Linux, trình duyệt/backend thật hoặc bước ráp.

## Khi dùng nhiều agent

- Chỉ chia khi user giao hoặc chỉ dẫn áp dụng yêu cầu. Khi chia: một khối một
  người ghi, phạm vi file và hợp đồng vào/ra rõ; phần độc lập làm song song.
- Coder và reviewer là hai vai riêng. Agent không sửa chồng file hoặc tự đổi
  hợp đồng/điểm nối chung; báo lead khi cần điều phối. Dùng worktree riêng khi
  có nguy cơ đụng nhau. Bàn giao model thực tế chỉ khi runtime xác nhận được.
- Lead đọc diff, chạy kiểm tích hợp cần thiết và ghi kết quả. Không coi chép
  file vào working tree là merge; không nhận đã commit/publish khi chưa làm.
  Giữ nguyên thay đổi sẵn có của user ngoài task.

## Nơi ghi để phiên sau tiếp tục

- [index.md](../../internal/plan/index.md): tiến độ hiện tại và quyết định còn chờ.
- [giao_viec/README.md](../../internal/plan/giao_viec/README.md): ai làm khối nào.
- `internal/plan/bang_chung/`: lệnh, môi trường, kết quả/review và giới hạn.
- [ghi chú Claude](../../internal/plan/giao_viec/CODEX_SQLITE_THONG_BAO_CLAUDE.md):
  tiếp quản, thay đổi phạm vi và việc migrate sau.
- Markdown là nguồn; đổi plan thì dựng và kiểm lại `docs/server_plan.html`
  bằng hai lệnh Node trong README. Không sửa tay HTML được sinh.
- Memory chỉ giữ thói quen phối hợp, quyết định bền và link nguồn. Không lưu
  khóa, token, mật khẩu hoặc dữ liệu riêng vào memory. Không chép
  log, số test/commit/tiến độ dễ cũ vào nhiều memory. Quyết định đổi thì sửa
  mục cũ, không nối thêm đoạn mâu thuẫn; hồ sơ tranh luận cũ dùng để đối chiếu.
