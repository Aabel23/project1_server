"""Kiểm S-NET trên server thật, cert tạm ngoài repo; không import spike."""

import datetime as dt
import hashlib
import http.client
import json
import os
import signal
import socket
import ssl
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from flask import Flask, jsonify, request

from deploy.server.make_ca import generate
from server.config.routing import CA_CERT_PATH
from server.core.net import NetServer, NetSettings, Wake, serve, wake
from server.core.net import tls


@pytest.fixture
def pki(tmp_path):
    paths = generate(tmp_path / "offline", tmp_path / "online", ["127.0.0.1", "flexmix.lan"], 30)
    return paths[1], paths[3], paths[2]


def settings(pki, **kwargs):
    ca, cert, key = pki
    return NetSettings(cert, key, ca, "127.0.0.1", host="127.0.0.1",
                       admin_port=0, agent_port=0, http_port=0, **kwargs)


def client_context(ca):
    return ssl.create_default_context(cafile=str(ca))


def call(port, context, path, method="GET", body=None, headers=None, timeout=5):
    conn = (http.client.HTTPSConnection("127.0.0.1", port, context=context, timeout=timeout)
            if context else http.client.HTTPConnection("127.0.0.1", port, timeout=timeout))
    try:
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        version = conn.sock.version() if context and conn.sock else None
        return response.status, response.read(), dict(response.getheaders()), version
    finally:
        conn.close()


def apps():
    admin, agent = Flask("s_net_admin"), Flask("s_net_agent")
    admin.add_url_rule("/admin", view_func=lambda: "admin", methods=["GET", "POST"])
    agent.add_url_rule("/agent", view_func=lambda: "agent")
    return admin, agent


def test_ca_san_expiry_exclusive_and_no_repo_keys(tmp_path, pki):
    ca_path, cert_path, key_path = pki
    ca = x509.load_pem_x509_certificate(ca_path.read_bytes())
    cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
    san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    assert san.get_values_for_type(x509.DNSName) == ["flexmix.lan"]
    assert str(san.get_values_for_type(x509.IPAddress)[0]) == "127.0.0.1"
    assert cert.not_valid_after_utc - cert.not_valid_before_utc == dt.timedelta(days=30)
    cert.verify_directly_issued_by(ca)
    before = key_path.read_bytes()
    with pytest.raises(FileExistsError):
        generate(ca_path.parent, cert_path.parent, ["flexmix.lan"], 30)
    assert key_path.read_bytes() == before
    repo = Path(__file__).resolve().parents[2]
    roots = [repo]
    if (repo / ".git").is_file():
        gitdir = Path((repo / ".git").read_text().split(": ", 1)[1].strip())
        common = (gitdir / (gitdir / "commondir").read_text().strip()).resolve()
        roots.append(common.parent)
    for root in roots:
        if root.exists():
            with pytest.raises(ValueError, match="repo"):
                generate(root / "secret", tmp_path / "unused", ["flexmix.lan"], 30)
    assert not (tmp_path / "unused").exists()
    if os.name != "nt":
        assert key_path.stat().st_mode & 0o777 == 0o600


def test_ca_validates_late_output_before_writing(tmp_path):
    leaf = tmp_path / "online"
    leaf.mkdir()
    (leaf / "leaf.key").write_bytes(b"existing secret")
    with pytest.raises(FileExistsError):
        generate(tmp_path / "offline", leaf, ["flexmix.lan"], 30)
    assert not (tmp_path / "offline").exists()
    assert (leaf / "leaf.key").read_bytes() == b"existing secret"


@pytest.mark.parametrize("sans,days", [([], 30), (["evil/path"], 30), (["ok.lan"], 0),
                                       (["ok.lan"], 3651), (["ok.lan"], True)])
def test_ca_rejects_before_writing(tmp_path, sans, days):
    with pytest.raises(ValueError):
        generate(tmp_path / "root", tmp_path / "leaf", sans, days)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("hostname", ["evil/path", "evil:443", "x\r\nHost: bad", "a..b", ""])
def test_hostname_rejected(pki, hostname):
    ca, cert, key = pki
    with pytest.raises(ValueError):
        NetSettings(cert, key, ca, hostname)


