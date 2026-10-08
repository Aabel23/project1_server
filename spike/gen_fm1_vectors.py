"""Sinh bộ vector FM1 cho hợp đồng C0.3: tests/vectors/fm1/*.json.

Vector tất định để chạy lại ra đúng từng byte:
- khoá cố định, dẫn từ SHA256 của một chuỗi ghi rõ (chỉ dùng cho test);
- HPKE seal bằng PyHPKE với ikmE cố định (G0.2 đã chứng minh cryptography
  mở được đúng từng byte gói do PyHPKE seal và ngược lại);
- Ed25519 vốn tất định; nonce response cố định.

Chạy: .venv/Scripts/python spike/gen_fm1_vectors.py [thư_mục_ra]
"""

from __future__ import annotations

import base64
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import fm1_ref as F  # noqa: E402
import pyhpke_ref as P  # noqa: E402

OUT_DEFAULT = Path(__file__).resolve().parent.parent / "tests" / "vectors" / "fm1"

NOW_MS = 1_791_500_000_000          # giờ server giả định khi kiểm vector
WINDOW_MS = 120_000                 # W = 120 s
AUDIENCE = "fmx-vector"
SERVER_KID = "5e7e1d0000000001"
MACHINE_KID = "a9e1000000000003"
EPOCH = bytes.fromhex("e90c0000000000000000000000000001")


def _seed(text: str) -> bytes:
    return F.sha256(("fm1-vector/" + text).encode())


SERVER_KEM_SK = _seed("server-kem")
MACHINE_SIGN_SK = _seed("machine-sign")
ENROLL_SIGN_SK = _seed("enroll-new-machine-sign")

SERVER_KEM_PK = F.raw_pub(F.x25519_priv(SERVER_KEM_SK).public_key())
MACHINE_SIGN_PK = F.raw_pub(F.ed25519_priv(MACHINE_SIGN_SK).public_key())
ENROLL_SIGN_PK = F.raw_pub(F.ed25519_priv(ENROLL_SIGN_SK).public_key())


def _keys(sign_sk: bytes, sign_pk: bytes) -> dict:
    return {
        "server_kem_sk_hex": SERVER_KEM_SK.hex(),
        "server_kem_pk_hex": SERVER_KEM_PK.hex(),
        "machine_sign_sk_hex": sign_sk.hex(),
        "machine_sign_pk_hex": sign_pk.hex(),
    }


def _fields(name: str, route_id: str, cred_kid: str = MACHINE_KID, issued_at: int = NOW_MS - 1500,
            epoch: bytes = EPOCH) -> dict:
    return {
        "audience": AUDIENCE,
        "server_kid": SERVER_KID,
        "credential_kid": cred_kid,
        "method": "POST",
        "route_id": route_id,
        "attempt_id": _seed("attempt/" + name)[:16],
        "issued_at": issued_at,
        "server_epoch_seen": epoch,
    }


def _fields_json(f: dict) -> dict:
    out = dict(f)
    out["attempt_id"] = f["attempt_id"].hex()
    out["server_epoch_seen"] = f["server_epoch_seen"].hex()
    return out


def _raw_m(f: dict, **override: bytes) -> bytes:
    """Dựng M thô, cho phép thay byte của một trường để tạo M sai."""
    raw = {
        "domain": F.DOMAIN,
        "version": struct.pack(">H", F.M_VERSION),
        "suite": F.SUITE_NAME,
        "audience": f["audience"].encode(),
        "server_kid": f["server_kid"].encode(),
        "credential_kid": f["credential_kid"].encode(),
        "method": f["method"].encode(),
        "route_id": f["route_id"].encode(),
        "attempt_id": f["attempt_id"],
        "issued_at": struct.pack(">Q", f["issued_at"]),
        "server_epoch_seen": f["server_epoch_seen"],
    }
    raw.update(override)
    return b"".join(F.lp(raw[k]) for k in F.M_FIELDS)


def _seal(name: str, m: bytes, pt: bytes, sign_sk: bytes, info: bytes | None = None,
          sig_label: bytes = F.LABEL_SIG) -> tuple[bytes, bytes, bytes, bytes]:
    ikm_e = _seed("ikmE/" + name)
    enc, ct = P.seal(SERVER_KEM_PK, F.hpke_info(m) if info is None else info, pt, ikm_e=ikm_e)
    sig = F.ed25519_priv(sign_sk).sign(F.tuple_(sig_label, m, enc, ct))
    return enc, ct, sig, ikm_e


