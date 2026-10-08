"""Bản tham chiếu FM1 cho spike G0. KHÔNG phải code chạy thật.

Mục đích:
- Chứng minh định dạng gói ở mục 4.2 của thiết kế làm được bằng
  `cryptography` (thư viện chạy thật).
- Sinh bộ vector C0.3 dùng chung cho server (S-FM1) và máy (A-NET).

S-FM1 sẽ viết lại `fm1_encoding.py` và `fm1_crypto.py` theo hợp đồng
`internal/contracts/fm1_wire.md`, không import file này.

Bố cục byte (bản nháp, chờ user chốt Q1):
- LP(x)            = uint32 big-endian độ dài ‖ x
- Tuple(nhãn, ...) = LP(nhãn) ‖ LP(trường 1) ‖ ... ‖ LP(trường n)
- Request          = ver(2) ‖ LP(M) ‖ LP(enc) ‖ LP(ct) ‖ LP(sig)
- Response         = ver(2) ‖ LP(nonce) ‖ LP(ct)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import struct

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hpke import AEAD, KDF, KEM, Suite

# ---------------------------------------------------------------------------
# Hằng
# ---------------------------------------------------------------------------

VER = b"\x00\x01"

LABEL_REQ = b"fm1-req"
LABEL_SIG = b"fm1-sig"
LABEL_RESP = b"fm1-resp"
LABEL_CMD = b"fm1-cmd"
LABEL_BUNDLE = b"fm1-bundle"
LABEL_PROOF = b"fm1-proof"
LABELS = (LABEL_REQ, LABEL_SIG, LABEL_RESP, LABEL_CMD, LABEL_BUNDLE, LABEL_PROOF)

DOMAIN = b"flexmix-fm1"
M_VERSION = 1
SUITE_NAME = b"X25519-HKDF-SHA256-AES-128-GCM/Ed25519"
ENROLL_KID = "enroll"

ENC_LEN = 32
SIG_LEN = 64
RESP_KEY_LEN = 16
ATTEMPT_ID_LEN = 16
EPOCH_LEN = 16
NONCE_LEN = 12
TAG_LEN = 16

M_MAX = 512
INFO_MAX = 64
# Trần mặc định cho thân JSON bên trong ct. ROUTE_POLICY đặt trần riêng từng route.
BODY_MAX_DEFAULT = 256 * 1024
# Phần cố định của ct request: LP(resp_key) + tiền tố LP(body) + tag GCM.
REQ_CT_OVERHEAD = 4 + RESP_KEY_LEN + 4 + TAG_LEN

_HPKE = Suite(KEM.X25519, KDF.HKDF_SHA256, AEAD.AES_128_GCM)

_ASCII_ID = re.compile(rb"^[a-z0-9][a-z0-9._-]{0,63}$")
_KID = re.compile(rb"^[a-z0-9]{1,32}$")
_ROUTE_ID = re.compile(rb"^AGENT_[A-Z0-9_]{1,52}_PATH$")

# Thứ tự trường của M. Đổi thứ tự là đổi định dạng: phải tăng M_VERSION.
M_FIELDS = (
    "domain",
    "version",
    "suite",
    "audience",
    "server_kid",
    "credential_kid",
    "method",
    "route_id",
    "attempt_id",
    "issued_at",
    "server_epoch_seen",
)


# ---------------------------------------------------------------------------
# Lỗi
# ---------------------------------------------------------------------------

class FM1Error(Exception):
    """Mọi lỗi FM1. `stage` cho biết bước nào từ chối."""

    stage = "fm1"


class FrameError(FM1Error):
    """Khung sai: độ dài, ver, trường M, JSON."""

    stage = "frame"


class SignatureError(FM1Error):
    """Chữ ký Ed25519 sai."""

    stage = "sig"


class OpenError(FM1Error):
    """HPKE hoặc AES-GCM không mở được."""

    stage = "open"


class BindingError(FM1Error):
    """Mở được nhưng không khớp attempt đang chờ."""

    stage = "binding"


# ---------------------------------------------------------------------------
# LP và Tuple
# ---------------------------------------------------------------------------

def lp(data: bytes) -> bytes:
    """Bọc một trường: 4 byte độ dài big-endian rồi tới nội dung."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("lp() chỉ nhận bytes")
    if len(data) > 0xFFFFFFFF:
        raise ValueError("trường quá dài")
    return struct.pack(">I", len(data)) + bytes(data)


