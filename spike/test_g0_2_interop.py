"""G0.2: liên thông byte-exact cryptography <-> PyHPKE, 1.000 lần mỗi chiều.

info = Tuple("fm1-req", SHA256(M)), aad rỗng.
Plaintext = LP(resp_key) ‖ LP(body), đúng hình dạng của FM1.

Chiều A (cryptography seal -> PyHPKE open):
- PyHPKE mở ra đúng từng byte plaintext;
- PyHPKE dẫn lại key và base_nonce từ enc, AES-GCM lại plaintext: ra đúng
  từng byte ct của cryptography (key schedule giống hệt).

Chiều B (PyHPKE seal -> cryptography open):
- cryptography mở ra đúng từng byte plaintext;
- PyHPKE dùng ikmE tất định, seal lại lần hai ra đúng enc và ct (kiểm phía
  tham chiếu tất định, để ct của chiều B cũng được so từng byte).
"""

from __future__ import annotations

import os
import random

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import fm1_ref as F
import pyhpke_ref as P

N = 1000
SEED = 20261008


def _m(rng: random.Random) -> bytes:
    return F.build_m({
        "audience": "fmx-" + rng.randbytes(4).hex(),
        "server_kid": rng.randbytes(8).hex(),
        "credential_kid": rng.choice([rng.randbytes(8).hex(), "enroll"]),
        "route_id": rng.choice(["AGENT_HELLO_PATH", "AGENT_COMMANDS_PATH", "AGENT_ORDERS_PATH"]),
        "attempt_id": os.urandom(16),
        "issued_at": rng.randrange(0, 2**63),
        "server_epoch_seen": rng.choice([b"", os.urandom(16)]),
    })


def _pt(rng: random.Random) -> bytes:
    size = rng.choice([0, 1, 2, 15, 16, 17, rng.randrange(0, 4096)])
    return F.inner_request(os.urandom(16), os.urandom(size))


def test_chieu_a_cryptography_seal_pyhpke_open():
    rng = random.Random(SEED)
    sk = F.x25519_priv(os.urandom(32))
    sk_raw, pk = F.raw_priv(sk), sk.public_key()
    so_lan = 0
    for _ in range(N):
        m = _m(rng)
        info = F.hpke_info(m)
        pt = _pt(rng)
        enc, ct = F.hpke_seal(pk, m, pt)
        assert len(enc) == 32 and len(ct) == len(pt) + 16
        assert P.open_(sk_raw, enc, info, ct) == pt
        ks = P.key_schedule(sk_raw, enc, info)
        assert AESGCM(ks["key"]).encrypt(ks["base_nonce"], pt, b"") == ct
        so_lan += 1
    assert so_lan == N


def test_chieu_b_pyhpke_seal_cryptography_open():
    rng = random.Random(SEED + 1)
    sk = F.x25519_priv(os.urandom(32))
    pk_raw = F.raw_pub(sk.public_key())
    so_lan = 0
    for _ in range(N):
        m = _m(rng)
        info = F.hpke_info(m)
        pt = _pt(rng)
        ikm_e = os.urandom(32)
        enc, ct = P.seal(pk_raw, info, pt, ikm_e=ikm_e)
        assert P.seal(pk_raw, info, pt, ikm_e=ikm_e) == (enc, ct)
        assert F.hpke_open(sk, m, enc, ct) == pt
        so_lan += 1
    assert so_lan == N


def test_info_duoi_64_byte():
    m = _m(random.Random(1))
    assert len(F.hpke_info(m)) == 4 + 7 + 4 + 32 == 47