def test_tls_isolation_http_and_safe_logs(pki, caplog):
    caplog.set_level("INFO", logger="flexmix.net")
    admin_app, agent_app = apps()

    @admin_app.get("/error")
    def failure():
        raise ValueError("EXCEPTION_SECRET " + request.headers.get("Authorization", ""))

    original_log_exception = admin_app.log_exception
    server = NetServer(admin_app, agent_app, settings(pki)).start()
    instances, threads = list(server.servers), list(server.threads)
    admin, agent, http = [item.bind_addr[1] for item in instances]
    context = client_context(pki[0])
    try:
        assert call(admin, context, "/admin")[0] == 200
        assert call(agent, context, "/agent")[3] == "TLSv1.3"
        assert call(admin, context, "/agent")[0] == 404
        assert call(agent, context, "/admin")[0] == 404
        assert instances[0].requests is not instances[1].requests
        tls12 = client_context(pki[0])
        tls12.maximum_version = ssl.TLSVersion.TLSv1_2
        with pytest.raises((ssl.SSLError, ConnectionError)):
            call(agent, tls12, "/agent")
        code, data, headers, _ = call(http, None, CA_CERT_PATH)
        assert code == 200 and data == pki[0].read_bytes()
        cert = x509.load_pem_x509_certificate(data)
        assert headers["X-CA-SHA256"] == cert.fingerprint(hashes.SHA256()).hex()
        result = call(http, None, "/admin?password=QUERY_SECRET", headers={"Host": "evil.example"})
        assert result[0] == 301
        assert result[2]["Location"] == f"https://127.0.0.1:{admin}/admin?password=QUERY_SECRET"
        for path in ("/caf%C3%A9", "/a%252Fb", "/a%25b?value=%252F&name=caf%C3%A9"):
            redirect = call(http, None, path)
            assert redirect[0] == 301
            assert redirect[2]["Location"] == f"https://127.0.0.1:{admin}{path}"
        assert call(http, None, CA_CERT_PATH, method="HEAD")[1] == b""
        assert call(http, None, "/admin", method="POST", body="BODY_SECRET")[0] == 405
        assert call(admin, context, "/admin?token=QUERY_SECRET", method="POST", body="BODY_SECRET",
                    headers={"Cookie": "COOKIE_SECRET", "Authorization": "Bearer AUTH_SECRET"})[0] == 200
        assert call(admin, context, "/error", headers={"Authorization": "Bearer AUTH_SECRET"})[0] == 500
        # Cả lỗi parse header của cheroot cũng không lộ request/traceback.
        with socket.create_connection(("127.0.0.1", http)) as conn:
            conn.sendall(b"GET /PATH_SECRET HTTP/1.1\r\nHost: x\r\nBROKEN_HEADER_SECRET\r\n\r\n")
            conn.recv(1024)
        log = caplog.text
        assert "listener=admin status=200" in log
        for secret in ("QUERY_SECRET", "BODY_SECRET", "COOKIE_SECRET", "AUTH_SECRET",
                       "PATH_SECRET", "BROKEN_HEADER_SECRET", "PRIVATE KEY"):
            assert secret not in log
        assert "EXCEPTION_SECRET" not in log
    finally:
        server.stop()
    assert all(not instance.ready and not instance.requests._threads for instance in instances)
    assert all(not thread.is_alive() for thread in threads)
    assert admin_app.log_exception == original_log_exception
    for port in (admin, agent, http):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", port))


def test_linux_permissions_fail_closed(pki, monkeypatch):
    # Chỉ thay biến os trong tls, không đổi os.name toàn tiến trình pytest.
    monkeypatch.setattr(tls, "os", SimpleNamespace(name="posix"))
    pki[2].chmod(0o644)
    with pytest.raises(PermissionError, match="0600"):
        tls.server_context(pki[1], pki[2])


def test_wake_isolation_all_waiters_timeout_and_cleanup():
    signal_bus = Wake()
    with ThreadPoolExecutor(3) as pool:
        a = pool.submit(signal_bus.wait, 1, 3)
        another_a = pool.submit(signal_bus.wait, 1, 3)
        b = pool.submit(signal_bus.wait, 2, 0.5)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            with signal_bus._condition:
                if sum(item[1] for item in signal_bus._waiting.values()) == 3:
                    break
            time.sleep(0.005)
        signal_bus.notify(1)
        assert a.result(0.5) is True and another_a.result(0.5) is True
        assert not b.done()
        assert b.result(1) is False
    assert signal_bus._waiting == {}
    signal_bus.notify(99)
    assert signal_bus._waiting == {}
    for timeout in (-1, float("inf"), float("nan")):
        with pytest.raises(ValueError):
            signal_bus.wait(1, timeout)


@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM])
def test_serve_signal_restores_handlers_and_ports(pki, sig):
    before = {item: signal.getsignal(item) for item in (signal.SIGINT, signal.SIGTERM)}
    timer = threading.Timer(0.3, lambda: signal.raise_signal(sig))
    timer.start()
    try:
        serve(*apps(), settings(pki))
    finally:
        timer.join()
    assert all(signal.getsignal(item) == handler for item, handler in before.items())


def test_shutdown_releases_active_poll(pki):
    admin, agent = apps()
    entered = threading.Event()

    @agent.get("/poll")
    def poll():
        entered.set()
        return jsonify(woken=wake.wait(900, 25))

    server = NetServer(admin, agent, settings(pki)).start()
    port = server.servers[1].bind_addr[1]
    with ThreadPoolExecutor(1) as pool:
        result = pool.submit(call, port, client_context(pki[0]), "/poll")
        assert entered.wait(3)
        start = time.monotonic()
        server.stop()
        assert time.monotonic() - start < 3
        response = result.result(3)
        assert response[0] == 200 and json.loads(response[1])["woken"] is False


