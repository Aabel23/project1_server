"""Mọi đường dẫn URL của server, gom một chỗ (bản 2).

Server này THAY version1.0/admin_gui: máy không còn trang quản trị riêng,
mọi thao tác quản trị đi qua các route dưới đây.

Cách đặt tên giữ như version1.0/admin_gui/serve.py: mỗi route một hằng,
đuôi _PATH. Đường dẫn có tham số là template có chỗ trống {machine_id},
{menu_id}, {command_id} hoặc {sha256}. Dựng bằng machine_path() hoặc
menu_path(), không cộng chuỗi, để gõ sai thành KeyError chứ không thành
404 lặng lẽ.

Hai nhóm:
    A. API quản trị -- trình duyệt của người quản trị nói với server, qua
       Bảo mật A (cookie phiên, X-FM-Req, quyền). Không dùng FM1.
    B. API máy -- agent trên máy nói với server, luôn do máy khởi xướng.
       Mỗi route agent có đúng một dòng trong ROUTE_POLICY; middleware FM1
       từ chối mọi route không có trong bảng (mục 4.4, M4 của thiết kế).

Đổi so với bản 1 (thiết kế mục 7, "Cần sửa routing.py"):
    - Bỏ AGENT_HEARTBEAT_PATH, MACHINE_TOKEN_ROTATE_PATH.
    - AGENT_COMMAND_RESULT_PATH thành AGENT_RESULTS_PATH, gửi theo lô.
    - AGENT_COMMANDS_PATH, AGENT_MENU_PATH đổi sang POST, tham số vào body.
    - AGENT_MEDIA_PATH theo {sha256}.
    - Thêm route ghép máy, thu hồi, lệnh, màn hình, xác thực lại, giờ, CA.
    - Menu khoá theo {menu_id} thay {machine_id}.
    - Thêm INGREDIENT_REGISTRY_PATH, MENU_BULK_PATH (thiết kế ghi "cần thêm").
    - DISPLAY_PATH tách thành DISPLAY_APPLY_PATH và DISPLAY_KEEP_PATH.
"""

from __future__ import annotations

from dataclasses import dataclass


# ==========================================================================
# A0. MÁY -- không có trong admin_gui
# ==========================================================================

MACHINES_PATH = "/api/machines"
MACHINE_SAVE_PATH = "/api/machine/save"        # body có menu_id (N4)
MACHINE_DELETE_PATH = "/api/machine/delete"
MACHINE_STATUS_PATH = "/api/machines/{machine_id}/status"
# Giữ từ bản 1; thiết kế bản 2 không nhắc tới. Chưa chốt có còn cần không.
MACHINE_SYNC_PATH = "/api/machines/{machine_id}/sync"

# Ghép máy và thu hồi (M1, M5). Cả hai cần xác thực lại.
MACHINE_ENROLL_CODE_PATH = "/api/machines/{machine_id}/enroll-code"
MACHINE_REVOKE_PATH = "/api/machines/{machine_id}/revoke"

# Lệnh xuống máy (L0): xem trạng thái một lệnh, nút "Kiểm tra".
MACHINE_COMMAND_PATH = "/api/machines/{machine_id}/commands/{command_id}"
MACHINE_COMMAND_CHECK_PATH = "/api/machines/{machine_id}/commands/{command_id}/check"


# ==========================================================================
# A1. TÀI KHOẢN VÀ QUYỀN
# ==========================================================================

LOGIN_PATH = "/api/admin/login"
WHOAMI_PATH = "/api/admin/whoami"
MY_PASSWORD_PATH = "/api/admin/password"
STEPUP_PATH = "/api/admin/stepup"              # xác thực lại (A1)

USERS_PATH = "/api/users"
USER_SAVE_PATH = "/api/user/save"
USER_PASSWORD_PATH = "/api/user/password"
USER_ROLE_PATH = "/api/user/role"
USER_ACTIVE_PATH = "/api/user/active"
USER_DELETE_PATH = "/api/user/delete"

PERMISSIONS_PATH = "/api/permissions"
PERMISSIONS_SAVE_PATH = "/api/permissions/save"


# ==========================================================================
# A2. MENU -- theo menu_id (N2, N3)
# ==========================================================================

