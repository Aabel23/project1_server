"""Hai pool TLS độc lập và cổng HTTP chỉ phục vụ CA/chuyển hướng."""

import ipaddress
import logging
import math
import re
import signal
import threading
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, quote_from_bytes

from cheroot import wsgi
from cheroot.ssl.builtin import BuiltinSSLAdapter
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization

from server.config.routing import CA_CERT_PATH
from .tls import server_context
from .wake import wake

logger = logging.getLogger("flexmix.net")


@dataclass(frozen=True)
class NetSettings:
    cert_file: Path
    key_file: Path
    ca_file: Path
    hostname: str
    host: str = "0.0.0.0"
    admin_port: int = 443
    agent_port: int = 8443
    http_port: int = 80
    admin_threads: int = 8
    agent_threads: int = 18
    http_threads: int = 4
    timeout: float = 60
    shutdown_timeout: float = 30

    def __post_init__(self):
        try:
            ipaddress.ip_address(self.hostname)
        except ValueError:
            labels = self.hostname.split(".")
            if len(self.hostname) > 253 or not all(
                re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
                for label in labels
            ):
                raise ValueError("Hostname HTTPS không hợp lệ") from None
        ports = [self.admin_port, self.agent_port, self.http_port]
        if any(type(port) is not int or not 0 <= port <= 65535 for port in ports):
            raise ValueError("Cổng phải trong 0..65535; 0 chỉ dùng test")
        fixed = [port for port in ports if port]
        if len(set(fixed)) != len(fixed):
            raise ValueError("Các cổng phải khác nhau")
        if any(type(count) is not int or count < 1 for count in
               (self.admin_threads, self.agent_threads, self.http_threads)):
            raise ValueError("Số thread phải là số nguyên dương")
        if any(not math.isfinite(value) or value <= 0 for value in
               (self.timeout, self.shutdown_timeout)):
            raise ValueError("Timeout phải hữu hạn và dương")


def logged_app(app, listener):
    """Chỉ log nhãn listener cố định và mã trạng thái; không log request."""
    def application(environ, start_response):
        def start(status, headers, exc_info=None):
            code = status.split(" ", 1)[0]
            logger.info("request listener=%s status=%s", listener,
                        code if re.fullmatch(r"[1-5][0-9]{2}", code) else "invalid")
            return start_response(status, headers, exc_info)
        return app(environ, start)
    return application


class NetServer:
    def __init__(self, admin_app, agent_app, settings):
        self.settings = settings
        self._apps = (admin_app, agent_app)
        self.servers = []
        self.threads = []
        self._exception_loggers = []

    def _http_app(self, environ, start_response):
        method = environ["REQUEST_METHOD"]
        if method not in ("GET", "HEAD"):
            start_response("405 Method Not Allowed", [("Allow", "GET, HEAD")])
            return [b""]
        if environ.get("PATH_INFO") == CA_CERT_PATH:
            start_response("200 OK", [
                ("Content-Type", "application/x-x509-ca-cert"),
                ("Content-Disposition", 'attachment; filename="ca.crt"'),
                ("Content-Length", str(len(self._ca_pem))),
                ("X-CA-SHA256", self._fingerprint),
            ])
            return [b"" if method == "HEAD" else self._ca_pem]
        hostname = self.settings.hostname
        if ":" in hostname:
            hostname = "[" + hostname + "]"
        port = self.servers[0].bind_addr[1]
        authority = hostname if port == 443 else f"{hostname}:{port}"
        # Không dùng Host do client gửi; path không được đổi authority.
        path = quote_from_bytes(environ.get("PATH_INFO", "/").encode("latin-1"), safe="/:@")
        query = quote(environ.get("QUERY_STRING", ""), safe="=&;%:+,/?@")
        location = f"https://{authority}{path}" + ("?" + query if query else "")
        start_response("301 Moved Permanently", [("Location", location), ("Content-Length", "0")])
        return [b""]

    def start(self):
        if self.servers:
            raise RuntimeError("Server đã khởi động")
        context = server_context(self.settings.cert_file, self.settings.key_file)
        # Chỉ công bố cert đã parse và mã hoá lại, không công bố bytes PEM thừa.
        ca = x509.load_pem_x509_certificate(Path(self.settings.ca_file).read_bytes())
        self._ca_pem = ca.public_bytes(serialization.Encoding.PEM)
        self._fingerprint = ca.fingerprint(hashes.SHA256()).hex()
        specs = zip((*self._apps, self._http_app),
                    (self.settings.admin_port, self.settings.agent_port, self.settings.http_port),
                    (self.settings.admin_threads, self.settings.agent_threads, self.settings.http_threads),
                    ("admin", "agent", "http"))
        try:
            for app, port, count, label in specs:
                # Flask tự log traceback trước khi trả 500; exception có thể chứa bí mật.
                if hasattr(app, "log_exception"):
                    self._exception_loggers.append((app, app.log_exception))
                    app.log_exception = lambda exc_info, label=label: logger.error(
                        "application_error listener=%s", label
                    )
                server = wsgi.Server(
                    (self.settings.host, port), logged_app(app, label), numthreads=count,
                    max=count, request_queue_size=128, server_name="flexmix",
                    timeout=self.settings.timeout, shutdown_timeout=self.settings.shutdown_timeout,
                )
                # Cheroot có thể đưa URL hoặc lỗi app vào message/traceback.
                server.error_log = lambda message, level=logging.ERROR, traceback=False: logger.log(
                    level, "server_error"
                )
                if label != "http":
                    adapter = BuiltinSSLAdapter(str(self.settings.cert_file), str(self.settings.key_file))
                    adapter.context = context
                    server.ssl_adapter = adapter
                self.servers.append(server)
                server.prepare()
            wake.resume()
            for server in self.servers:
                thread = threading.Thread(target=server.serve, name="flexmix-listener", daemon=True)
                self.threads.append(thread)
                thread.start()
            return self
        except BaseException:
            self.stop()
            raise

    def stop(self):
        wake.cancel_waiters()
        # Đóng listener trước, chờ worker hoàn tất trong shutdown_timeout.
        for server in reversed(self.servers):
            server.stop()
        for thread in self.threads:
            thread.join(self.settings.shutdown_timeout)
        self.servers.clear()
        self.threads.clear()
        for app, original in self._exception_loggers:
            app.log_exception = original
        self._exception_loggers.clear()


def serve(admin_app, agent_app, settings):
    """Cửa vào wiring tạm; gọi từ main thread để quản lý signal."""
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("serve phải chạy từ main thread")
    stopped = threading.Event()
    previous = {}
    server = NetServer(admin_app, agent_app, settings)
    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            previous[sig] = signal.signal(sig, lambda signum, frame: stopped.set())
        server.start()
        while not stopped.wait(0.2):
            if any(not thread.is_alive() for thread in server.threads):
                raise RuntimeError("Listener đã dừng ngoài dự kiến")
    finally:
        server.stop()
        for sig, handler in previous.items():
            signal.signal(sig, handler)
