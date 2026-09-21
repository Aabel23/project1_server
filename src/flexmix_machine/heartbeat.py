"""Best-effort machine heartbeat sender; local operation is independent."""

from collections.abc import Callable
from typing import Any


class HeartbeatUploadError(RuntimeError):
    pass


def send_heartbeat(send: Callable[[dict[str, Any]], dict[str, Any]], heartbeat: dict[str, Any]) -> bool:
    """Return false on Hub/network failure so local selling can continue."""
    try:
        response = send(heartbeat)
    except Exception:
        return False
    return response.get("ack") == "ok"
