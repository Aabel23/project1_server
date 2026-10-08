"""Every URL path the server answers, in one place.

This server REPLACES version1.0/admin_gui: the machines no longer carry
an admin console, so every management action goes through these routes.

Same naming as version1.0/admin_gui/serve.py: one constant per route,
ending in _PATH. Paths that carry a machine id are templates with a
{machine_id} placeholder -- build them with machine_path(), never by
string concatenation, so a typo is a KeyError and not a silent 404.

Two groups:
    A. Admin API   -- the browser of an admin talks to the server.
    B. Machine API -- a version1.0 machine talks to the server.
       Always initiated by the machine (polling), authenticated by the
       machine's own token.
"""

from __future__ import annotations


# ==========================================================================
# A0. MACHINES -- new, does not exist in admin_gui
# ==========================================================================

MACHINES_PATH = "/api/machines"
MACHINE_SAVE_PATH = "/api/machine/save"
MACHINE_DELETE_PATH = "/api/machine/delete"
MACHINE_TOKEN_ROTATE_PATH = "/api/machine/token/rotate"
MACHINE_STATUS_PATH = "/api/machines/{machine_id}/status"
MACHINE_SYNC_PATH = "/api/machines/{machine_id}/sync"
MENU_COPY_PATH = "/api/menu/copy"


# ==========================================================================
# A1. ACCOUNTS AND PERMISSIONS
# ==========================================================================

LOGIN_PATH = "/api/admin/login"
WHOAMI_PATH = "/api/admin/whoami"
MY_PASSWORD_PATH = "/api/admin/password"

USERS_PATH = "/api/users"
USER_SAVE_PATH = "/api/user/save"
USER_PASSWORD_PATH = "/api/user/password"
USER_ROLE_PATH = "/api/user/role"
USER_ACTIVE_PATH = "/api/user/active"
USER_DELETE_PATH = "/api/user/delete"

PERMISSIONS_PATH = "/api/permissions"
PERMISSIONS_SAVE_PATH = "/api/permissions/save"


# ==========================================================================
# A2. MENU -- per machine
# ==========================================================================

MENU_PATH = "/api/machines/{machine_id}/menu"

# Body carries machine_id.
AVAILABLE_PATH = "/api/drink/available"
PRICE_PATH = "/api/drink/price"
FEATURED_PATH = "/api/drink/featured"

FEATURED_CONFIG_PATH = "/api/machines/{machine_id}/store/featured"
BESTSELLER_CONFIG_PATH = "/api/machines/{machine_id}/store/bestseller"
LAYOUT_PATH = "/api/machines/{machine_id}/store/layout"

DELETE_PATH = "/api/drink/delete"
RESTORE_PATH = "/api/drink/restore"
PURGE_PATH = "/api/drink/purge"
BIN_PATH = "/api/drink/bin"  # ?machine=

EDITOR_PATH = "/api/recipe-editor"
RECIPE_PATH = "/api/recipe"

# Shared by every machine.
IMAGES_PATH = "/api/images"
IMAGE_UPLOAD_PATH = "/api/image"
MEDIA_LIST_PATH = "/api/medias"
MEDIA_UPLOAD_PATH = "/api/media"


# ==========================================================================
# A3. INGREDIENTS AND STOCK -- per machine
# ==========================================================================

INGREDIENTS_PATH = "/api/machines/{machine_id}/ingredients"
INGREDIENT_SAVE_PATH = "/api/ingredient/save"
INGREDIENT_DELETE_PATH = "/api/ingredient/delete"
INGREDIENT_REFILL_PATH = "/api/ingredient/refill"
INGREDIENT_REFILL_ALL_PATH = "/api/ingredient/refill-all"


# ==========================================================================
# A4. REPORTS, TICKETS, ERRORS -- data the machines sent up
# ==========================================================================
# All GETs take ?machine=<id> or ?machine=all.

REPORT_PATH = "/api/report"
ORDERS_PATH = "/api/report/orders"
TICKETS_PATH = "/api/tickets"
TICKET_STATUS_PATH = "/api/ticket/status"
ERRORS_PATH = "/api/errors"
ERRORS_DELETE_PATH = "/api/errors/delete"


# ==========================================================================
# A5. COMMANDS TO A MACHINE -- only take effect while it is online
# ==========================================================================

TICKET_REPRINT_PATH = "/api/machines/{machine_id}/ticket/reprint"
ORDER_MODE_PATH = "/api/machines/{machine_id}/order-mode"
DISPLAY_PATH = "/api/machines/{machine_id}/display"


# ==========================================================================
# B. MACHINE API -- version1.0 machine <-> server
# ==========================================================================

AGENT_HELLO_PATH = "/api/agent/hello"
AGENT_HEARTBEAT_PATH = "/api/agent/heartbeat"
AGENT_MENU_PATH = "/api/agent/menu"  # ?since=<version>
AGENT_MEDIA_PATH = "/api/agent/media/{filename}"
AGENT_MENU_ACK_PATH = "/api/agent/menu/ack"
AGENT_ORDERS_PATH = "/api/agent/orders"
AGENT_ERRORS_PATH = "/api/agent/errors"
AGENT_STOCK_PATH = "/api/agent/stock"
AGENT_COMMANDS_PATH = "/api/agent/commands"
AGENT_COMMAND_RESULT_PATH = "/api/agent/commands/{command_id}/result"


# ==========================================================================
# HELPERS
# ==========================================================================

def machine_path(template: str, machine_id: int | str, **params: object) -> str:
    """Fill a template: machine_path(MENU_PATH, 3) -> "/api/machines/3/menu"."""
    return template.format(machine_id=machine_id, **params)
