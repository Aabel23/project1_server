"""G0.7: long-poll qua TLS 1.3 của cheroot, hai cổng, hai pool.

Kịch bản:
1. Sinh CA và cert leaf tự ký TẠM trong thư mục tạm (xoá khi xong, không commit).
2. Hai server cheroot trong một tiến trình:
   - cổng quản trị: pool nhỏ, có route nặng để flood và route đánh thức;
   - cổng agent: pool riêng, route long-poll chờ trên threading.Condition.
3. Treo N poll (mặc định N = 10, giả định vì chưa có Q9) với wait = 25 s.
   - Một nửa (poll 0..N/2-1) treo hết 25 s rồi trả "timeout".
   - Nửa còn lại được đánh thức ở giây thứ 10: phần lớn gọi thẳng
     wake.notify() (giống module gọi sau commit), poll cuối đánh thức qua
     HTTP ở cổng quản trị (đi qua pool đang bị flood).
4. Trong suốt thời gian treo, flood cổng quản trị bằng nhiều luồng hơn số
   thread của pool quản trị.
5. Kiểm thêm: client TLS 1.2 bị từ chối; route agent gọi vào cổng quản trị
   là 404.

Đạt khi: mọi poll nhận đủ HTTP 200 đúng nội dung, không poll nào bị cắt,
poll timeout kết thúc trong [25, 27) s, poll được đánh thức kết thúc trước 25 s.

Chạy: .venv/Scripts/python spike/longpoll_g0_7.py [--n 10] [--hang 25]
"""

from __future__ import annotations

import argparse
import datetime as dt
import http.client
import ipaddress
import json
import shutil
import ssl
import sys
import tempfile
import threading
import time
from pathlib import Path

from cheroot import wsgi
from cheroot.ssl.builtin import BuiltinSSLAdapter
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from flask import Flask, jsonify, request

HOST = "127.0.0.1"


# ---------------------------------------------------------------------------
# Cert tạm
# ---------------------------------------------------------------------------