def tuple_(label: bytes, *fields: bytes) -> bytes:
    """Tuple có nhãn. Nhãn phải là một trong sáu nhãn FM1."""
    if label not in LABELS:
        raise ValueError(f"nhãn lạ: {label!r}")
    return lp(label) + b"".join(lp(f) for f in fields)


def read_lps(buf: bytes, count: int, limits: tuple[int, ...] | None = None) -> list[bytes]:
    """Đọc đúng `count` trường LP và phải hết buffer. Thừa hay thiếu là lỗi."""
    out: list[bytes] = []
    pos = 0
    for i in range(count):
        if len(buf) - pos < 4:
            raise FrameError("thiếu tiền tố LP")
        (n,) = struct.unpack_from(">I", buf, pos)
        pos += 4
        if limits is not None and n > limits[i]:
            raise FrameError("trường vượt trần")
        if len(buf) - pos < n:
            raise FrameError("LP dài hơn phần còn lại")
        out.append(bytes(buf[pos:pos + n]))
        pos += n
    if pos != len(buf):
        raise FrameError("thừa byte sau khung")
    return out


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


# ---------------------------------------------------------------------------
# M
# ---------------------------------------------------------------------------

def build_m(fields: dict) -> bytes:
    """Dựng M từ dict. Kiểm mọi trường như khi parse."""
    raw = [
        DOMAIN,
        struct.pack(">H", M_VERSION),
        SUITE_NAME,
        fields["audience"].encode("ascii"),
        fields["server_kid"].encode("ascii"),
        fields["credential_kid"].encode("ascii"),
        fields.get("method", "POST").encode("ascii"),
        fields["route_id"].encode("ascii"),
        fields["attempt_id"],
        struct.pack(">Q", fields["issued_at"]),
        fields.get("server_epoch_seen", b""),
    ]
    m = b"".join(lp(x) for x in raw)
    parse_m(m)  # tự kiểm: không dựng ra M mà chính mình không nhận
    return m


def parse_m(m: bytes) -> dict:
    """Parse và kiểm M. Sai bất cứ chỗ nào thì FrameError."""
    if len(m) > M_MAX:
        raise FrameError("M vượt trần")
    parts = read_lps(m, len(M_FIELDS), (32, 2, 64, 64, 32, 32, 8, 64, 16, 8, 16))
    (domain, version, suite, audience, server_kid, cred_kid, method, route_id,
     attempt_id, issued_at, epoch_seen) = parts
    if domain != DOMAIN:
        raise FrameError("domain sai")
    if len(version) != 2 or struct.unpack(">H", version)[0] != M_VERSION:
        raise FrameError("version sai")
    if suite != SUITE_NAME:
        raise FrameError("suite sai")
    if not _ASCII_ID.match(audience):
        raise FrameError("audience sai")
    if not _KID.match(server_kid):
        raise FrameError("server_kid sai")
    if not _KID.match(cred_kid):
        raise FrameError("credential_kid sai")
    if method != b"POST":
        raise FrameError("method sai")
    if not _ROUTE_ID.match(route_id):
        raise FrameError("route_id sai")
    if len(attempt_id) != ATTEMPT_ID_LEN:
        raise FrameError("attempt_id sai độ dài")
    if len(issued_at) != 8:
        raise FrameError("issued_at sai độ dài")
    if len(epoch_seen) not in (0, EPOCH_LEN):
        raise FrameError("server_epoch_seen sai độ dài")
    return {
        "audience": audience.decode("ascii"),
        "server_kid": server_kid.decode("ascii"),
        "credential_kid": cred_kid.decode("ascii"),
        "method": "POST",
        "route_id": route_id.decode("ascii"),
        "attempt_id": attempt_id,
        "issued_at": struct.unpack(">Q", issued_at)[0],
        "server_epoch_seen": epoch_seen,
    }


def hpke_info(m: bytes) -> bytes:
    info = tuple_(LABEL_REQ, sha256(m))
    assert len(info) <= INFO_MAX
    return info


