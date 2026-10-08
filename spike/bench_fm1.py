"""G0.6: benchmark một vòng FM1. Chạy trên Pi thật để lấy số cho cổng G0.

Một vòng agent: sinh attempt_id và resp_key, dựng M, HPKE seal (sinh khoá
tạm bên trong), ký Ed25519; sau đó mở response.
Một vòng server: parse khung, verify, HPKE open, tách resp_key, parse JSON,
seal response.

In ra p50, p95, max (ms), thời gian CPU, và thông tin máy để chép vào
`internal/plan/bang_chung/G0.md`.

Chạy: python spike/bench_fm1.py [--rounds 1000] [--body 2048]
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cryptography  # noqa: E402

import fm1_ref as F  # noqa: E402


def pct(sorted_ms: list[float], p: float) -> float:
    return sorted_ms[min(len(sorted_ms) - 1, int(len(sorted_ms) * p))]


def machine_info() -> dict:
    info = {
        "python": sys.version.split()[0],
        "cryptography": cryptography.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or None,
        "cpu_count": os.cpu_count(),
    }
    model = Path("/proc/device-tree/model")
    if model.exists():
        info["pi_model"] = model.read_bytes().rstrip(b"\x00").decode(errors="replace")
    os_release = Path("/etc/os-release")
    if os_release.exists():
        for line in os_release.read_text().splitlines():
            if line.startswith("PRETTY_NAME="):
                info["os"] = line.split("=", 1)[1].strip('"')
    return info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=1000)
    ap.add_argument("--body", type=int, default=2048, help="cỡ thân JSON request (byte)")
    args = ap.parse_args()

    server_kem = F.x25519_priv(os.urandom(32))
    server_pub = server_kem.public_key()
    machine_sign = F.ed25519_priv(os.urandom(32))
    machine_pub = machine_sign.public_key()
    body = json.dumps({"pad": "x" * max(0, args.body - 12)}).encode()
    epoch = os.urandom(16)
    resp_body = {"commands": [], "target_menu_version": 12}

    agent_ms: list[float] = []
    server_ms: list[float] = []
    open_ms: list[float] = []
    cpu0 = time.process_time()
    wall0 = time.perf_counter()
    for _ in range(args.rounds):
        # Vòng agent: seal + ký.
        t = time.perf_counter()
        attempt_id, resp_key = os.urandom(16), os.urandom(16)
        env, m = F.seal_request({
            "audience": "fmx-bench", "server_kid": "a1b2c3d4e5f60718",
            "credential_kid": "0011223344556677", "route_id": "AGENT_COMMANDS_PATH",
            "attempt_id": attempt_id, "issued_at": int(time.time() * 1000),
            "server_epoch_seen": epoch,
        }, body, resp_key, server_pub, machine_sign)
        agent_ms.append((time.perf_counter() - t) * 1000)

        # Vòng server: parse, verify, open, seal.
        t = time.perf_counter()
        fields, m_srv, key_srv, _body = F.open_request(env, server_kem, machine_pub)
        resp = F.seal_response(key_srv, m_srv, F.response_inner(fields["attempt_id"], "ok", epoch, resp_body))
        server_ms.append((time.perf_counter() - t) * 1000)

        # Agent mở response.
        t = time.perf_counter()
        F.open_response(resp_key, m, resp, attempt_id)
        open_ms.append((time.perf_counter() - t) * 1000)
    wall = time.perf_counter() - wall0
    cpu = time.process_time() - cpu0

    def summary(xs: list[float]) -> dict:
        s = sorted(xs)
        return {"p50_ms": round(pct(s, 0.50), 3), "p95_ms": round(pct(s, 0.95), 3),
                "max_ms": round(s[-1], 3), "mean_ms": round(statistics.fmean(s), 3)}

    agent_total = [a + o for a, o in zip(agent_ms, open_ms)]
    out = {
        "may": machine_info(),
        "rounds": args.rounds,
        "body_bytes": len(body),
        "agent_seal_ky": summary(agent_ms),
        "agent_mo_response": summary(open_ms),
        "agent_ca_vong": summary(agent_total),
        "server_ca_vong": summary(server_ms),
        "wall_s": round(wall, 3),
        "cpu_s": round(cpu, 3),
        "cpu_phan_tram_mot_nhan": round(100 * cpu / wall, 1) if wall else None,
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
