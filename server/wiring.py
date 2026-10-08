"""C0.11: khung điểm nối duy nhất cho các lần ráp sau.

R1: đọc settings -> Database/migrate -> Wake -> accounts/machines -> S-SECA
    -> hai app quản trị/agent độc lập -> UI-SHELL -> S-NET.
R2: catalogue -> menus -> báo cáo chỉ đọc.
R3: keys + dependencies epoch -> S-FM1 -> handler hello/long-poll.
R4: publish + ingest; agent apply/upload/stock nối tại agent/main.py.
R5: commands; truyền take_for_offer cho machines và ingest cho commands.
R6: epoch; truyền mark_unknown_all, rotate_key, reapply_revoked.

Tạo API trước đăng ký route để tránh vòng setup. Truyền đối tượng dependency
theo server.contracts, module không import nhau. Chỉ khởi động sau khi các
khối của lần ráp tương ứng qua review tích hợp.
"""
