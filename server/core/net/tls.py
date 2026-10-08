"""TLS 1.3 và quyền khoá; không đọc cấu hình nghiệp vụ."""

import os
import ssl
import stat
from pathlib import Path


def server_context(cert_file, key_file):
    key = Path(key_file)
    mode = key.stat().st_mode
    if not stat.S_ISREG(mode):
        raise ValueError("Khoá TLS phải là file thường")
    # Windows không có quyền POSIX; operator phải quản lý ACL riêng.
    if os.name != "nt" and stat.S_IMODE(mode) != 0o600:
        raise PermissionError("Khoá TLS phải có quyền 0600")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3
    context.load_cert_chain(str(cert_file), str(key))
    return context
