"""S-NET: cấu hình nhận trực tiếp trong lúc chờ hợp đồng C0."""

from .main import NetServer, NetSettings, serve
from .wake import Wake, wake

__all__ = ["NetServer", "NetSettings", "serve", "Wake", "wake"]