# Danh sách menu cho trang Menu và bộ chọn menu ở N4.
# Đề xuất thêm, thiết kế chưa ghi tên hằng: chưa chốt.
MENUS_PATH = "/api/menus"
MENU_PATH = "/api/menus/{menu_id}"
MENU_COPY_PATH = "/api/menu/copy"
MENU_BULK_PATH = "/api/menu/bulk"              # sửa hàng loạt một món trên nhiều menu

# Body mang menu_id, row_version, request_key, server_epoch.
AVAILABLE_PATH = "/api/drink/available"
PRICE_PATH = "/api/drink/price"
FEATURED_PATH = "/api/drink/featured"

FEATURED_CONFIG_PATH = "/api/menus/{menu_id}/store/featured"
BESTSELLER_CONFIG_PATH = "/api/menus/{menu_id}/store/bestseller"
LAYOUT_PATH = "/api/menus/{menu_id}/store/layout"


# ==========================================================================
# A3. THƯ VIỆN MÓN -- dùng chung mọi menu (N1, N6, K4)
# ==========================================================================

DELETE_PATH = "/api/drink/delete"
RESTORE_PATH = "/api/drink/restore"
PURGE_PATH = "/api/drink/purge"
BIN_PATH = "/api/drink/bin"

EDITOR_PATH = "/api/recipe-editor"
RECIPE_PATH = "/api/recipe"

IMAGES_PATH = "/api/images"
IMAGE_UPLOAD_PATH = "/api/image"
MEDIA_LIST_PATH = "/api/medias"
MEDIA_UPLOAD_PATH = "/api/media"

INGREDIENT_REGISTRY_PATH = "/api/ingredient-registry"   # sổ cấp id 1-24 (K4)


# ==========================================================================
# A4. NGUYÊN LIỆU VÀ TỒN KHO -- theo máy, đi bằng lệnh (K1, K2)
# ==========================================================================

INGREDIENTS_PATH = "/api/machines/{machine_id}/ingredients"
# Body mang machine_id, request_key, server_epoch.
INGREDIENT_SAVE_PATH = "/api/ingredient/save"
INGREDIENT_DELETE_PATH = "/api/ingredient/delete"
INGREDIENT_REFILL_PATH = "/api/ingredient/refill"
INGREDIENT_REFILL_ALL_PATH = "/api/ingredient/refill-all"


# ==========================================================================
# A5. BÁO CÁO, VÉ, LỖI -- bản sao máy gửi lên (D3, L1)
# ==========================================================================
# Các GET nhận ?machine=<id> hoặc ?machine=all.

REPORT_PATH = "/api/report"
ORDERS_PATH = "/api/report/orders"
TICKETS_PATH = "/api/tickets"
TICKET_STATUS_PATH = "/api/ticket/status"
ERRORS_PATH = "/api/errors"
ERRORS_DELETE_PATH = "/api/errors/delete"


# ==========================================================================
# A6. LỆNH XUỐNG MÁY -- chỉ có tác dụng khi máy online (L2, L3, L4)
# ==========================================================================

TICKET_REPRINT_PATH = "/api/machines/{machine_id}/ticket/reprint"
ORDER_MODE_PATH = "/api/machines/{machine_id}/order-mode"
DISPLAY_APPLY_PATH = "/api/machines/{machine_id}/display/apply"
DISPLAY_KEEP_PATH = "/api/machines/{machine_id}/display/keep"


# ==========================================================================
# A7. VẬN HÀNH
# ==========================================================================

CLOCK_CONFIRM_PATH = "/api/admin/clock/confirm"   # "Xác nhận giờ đúng" (M2), cần xác thực lại
# Cổng 80, công khai: tải ca.crt kèm vân tay SHA-256.
CA_CERT_PATH = "/api/ca-cert"


# ==========================================================================
# B. API MÁY -- agent <-> server, cổng agent
# ==========================================================================

AGENT_TRUST_PATH = "/api/agent/trust"           # M1, trust bundle có HMAC
AGENT_ENROLL_PATH = "/api/agent/enroll"         # M1, FM1 với kid "enroll"
AGENT_HELLO_PATH = "/api/agent/hello"           # M3, M6
AGENT_COMMANDS_PATH = "/api/agent/commands"     # M3, long-poll, POST
AGENT_RESULTS_PATH = "/api/agent/results"       # L0, kết quả theo lô
AGENT_MENU_PATH = "/api/agent/menu"             # N5, POST, since trong body
AGENT_MENU_ACK_PATH = "/api/agent/menu/ack"     # N5
AGENT_ORDERS_PATH = "/api/agent/orders"         # D1
AGENT_ERRORS_PATH = "/api/agent/errors"         # D2
AGENT_STOCK_PATH = "/api/agent/stock"           # K3
AGENT_MEDIA_PATH = "/api/agent/media/{sha256}"  # N5, GET, chỉ TLS