def sig_input(m: bytes, enc: bytes, ct: bytes) -> bytes:
    return tuple_(LABEL_SIG, m, enc, ct)


def resp_aad(m: bytes) -> bytes:
    return tuple_(LABEL_RESP, sha256(m))


# ---------------------------------------------------------------------------
# JSON chặt
# ---------------------------------------------------------------------------

def _no_dup(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise FrameError("JSON có khoá trùng")
        out[k] = v
    return out


def _no_const(name):
    raise FrameError(f"JSON có {name}")


def strict_json(data: bytes, limit: int = BODY_MAX_DEFAULT) -> dict:
    """Parse JSON: UTF-8, object ở gốc, không khoá trùng, không NaN/Infinity."""
    if len(data) > limit:
        raise FrameError("JSON vượt trần")
    try:
        text = data.decode("utf-8")
        obj = json.loads(text, object_pairs_hook=_no_dup, parse_constant=_no_const)
    except FrameError:
        raise
    except (UnicodeDecodeError, ValueError) as exc:
        raise FrameError("JSON sai") from exc
    if not isinstance(obj, dict):
        raise FrameError("gốc JSON phải là object")
    return obj


def canonical_json(obj: dict) -> bytes:
    """JSON gọn, sắp khoá: dùng cho vector để ra cùng byte."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


# ---------------------------------------------------------------------------
# Khoá
# ---------------------------------------------------------------------------

def x25519_priv(raw: bytes) -> X25519PrivateKey:
    return X25519PrivateKey.from_private_bytes(raw)


def x25519_pub(raw: bytes) -> X25519PublicKey:
    return X25519PublicKey.from_public_bytes(raw)


def ed25519_priv(raw: bytes) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(raw)


def ed25519_pub(raw: bytes) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(raw)


def raw_pub(key) -> bytes:
    return key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def raw_priv(key) -> bytes:
    return key.private_bytes(serialization.Encoding.Raw,
                             serialization.PrivateFormat.Raw,
                             serialization.NoEncryption())


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

def hpke_seal(server_kem_pub: X25519PublicKey, m: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    """HPKE Base single-shot bằng cryptography. Trả (enc, ct)."""
    out = _HPKE.encrypt(plaintext, server_kem_pub, info=hpke_info(m))
    return out[:ENC_LEN], out[ENC_LEN:]


def hpke_open(server_kem_priv: X25519PrivateKey, m: bytes, enc: bytes, ct: bytes) -> bytes:
    try:
        return _HPKE.decrypt(enc + ct, server_kem_priv, info=hpke_info(m))
    except InvalidTag as exc:
        raise OpenError("HPKE không mở được") from exc


def inner_request(resp_key: bytes, body: bytes) -> bytes:
    if len(resp_key) != RESP_KEY_LEN:
        raise ValueError("resp_key phải 16 byte")
    return lp(resp_key) + lp(body)


def split_inner_request(pt: bytes, body_limit: int = BODY_MAX_DEFAULT) -> tuple[bytes, bytes]:
    resp_key, body = read_lps(pt, 2, (RESP_KEY_LEN, body_limit))
    if len(resp_key) != RESP_KEY_LEN:
        raise FrameError("resp_key sai độ dài")
    return resp_key, body


def frame_request(m: bytes, enc: bytes, ct: bytes, sig: bytes) -> bytes:
    return VER + lp(m) + lp(enc) + lp(ct) + lp(sig)


def seal_request(m_fields: dict, body: bytes, resp_key: bytes,
                 server_kem_pub: X25519PublicKey,
                 machine_sign_priv: Ed25519PrivateKey) -> tuple[bytes, bytes]:
    """Phía máy: dựng M, HPKE seal, ký. Trả (envelope, M)."""
    m = build_m(m_fields)
    enc, ct = hpke_seal(server_kem_pub, m, inner_request(resp_key, body))
    sig = machine_sign_priv.sign(sig_input(m, enc, ct))
    return frame_request(m, enc, ct, sig), m


def parse_request(env: bytes, body_limit: int = BODY_MAX_DEFAULT) -> tuple[bytes, dict, bytes, bytes, bytes]:
    """Bước rẻ: kiểm khung và M. Không đụng mật mã. Trả (M, M đã parse, enc, ct, sig)."""
    if len(env) < 2 or env[:2] != VER:
        raise FrameError("ver sai")
    m, enc, ct, sig = read_lps(env[2:], 4, (M_MAX, ENC_LEN, body_limit + REQ_CT_OVERHEAD, SIG_LEN))
    if len(enc) != ENC_LEN or len(sig) != SIG_LEN:
        raise FrameError("enc hoặc sig sai độ dài")
    if len(ct) < REQ_CT_OVERHEAD:
        raise FrameError("ct quá ngắn")
    return m, parse_m(m), enc, ct, sig


def verify_request(machine_sign_pub: Ed25519PublicKey, m: bytes, enc: bytes, ct: bytes, sig: bytes) -> None:
    try:
        machine_sign_pub.verify(sig, sig_input(m, enc, ct))
    except InvalidSignature as exc:
        raise SignatureError("chữ ký sai") from exc


def open_request(env: bytes, server_kem_priv: X25519PrivateKey,
                 machine_sign_pub: Ed25519PublicKey,
                 body_limit: int = BODY_MAX_DEFAULT) -> tuple[dict, bytes, bytes, dict]:
    """Phía server, phần mật mã của pipeline 4.4 (không gồm tra kid, giờ, claim).

    Trả (M đã parse, M thô, resp_key, body JSON).
    """
    m, fields, enc, ct, sig = parse_request(env, body_limit)
    verify_request(machine_sign_pub, m, enc, ct, sig)
    pt = hpke_open(server_kem_priv, m, enc, ct)
    resp_key, body = split_inner_request(pt, body_limit)
    return fields, m, resp_key, strict_json(body, body_limit)


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

def seal_response(resp_key: bytes, m: bytes, inner: dict, nonce: bytes | None = None) -> bytes:
    """Phía server. Nonce ngẫu nhiên mỗi lần; chỉ vector mới truyền nonce cố định."""
    if nonce is None:
        nonce = os.urandom(NONCE_LEN)
    if len(nonce) != NONCE_LEN:
        raise ValueError("nonce phải 12 byte")
    ct = AESGCM(resp_key).encrypt(nonce, canonical_json(inner), resp_aad(m))
    return VER + lp(nonce) + lp(ct)


def response_inner(attempt_id: bytes, status: str, server_epoch: bytes, body: dict) -> dict:
    return {
        "attempt_id": attempt_id.hex(),
        "status": status,
        "server_epoch": server_epoch.hex(),
        "body": body,
    }


def open_response(resp_key: bytes, m: bytes, env: bytes, expected_attempt_id: bytes,
                  body_limit: int = BODY_MAX_DEFAULT) -> dict:
    """Phía máy: mở bằng resp_key của attempt đang chờ, kiểm attempt_id."""
    if len(env) < 2 or env[:2] != VER:
        raise FrameError("ver sai")
    nonce, ct = read_lps(env[2:], 2, (NONCE_LEN, body_limit + 1024 + TAG_LEN))
    if len(nonce) != NONCE_LEN or len(ct) < TAG_LEN:
        raise FrameError("nonce hoặc ct sai độ dài")
    try:
        pt = AESGCM(resp_key).decrypt(nonce, ct, resp_aad(m))
    except InvalidTag as exc:
        raise OpenError("response không mở được") from exc
    inner = strict_json(pt, body_limit + 1024)
    if set(inner) != {"attempt_id", "status", "server_epoch", "body"}:
        raise FrameError("inner thiếu hoặc thừa trường")
    if inner["attempt_id"] != expected_attempt_id.hex():
        raise BindingError("attempt_id không khớp")
    if not isinstance(inner["status"], str) or not isinstance(inner["body"], dict):
        raise FrameError("status hoặc body sai kiểu")
    return inner


# ---------------------------------------------------------------------------
# Fingerprint lệnh (dùng ở C0.6)
# ---------------------------------------------------------------------------

def command_fingerprint(machine_id: int, kind: str, args_bytes: bytes) -> bytes:
    """SHA256(Tuple("fm1-cmd", machine_id, kind, args_bytes)). machine_id: uint32 BE."""
    return sha256(tuple_(LABEL_CMD, struct.pack(">I", machine_id), kind.encode("ascii"), args_bytes))