def request_vector(name: str, path: str, f: dict, body: bytes, *, expect: str = "accept",
                   stage: str | None = None, note: str, sign: str = "machine",
                   m: bytes | None = None, pt: bytes | None = None, info: bytes | None = None,
                   sig_label: bytes = F.LABEL_SIG, mutate=None, verify_with: str | None = None) -> dict:
    sign_sk, sign_pk = (MACHINE_SIGN_SK, MACHINE_SIGN_PK) if sign == "machine" else (ENROLL_SIGN_SK, ENROLL_SIGN_PK)
    verify_pk = sign_pk if verify_with is None else MACHINE_SIGN_PK
    resp_key = _seed("resp_key/" + name)[:16]
    m = _raw_m(f) if m is None else m
    pt = F.inner_request(resp_key, body) if pt is None else pt
    enc, ct, sig, ikm_e = _seal(name, m, pt, sign_sk, info, sig_label)
    env = F.frame_request(m, enc, ct, sig)
    if mutate is not None:
        env = mutate(env, m, enc, ct, sig)
    v = {
        "_ghi_chu": note,
        "name": name,
        "kind": "request",
        "expect": expect,
        "stage": stage,
        "path": path,
        "server_now_ms": NOW_MS,
        "window_ms": WINDOW_MS,
        "server_audience": AUDIENCE,
        "server_kid": SERVER_KID,
        "keys": _keys(sign_sk, verify_pk),
        "m_fields": _fields_json(f),
        "m_hex": m.hex(),
        "ikm_e_hex": ikm_e.hex(),
        "enc_hex": enc.hex(),
        "ct_hex": ct.hex(),
        "sig_hex": sig.hex(),
        "resp_key_hex": resp_key.hex(),
        "body_utf8": body.decode("utf-8", errors="replace"),
        "request_hex": env.hex(),
    }
    return v


def add_response(v: dict, status: str, body: dict) -> dict:
    m = bytes.fromhex(v["m_hex"])
    resp_key = bytes.fromhex(v["resp_key_hex"])
    nonce = _seed("nonce/" + v["name"])[:12]
    inner = F.response_inner(bytes.fromhex(v["m_fields"]["attempt_id"]), status, EPOCH, body)
    v["response"] = {
        "nonce_hex": nonce.hex(),
        "aad_hex": F.resp_aad(m).hex(),
        "inner": inner,
        "inner_json_utf8": F.canonical_json(inner).decode(),
        "response_hex": F.seal_response(resp_key, m, inner, nonce=nonce).hex(),
    }
    return v


def response_reject(name: str, base: dict, note: str, stage: str, *, m: bytes | None = None,
                    resp_key: bytes | None = None, inner: dict | None = None,
                    expected_attempt: bytes | None = None, raw_inner: bytes | None = None,
                    mutate=None) -> dict:
    m_true = bytes.fromhex(base["m_hex"])
    key = bytes.fromhex(base["resp_key_hex"])
    nonce = _seed("nonce/" + name)[:12]
    seal_m = m_true if m is None else m
    seal_key = key if resp_key is None else resp_key
    inner = inner if inner is not None else base["response"]["inner"]
    if raw_inner is None:
        env = F.seal_response(seal_key, seal_m, inner, nonce=nonce)
    else:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        env = F.VER + F.lp(nonce) + F.lp(AESGCM(seal_key).encrypt(nonce, raw_inner, F.resp_aad(seal_m)))
    if mutate is not None:
        env = mutate(env)
    attempt = bytes.fromhex(base["m_fields"]["attempt_id"]) if expected_attempt is None else expected_attempt
    return {
        "_ghi_chu": note,
        "name": name,
        "kind": "response",
        "expect": "reject",
        "stage": stage,
        "m_hex": base["m_hex"],
        "resp_key_hex": base["resp_key_hex"],
        "expected_attempt_id_hex": attempt.hex(),
        "response_hex": env.hex(),
    }


def _flip(env: bytes, i: int) -> bytes:
    b = bytearray(env)
    b[i] ^= 0x01
    return bytes(b)


