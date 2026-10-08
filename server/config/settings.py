"""Đọc cấu hình TOML; dừng trước khởi động nếu cấu hình sai."""

import ipaddress
from pathlib import Path
import re
import tomllib


DEFAULTS = {
    "db": {"timeout": 10},
    "net": {
        "host": "0.0.0.0", "admin_port": 443, "agent_port": 8443, "http_port": 80,
        "admin_threads": 8, "agent_threads": 18, "http_threads": 4,
        "timeout": 60, "shutdown_timeout": 30,
    },
    "protocol": {
        "window_seconds": 120, "enroll_seconds": 600, "enroll_attempts": 5,
        "revoked_notice_seconds": 60, "ledger_days": 30, "poll_seconds": 25,
        "read_seconds": 5, "write_seconds": 30, "reprint_seconds": 120,
        "display_seconds": 10,
    },
}
REQUIRED = {
    "db": ("path",),
    "net": ("cert_file", "key_file", "ca_file", "hostname"),
    "fm1": ("audience",),
}


def load_settings(path: str | Path) -> dict[str, dict]:
    """Trả các section đã kiểm; đường dẫn tương đối tính từ cwd tiến trình.

    Ném OSError, tomllib.TOMLDecodeError hoặc ValueError, không chạy service.
    Nội dung và quyền file TLS do S-NET kiểm khi khởi động.
    """
    with Path(path).open("rb") as stream:
        supplied = tomllib.load(stream)
    if supplied.keys() - (DEFAULTS.keys() | REQUIRED.keys()):
        raise ValueError("Section cấu hình không được hỗ trợ")
    settings = {}
    for section in DEFAULTS.keys() | REQUIRED.keys():
        values = supplied.get(section, {})
        defaults = DEFAULTS.get(section, {})
        required = REQUIRED.get(section, ())
        if not isinstance(values, dict) or values.keys() - (defaults.keys() | set(required)):
            raise ValueError(f"Section không hợp lệ: {section}")
        settings[section] = defaults | values
        for key in required:
            value = values.get(key)
            if not isinstance(value, str) or not value.strip() or "\x00" in value:
                raise ValueError(f"Bắt buộc chuỗi không rỗng: {section}.{key}")
        for key, default in defaults.items():
            value = settings[section][key]
            if isinstance(default, int):
                if type(value) is not int or value <= 0:
                    raise ValueError(f"Bắt buộc số nguyên dương: {section}.{key}")
            elif not isinstance(value, str) or not value.strip() or "\x00" in value:
                raise ValueError(f"Bắt buộc chuỗi không rỗng: {section}.{key}")
    net = settings["net"]
    ports = [net[key] for key in ("admin_port", "agent_port", "http_port")]
    if max(ports) > 65535 or len(set(ports)) != 3:
        raise ValueError("Các cổng phải khác nhau và trong 1..65535")
    try:
        ipaddress.ip_address(net["hostname"])
    except ValueError:
        if len(net["hostname"]) > 253 or not all(
            re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
            for label in net["hostname"].split(".")
        ):
            raise ValueError("Hostname HTTPS không hợp lệ") from None
    if settings["db"]["path"] == ":memory:":
        raise ValueError("db.path phải là file cho backend SQLite tạm")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", settings["fm1"]["audience"]):
        raise ValueError("fm1.audience không hợp lệ")
    if settings["protocol"]["poll_seconds"] > 25:
        raise ValueError("protocol.poll_seconds không được vượt 25")
    if net["timeout"] <= settings["protocol"]["poll_seconds"]:
        raise ValueError("net.timeout phải lớn hơn protocol.poll_seconds")
    return settings