def make_temp_pki(folder: Path) -> tuple[Path, Path, Path]:
    now = dt.datetime.now(dt.timezone.utc)
    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "G0.7 spike CA (tam)")])
    ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name)
          .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(now - dt.timedelta(minutes=5)).not_valid_after(now + dt.timedelta(hours=2))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.KeyUsage(digital_signature=True, key_cert_sign=True, crl_sign=True,
                                       content_commitment=False, key_encipherment=False,
                                       data_encipherment=False, key_agreement=False,
                                       encipher_only=False, decipher_only=False), critical=True)
          .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
          .sign(ca_key, hashes.SHA256()))
    leaf_key = ec.generate_private_key(ec.SECP256R1())
    leaf = (x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, HOST)]))
            .issuer_name(ca_name).public_key(leaf_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - dt.timedelta(minutes=5)).not_valid_after(now + dt.timedelta(hours=2))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(HOST))]), critical=False)
            .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
            .sign(ca_key, hashes.SHA256()))
    ca_path, cert_path, key_path = folder / "ca.crt", folder / "leaf.crt", folder / "leaf.key"
    ca_path.write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    cert_path.write_bytes(leaf.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(leaf_key.private_bytes(serialization.Encoding.PEM,
                                                serialization.PrivateFormat.PKCS8,
                                                serialization.NoEncryption()))
    return ca_path, cert_path, key_path


# ---------------------------------------------------------------------------
# Tín hiệu đánh thức dùng chung giữa hai pool
# ---------------------------------------------------------------------------

class Wake:
    """Mỗi máy một bộ đếm thế hệ; notify tăng bộ đếm và đánh thức mọi người chờ."""

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._gen: dict[int, int] = {}

    def wait(self, machine_id: int, timeout: float) -> bool:
        with self._cond:
            start = self._gen.get(machine_id, 0)
            return self._cond.wait_for(lambda: self._gen.get(machine_id, 0) != start, timeout)

    def notify(self, machine_id: int) -> None:
        with self._cond:
            self._gen[machine_id] = self._gen.get(machine_id, 0) + 1
            self._cond.notify_all()


# ---------------------------------------------------------------------------
# Hai app
# ---------------------------------------------------------------------------

def make_apps(wake: Wake, hang: float):
    admin = Flask("admin")
    agent = Flask("agent")
    counters = {"admin_ok": 0}
    lock = threading.Lock()

    @admin.post("/api/admin/login")
    def login():
        # Giả lập việc tốn CPU như pbkdf2 ở đăng nhập.
        import hashlib
        hashlib.pbkdf2_hmac("sha256", b"pw", b"salt", 20_000)
        with lock:
            counters["admin_ok"] += 1
        return jsonify(ok=False), 401

    @admin.post("/api/admin/notify/<int:machine_id>")
    def notify(machine_id: int):
        wake.notify(machine_id)
        return jsonify(ok=True)

    @agent.post("/api/agent/commands")
    def commands():
        body = request.get_json(force=True)
        machine_id = int(body["machine_id"])
        wait = min(float(body.get("wait", hang)), hang)
        t0 = time.monotonic()
        woken = wake.wait(machine_id, wait)
        return jsonify(machine_id=machine_id, woken=woken, waited=round(time.monotonic() - t0, 3),
                       commands=[{"kind": "noop"}] if woken else [])

    return admin, agent, counters


def make_server(app, port: int, threads: int, cert: Path, key: Path):
    srv = wsgi.Server((HOST, port), app, numthreads=threads, max=threads,
                      server_name="g0.7", timeout=60)
    adapter = BuiltinSSLAdapter(str(cert), str(key))
    adapter.context.minimum_version = ssl.TLSVersion.TLSv1_3
    srv.ssl_adapter = adapter
    srv.prepare()
    t = threading.Thread(target=srv.serve, daemon=True)
    t.start()
    return srv, srv.bind_addr[1]


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

def client_ctx(ca: Path, max_version=None) -> ssl.SSLContext:
    ctx = ssl.create_default_context(cafile=str(ca))
    if max_version is not None:
        ctx.maximum_version = max_version
    return ctx


def post(port: int, ctx: ssl.SSLContext, path: str, body: dict, timeout: float):
    conn = http.client.HTTPSConnection(HOST, port, context=ctx, timeout=timeout)
    try:
        conn.request("POST", path, body=json.dumps(body), headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        data = resp.read()
        return resp.status, data, conn.sock.version() if conn.sock else None
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10, help="số poll treo (giả định 10 vì chưa có Q9)")
    ap.add_argument("--hang", type=float, default=25.0)
    ap.add_argument("--wake-at", type=float, default=10.0)
    ap.add_argument("--admin-threads", type=int, default=8)
    ap.add_argument("--agent-threads", type=int, default=0, help="0 = n + 8")
    ap.add_argument("--flooders", type=int, default=32)
    args = ap.parse_args()
    n = args.n
    agent_threads = args.agent_threads or n + 8

    tmp = Path(tempfile.mkdtemp(prefix="g07_"))
    report: dict = {"n_poll": n, "hang_s": args.hang, "admin_threads": args.admin_threads,
                    "agent_threads": agent_threads, "flooders": args.flooders,
                    "python": sys.version.split()[0], "openssl": ssl.OPENSSL_VERSION}
    ok = True
    try:
        ca, cert, key = make_temp_pki(tmp)
        wake = Wake()
        admin_app, agent_app, counters = make_apps(wake, args.hang)
        admin_srv, admin_port = make_server(admin_app, 0, args.admin_threads, cert, key)
        agent_srv, agent_port = make_server(agent_app, 0, agent_threads, cert, key)
        ctx = client_ctx(ca)

        # Kiểm phụ: TLS 1.2 bị từ chối; route agent ở cổng quản trị là 404.
        try:
            post(agent_port, client_ctx(ca, ssl.TLSVersion.TLSv1_2), "/api/agent/commands",
                 {"machine_id": 999, "wait": 0}, 5)
            report["tls12_bi_tu_choi"] = False
            ok = False
        except (ssl.SSLError, ConnectionError, OSError) as exc:
            report["tls12_bi_tu_choi"] = True
            report["tls12_loi"] = type(exc).__name__
        status, _d, _v = post(admin_port, ctx, "/api/agent/commands", {"machine_id": 1, "wait": 0}, 5)
        report["agent_route_o_cong_quan_tri"] = status
        ok &= status == 404

        # Treo N poll.
        results: dict[int, dict] = {}
        t_start = time.monotonic()

        def poller(i: int):
            t0 = time.monotonic()
            try:
                status, data, ver = post(agent_port, ctx, "/api/agent/commands",
                                         {"machine_id": i, "wait": args.hang}, args.hang + 30)
                body = json.loads(data)
                results[i] = {"status": status, "tls": ver, "woken": body["woken"],
                              "elapsed": round(time.monotonic() - t0, 2)}
            except Exception as exc:  # noqa: BLE001 - ghi lại mọi lỗi để báo cáo
                results[i] = {"error": f"{type(exc).__name__}: {exc}",
                              "elapsed": round(time.monotonic() - t0, 2)}

        polls = [threading.Thread(target=poller, args=(i,)) for i in range(n)]
        for t in polls:
            t.start()

        # Flood cổng quản trị.
        stop = threading.Event()
        flood = {"sent": 0, "errors": 0, "lat": []}
        flock = threading.Lock()

        def flooder():
            fctx = client_ctx(ca)
            while not stop.is_set():
                t0 = time.monotonic()
                try:
                    post(admin_port, fctx, "/api/admin/login", {"u": "x", "p": "y"}, 30)
                    with flock:
                        flood["sent"] += 1
                        flood["lat"].append(time.monotonic() - t0)
                except Exception:  # noqa: BLE001
                    with flock:
                        flood["errors"] += 1

        flooders = [threading.Thread(target=flooder, daemon=True) for _ in range(args.flooders)]
        for t in flooders:
            t.start()

        # Đánh thức nửa sau.
        time.sleep(args.wake_at)
        woken_ids = list(range(n // 2, n))
        for i in woken_ids[:-1]:
            wake.notify(i)
        t0 = time.monotonic()
        status, _d, _v = post(admin_port, ctx, f"/api/admin/notify/{woken_ids[-1]}", {}, 30)
        report["notify_qua_http_cong_quan_tri"] = {"status": status,
                                                   "tre_s": round(time.monotonic() - t0, 2)}

        for t in polls:
            t.join(args.hang + 40)
        stop.set()
        for t in flooders:
            t.join(35)
        report["tong_thoi_gian_s"] = round(time.monotonic() - t_start, 2)

        lat = sorted(flood["lat"])
        report["flood_cong_quan_tri"] = {
            "request_xong": flood["sent"], "loi": flood["errors"],
            "p50_s": round(lat[len(lat) // 2], 3) if lat else None,
            "p95_s": round(lat[int(len(lat) * 0.95)], 3) if lat else None,
            "max_s": round(lat[-1], 3) if lat else None,
            "server_dem": counters["admin_ok"],
        }

        polls_ok = 0
        for i in range(n):
            r = results.get(i, {"error": "không có kết quả"})
            expect_woken = i in woken_ids
            good = (r.get("status") == 200 and r.get("tls") == "TLSv1.3"
                    and r.get("woken") is expect_woken)
            if good and expect_woken:
                good = r["elapsed"] < args.hang
            elif good:
                good = args.hang <= r["elapsed"] < args.hang + 2
            r["dat"] = good
            polls_ok += good
        report["polls"] = results
        report["poll_dat"] = f"{polls_ok}/{n}"
        ok &= polls_ok == n

        admin_srv.stop()
        agent_srv.stop()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        report["thu_muc_cert_tam_da_xoa"] = not tmp.exists()

    report["ket_qua"] = "DAT" if ok else "CHUA_DAT"
    print(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