def build() -> list[dict]:
    vs: list[dict] = []

    # ---------------- Hợp lệ ----------------
    hello = request_vector(
        "ok_hello", "/api/agent/hello", _fields("ok_hello", "AGENT_HELLO_PATH"),
        F.canonical_json({"agent_version": "0.1.0",
                          "applied": {"epoch": EPOCH.hex(), "version": 7, "sha256": "00" * 32},
                          "results": []}),
        note="Hello hợp lệ của máy đã ghép.")
    target = {"server_epoch": EPOCH.hex(), "version": 8, "sha256": "00" * 32}
    vs.append(add_response(hello, "ok", {"target_menu_version": target,
                                        "server_epoch": EPOCH.hex(), "server_time": NOW_MS}))

    cmds = request_vector(
        "ok_commands", "/api/agent/commands", _fields("ok_commands", "AGENT_COMMANDS_PATH"),
        F.canonical_json({"wait": 25}), note="Long-poll hợp lệ.")
    vs.append(add_response(cmds, "ok", {"commands": [{
        "command_id": "00112233445566778899aabbccddeeff", "kind": "ingredients.read", "args": {},
        "fingerprint": F.command_fingerprint(3, "ingredients.read", b"{}").hex(), "ttl_ms": 5000}],
        "target_menu_version": target}))

    enroll_f = _fields("ok_enroll", "AGENT_ENROLL_PATH", cred_kid=F.ENROLL_KID, epoch=b"")
    enroll = request_vector(
        "ok_enroll", "/api/agent/enroll", enroll_f,
        F.canonical_json({"pubkey": base64.b64encode(ENROLL_SIGN_PK).decode("ascii"),
                          "install_uuid": "3f6c2a7e-0000-4000-8000-000000000001", "proof": "00" * 32}),
        sign="enroll",
        note="Enroll: credential_kid = enroll, ký bằng khoá mới, chưa biết epoch (rỗng). "
             "proof ở đây là giá trị giả; kiểm proof là việc của M-KEY, không thuộc vector FM1.")
    vs.append(add_response(enroll, "ok", {"kid": MACHINE_KID, "generation": 1}))

    revoked = request_vector(
        "ok_revoked_notice", "/api/agent/stock", _fields("ok_revoked_notice", "AGENT_STOCK_PATH"),
        F.canonical_json({"stock": [], "out_of_stock": []}),
        note="Gói hợp lệ về mật mã; server trả thông báo thu hồi đã seal (status revoked).")
    vs.append(add_response(revoked, "revoked", {}))

    # ---------------- Request phải bị từ chối ----------------
    def rej(name, stage, note, **kw):
        path = kw.pop("path", "/api/agent/hello")
        f = kw.pop("f", None) or _fields(name, "AGENT_HELLO_PATH")
        body = kw.pop("body", F.canonical_json({"agent_version": "0.1.0"}))
        vs.append(request_vector(name, path, f, body, expect="reject", stage=stage, note=note, **kw))

    rej("rej_ver", "frame", "ver = 0x0002.",
        mutate=lambda env, *a: b"\x00\x02" + env[2:])
    rej("rej_trailing_byte", "frame", "Thừa 1 byte sau khung.",
        mutate=lambda env, *a: env + b"\x00")
    rej("rej_truncated", "frame", "Cắt mất byte cuối của sig.",
        mutate=lambda env, *a: env[:-1])
    rej("rej_lp_overflow", "frame", "Tiền tố LP(M) ghi dài hơn phần còn lại.",
        mutate=lambda env, *a: env[:2] + struct.pack(">I", 0xFFFFFF) + env[6:])
    f = _fields("rej_route_id_lower", "AGENT_HELLO_PATH")
    rej("rej_route_id_lower", "frame", "route_id viết thường, sai ngữ pháp.",
        m=_raw_m(f, route_id=b"agent_hello_path"), f=f)
    f = _fields("rej_method_get", "AGENT_HELLO_PATH")
    rej("rej_method_get", "frame", "method trong M là GET.", m=_raw_m(f, method=b"GET"), f=f)
    f = _fields("rej_epoch_len", "AGENT_HELLO_PATH")
    rej("rej_epoch_len", "frame", "server_epoch_seen dài 8 byte.",
        m=_raw_m(f, server_epoch_seen=b"\x00" * 8), f=f)
    f = _fields("rej_audience_other", "AGENT_HELLO_PATH")
    f2 = dict(f, audience="fmx-other")
    rej("rej_audience_other", "audience", "audience của hệ khác.", f=f2)
    rej("rej_route_mismatch", "route",
        "route_id = AGENT_STOCK_PATH nhưng gửi tới /api/agent/hello (đem gói route này dùng cho route khác).",
        f=_fields("rej_route_mismatch", "AGENT_STOCK_PATH"))
    rej("rej_route_unknown", "route", "route_id hợp ngữ pháp nhưng không có trong ROUTE_POLICY.",
        f=_fields("rej_route_unknown", "AGENT_HEARTBEAT_PATH"), path="/api/agent/heartbeat")
    rej("rej_time_old", "time", "issued_at cũ hơn giờ server quá W.",
        f=_fields("rej_time_old", "AGENT_HELLO_PATH", issued_at=NOW_MS - WINDOW_MS - 1))
    rej("rej_time_future", "time", "issued_at vượt giờ server quá W.",
        f=_fields("rej_time_future", "AGENT_HELLO_PATH", issued_at=NOW_MS + WINDOW_MS + 1))

    def flip_in(field):
        def mut(env, m, enc, ct, sig):
            offsets = {"m": 2 + 4 + len(m) - 40,  # một byte trong attempt_id
                       "enc": 2 + 4 + len(m) + 4,
                       "ct": 2 + 4 + len(m) + 4 + len(enc) + 4 + 5,
                       "sig": len(env) - 1}
            return _flip(env, offsets[field])
        return mut

    for field in ("m", "enc", "ct", "sig"):
        rej(f"rej_flip_{field}", "sig", f"Đổi 1 bit trong {field}: chữ ký phải sai.", mutate=flip_in(field))
    rej("rej_sig_label", "sig", "Ký bằng nhãn fm1-req thay fm1-sig.", sig_label=F.LABEL_REQ)
    rej("rej_wrong_signer", "sig", "Ký bằng khoá của máy khác (khoá enroll mới), kid vẫn là máy 3.",
        sign="enroll", verify_with="machine")
    f = _fields("rej_info_other_m", "AGENT_HELLO_PATH")
    other_m = _raw_m(dict(f, attempt_id=b"\xff" * 16))
    rej("rej_info_other_m", "open",
        "ct mã hoá với info của một M khác; chữ ký đúng trên (M, enc, ct). HPKE phải không mở được.",
        f=f, info=F.hpke_info(other_m))
    rej("rej_resp_key_short", "frame", "Bên trong ct, resp_key chỉ 15 byte.",
        pt=F.lp(b"\x01" * 15) + F.lp(b"{}"))
    rej("rej_inner_trailing", "frame", "Bên trong ct thừa byte sau LP(body).",
        pt=F.inner_request(b"\x02" * 16, b"{}") + b"\x00")
    rej("rej_json_dup_key", "frame", "Body JSON có khoá trùng.", body=b'{"wait":1,"wait":25}')
    rej("rej_json_nan", "frame", "Body JSON có NaN.", body=b'{"wait":NaN}')
    rej("rej_json_array", "frame", "Gốc JSON là mảng.", body=b"[]")
    rej("rej_json_not_utf8", "frame", "Body không phải UTF-8.", body=b'{"a":"\xff"}')

    # ---------------- Response phải bị từ chối ----------------
    other_m = bytes.fromhex(request_vector("tmp", "/api/agent/hello", _fields("other", "AGENT_HELLO_PATH"),
                                           b"{}", note="")["m_hex"])
    vs.append(response_reject("resp_rej_aad_other_m", hello, "Seal với AAD của một M khác.", "open", m=other_m))
    vs.append(response_reject("resp_rej_other_key", hello, "Seal bằng resp_key khác.", "open",
                              resp_key=b"\x07" * 16))
    vs.append(response_reject("resp_rej_flip_ct", hello, "Đổi 1 bit trong ct.", "open",
                              mutate=lambda env: _flip(env, len(env) - 3)))
    vs.append(response_reject("resp_rej_flip_nonce", hello, "Đổi 1 bit trong nonce.", "open",
                              mutate=lambda env: _flip(env, 2 + 4)))
    vs.append(response_reject("resp_rej_ver", hello, "ver = 0x0002.", "frame",
                              mutate=lambda env: b"\x00\x02" + env[2:]))
    vs.append(response_reject("resp_rej_attempt", hello, "Mở được nhưng attempt_id không khớp attempt đang chờ.",
                              "binding", expected_attempt=b"\x05" * 16))
    inner_extra = dict(hello["response"]["inner"], extra=1)
    vs.append(response_reject("resp_rej_extra_field", hello, "inner có trường lạ.", "frame", inner=inner_extra))
    vs.append(response_reject("resp_rej_dup_key", hello, "inner JSON có khoá trùng.", "frame",
                              raw_inner=b'{"attempt_id":"00","attempt_id":"01","status":"ok",'
                                        b'"server_epoch":"00","body":{}}'))
    return vs


def write(out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for v in build():
        p = out / f"{v['name']}.json"
        p.write_text(json.dumps(v, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        written.append(p)
    return written


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT_DEFAULT
    sys.stdout.reconfigure(encoding="utf-8")
    files = write(target)
    print(f"Đã ghi {len(files)} vector vào {target}")