# ==========================================================================
# ROUTE_POLICY -- mỗi route agent một chế độ bảo vệ (M4)
# ==========================================================================

MODE_TRUST = "trust"        # chưa FM1; response mang HMAC dẫn từ mã ghép
MODE_ENROLL = "enroll"      # FM1, credential_kid = "enroll", kèm proof
MODE_FM1 = "fm1"            # FM1 đầy đủ, credential của máy
MODE_TLS_ONLY = "tls_only"  # chỉ TLS; toàn vẹn nhờ sha256 + size trong snapshot
MODES = (MODE_TRUST, MODE_ENROLL, MODE_FM1, MODE_TLS_ONLY)

KIB = 1024
MIB = 1024 * KIB


@dataclass(frozen=True)
class RoutePolicy:
    """Một dòng của ROUTE_POLICY.

    max_request: trần thân request. Với fm1/enroll là trần JSON bên trong
        bản mã, chưa tính envelope. Với tls_only (GET) là 0.
    max_response: trần thân response. Với fm1/enroll là trần JSON `body`
        bên trong response đã seal.
    Hai trần là tham số đề xuất, chưa chốt (thiết kế M4).
    """

    path: str
    method: str
    mode: str
    max_request: int
    max_response: int


# Khoá là route_id: tên hằng, đúng chuỗi agent ghi vào trường route_id của M.
ROUTE_POLICY: dict[str, RoutePolicy] = {
    "AGENT_TRUST_PATH": RoutePolicy(AGENT_TRUST_PATH, "POST", MODE_TRUST, 1 * KIB, 16 * KIB),
    "AGENT_ENROLL_PATH": RoutePolicy(AGENT_ENROLL_PATH, "POST", MODE_ENROLL, 4 * KIB, 4 * KIB),
    "AGENT_HELLO_PATH": RoutePolicy(AGENT_HELLO_PATH, "POST", MODE_FM1, 256 * KIB, 4 * KIB),
    "AGENT_COMMANDS_PATH": RoutePolicy(AGENT_COMMANDS_PATH, "POST", MODE_FM1, 1 * KIB, 64 * KIB),
    "AGENT_RESULTS_PATH": RoutePolicy(AGENT_RESULTS_PATH, "POST", MODE_FM1, 256 * KIB, 16 * KIB),
    "AGENT_MENU_PATH": RoutePolicy(AGENT_MENU_PATH, "POST", MODE_FM1, 1 * KIB, 2 * MIB),
    "AGENT_MENU_ACK_PATH": RoutePolicy(AGENT_MENU_ACK_PATH, "POST", MODE_FM1, 64 * KIB, 1 * KIB),
    "AGENT_ORDERS_PATH": RoutePolicy(AGENT_ORDERS_PATH, "POST", MODE_FM1, 256 * KIB, 1 * KIB),
    "AGENT_ERRORS_PATH": RoutePolicy(AGENT_ERRORS_PATH, "POST", MODE_FM1, 256 * KIB, 1 * KIB),
    "AGENT_STOCK_PATH": RoutePolicy(AGENT_STOCK_PATH, "POST", MODE_FM1, 16 * KIB, 1 * KIB),
    "AGENT_MEDIA_PATH": RoutePolicy(AGENT_MEDIA_PATH, "GET", MODE_TLS_ONLY, 0, 10 * MIB),
}


# ==========================================================================
# HÀM DỰNG ĐƯỜNG DẪN
# ==========================================================================

def machine_path(template: str, machine_id: int | str, **params: object) -> str:
    """Điền template: machine_path(INGREDIENTS_PATH, 3) -> "/api/machines/3/ingredients"."""
    return template.format(machine_id=machine_id, **params)


def menu_path(template: str, menu_id: int | str, **params: object) -> str:
    """Điền template: menu_path(MENU_PATH, 2) -> "/api/menus/2"."""
    return template.format(menu_id=menu_id, **params)
