"""G0.5: chữ ký Ed25519 và response AES-128-GCM.

- Ed25519 trên Tuple("fm1-sig", M, enc, ct): đổi 1 byte ở bất kỳ đâu
  trong M, enc, ct hoặc sig là verify sai.
- Response: AES-128-GCM bằng resp_key, nonce 12 byte ngẫu nhiên,
  AAD = Tuple("fm1-resp", SHA256(M)). Đổi 1 byte là không mở được;
  mở bằng M khác (gói khác) là không mở được.
- 10.000 lần seal cùng resp_key: không lặp nonce.
"""

from __future__ import annotations

import os

import pytest

import fm1_ref as F

SIGN = F.ed25519_priv(bytes(range(32, 64)))
SIGN_PUB = SIGN.public_key()
KEM = F.x25519_priv(bytes(range(32)))
FIELDS = {
    "audience": "fmx-test", "server_kid": "a1b2c3d4e5f60718", "credential_kid": "0011223344556677",
    "route_id": "AGENT_HELLO_PATH", "attempt_id": bytes(range(16)), "issued_at": 1_790_000_000_000,
    "server_epoch_seen": b"",
}


def _parts():
    env, m = F.seal_request(FIELDS, b'{"agent_version":"0.1"}', bytes(16), KEM.public_key(), SIGN)
    m2, _f, enc, ct, sig = F.parse_request(env)
    assert m2 == m
    return m, enc, ct, sig


def _bump(data: bytes, i: int) -> bytes:
    b = bytearray(data)
    b[i] = (b[i] + 1) % 256
    return bytes(b)


def test_chu_ky_dung_thi_qua():
    m, enc, ct, sig = _parts()
    F.verify_request(SIGN_PUB, m, enc, ct, sig)


@pytest.mark.parametrize("which", ["m", "enc", "ct", "sig"])
def test_doi_1_byte_la_verify_sai(which):
    m, enc, ct, sig = _parts()
    parts = {"m": m, "enc": enc, "ct": ct, "sig": sig}
    for i in range(len(parts[which])):
        p = dict(parts)
        p[which] = _bump(parts[which], i)
        with pytest.raises(F.SignatureError):
            F.verify_request(SIGN_PUB, p["m"], p["enc"], p["ct"], p["sig"])


def test_ky_bang_nhan_khac_thi_sai():
    m, enc, ct, _sig = _parts()
    sig = SIGN.sign(F.tuple_(F.LABEL_REQ, m, enc, ct))
    with pytest.raises(F.SignatureError):
        F.verify_request(SIGN_PUB, m, enc, ct, sig)


def test_khoa_khac_thi_sai():
    m, enc, ct, sig = _parts()
    other = F.ed25519_priv(os.urandom(32)).public_key()
    with pytest.raises(F.SignatureError):
        F.verify_request(other, m, enc, ct, sig)


def test_response_mo_duoc_va_rang_buoc_m():
    m, *_ = _parts()
    key = os.urandom(16)
    inner = F.response_inner(FIELDS["attempt_id"], "ok", bytes(16), {"x": 1})
    env = F.seal_response(key, m, inner)
    assert F.open_response(key, m, env, FIELDS["attempt_id"]) == inner
    m_other = F.build_m({**FIELDS, "attempt_id": os.urandom(16)})
    with pytest.raises(F.OpenError):
        F.open_response(key, m_other, env, FIELDS["attempt_id"])
    with pytest.raises(F.OpenError):
        F.open_response(os.urandom(16), m, env, FIELDS["attempt_id"])
    with pytest.raises(F.BindingError):
        F.open_response(key, m, env, os.urandom(16))


def test_response_doi_1_byte_la_khong_mo_duoc():
    m, *_ = _parts()
    key = os.urandom(16)
    env = F.seal_response(key, m, F.response_inner(FIELDS["attempt_id"], "ok", bytes(16), {}))
    for i in range(len(env)):
        with pytest.raises(F.FM1Error):
            F.open_response(key, m, _bump(env, i), FIELDS["attempt_id"])


def test_10000_lan_seal_khong_lap_nonce():
    m, *_ = _parts()
    key = os.urandom(16)
    inner = F.response_inner(FIELDS["attempt_id"], "ok", bytes(16), {"commands": []})
    nonces = set()
    for _ in range(10_000):
        env = F.seal_response(key, m, inner)
        nonce, _ct = F.read_lps(env[2:], 2)
        nonces.add(nonce)
    assert len(nonces) == 10_000