def test_shutdown_cancels_poll_arriving_during_http_drain_and_restart(pki, monkeypatch):
    admin, agent = apps()
    entered = threading.Event()

    @agent.get("/poll")
    def poll():
        entered.set()
        return jsonify(woken=wake.wait(901, 3))

    server = NetServer(admin, agent, settings(pki, shutdown_timeout=0.5)).start()
    instances, threads = list(server.servers), list(server.threads)
    context = client_context(pki[0])
    draining, release = threading.Event(), threading.Event()
    http_stop = instances[2].stop

    def drain_http():
        draining.set()
        try:
            assert release.wait(5)
        finally:
            http_stop()

    # Giữ đúng giai đoạn HTTP drain, trong khi agent listener vẫn chạy thật.
    monkeypatch.setattr(instances[2], "stop", drain_http)
    with ThreadPoolExecutor(1) as pool:
        stopped = pool.submit(server.stop)
        try:
            assert draining.wait(3)
            response = call(instances[1].bind_addr[1], context, "/poll", timeout=1)
            assert entered.is_set()
            assert response[0] == 200 and json.loads(response[1])["woken"] is False
            assert wake._waiting == {}
        finally:
            release.set()
            stopped.result(5)
    assert all(not instance.requests._threads for instance in instances)
    assert all(not thread.is_alive() for thread in threads)

    # Khởi động lại cùng server phải cho poll chờ và nhận notify bình thường.
    entered.clear()
    server.start()
    try:
        with ThreadPoolExecutor(1) as pool:
            result = pool.submit(call, server.servers[1].bind_addr[1], context, "/poll")
            assert entered.wait(3)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                with wake._condition:
                    if 901 in wake._waiting:
                        break
                time.sleep(0.005)
            with wake._condition:
                assert 901 in wake._waiting
            wake.notify(901)
            response = result.result(1)
            assert response[0] == 200 and json.loads(response[1])["woken"] is True
    finally:
        server.stop()


def test_longpoll_25s_n10_under_admin_flood(pki):
    """N=10 là giả định Q9. Nửa timeout, nửa notify ở giây 10."""
    admin, agent = apps()
    all_waiting = threading.Condition()
    waiting = set()

    @admin.post("/load")
    def load():
        hashlib.pbkdf2_hmac("sha256", b"pw", b"salt", 20_000)
        return "busy", 401

    @admin.post("/notify/<int:machine_id>")
    def notify(machine_id):
        wake.notify(machine_id)
        return "ok"

    @agent.post("/poll")
    def poll():
        machine_id = request.get_json()["machine_id"]
        with all_waiting:
            waiting.add(machine_id)
            all_waiting.notify_all()
        return jsonify(woken=wake.wait(machine_id, 25))

    server = NetServer(admin, agent, settings(pki, admin_threads=8, agent_threads=18)).start()
    admin_port, agent_port = [item.bind_addr[1] for item in server.servers[:2]]
    context = client_context(pki[0])
    stopped = threading.Event()
    counters = {"finished": 0, "errors": 0}
    counter_lock = threading.Lock()

    def poll_request(machine_id):
        start = time.monotonic()
        response = call(agent_port, context, "/poll", "POST", json.dumps({"machine_id": machine_id}),
                        {"Content-Type": "application/json"}, timeout=35)
        return response, time.monotonic() - start

    def flood():
        while not stopped.is_set():
            try:
                response = call(admin_port, context, "/load", "POST", timeout=10)
                success = response[0] == 401
            except (OSError, http.client.HTTPException):
                success = False
            with counter_lock:
                counters["finished" if success else "errors"] += 1

    flooders = [threading.Thread(target=flood, daemon=True) for _ in range(32)]
    try:
        with ThreadPoolExecutor(10) as pool:
            polls = [pool.submit(poll_request, machine_id) for machine_id in range(10)]
            with all_waiting:
                assert all_waiting.wait_for(lambda: len(waiting) == 10, 5)
            for thread in flooders:
                thread.start()
            time.sleep(10)
            for machine_id in range(5, 9):
                wake.notify(machine_id)
            notify = call(admin_port, context, "/notify/9", "POST", timeout=10)
            assert notify[0] == 200
            results = [future.result(30) for future in polls]
        for machine_id, (response, elapsed) in enumerate(results):
            assert response[0] == 200 and response[3] == "TLSv1.3"
            assert json.loads(response[1])["woken"] is (machine_id >= 5)
            assert (elapsed < 25) if machine_id >= 5 else (25 <= elapsed < 27)
        assert counters["finished"] > 10
        print(json.dumps({"n": 10, "hang_s": 25, "cut_polls": 0,
                          "elapsed_s": [round(item[1], 3) for item in results],
                          "admin_flood": counters}))
    finally:
        stopped.set()
        for thread in flooders:
            if thread.ident is not None:
                thread.join(12)
        server.stop()
