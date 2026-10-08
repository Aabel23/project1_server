"""PyHPKE làm bản tham chiếu độc lập cho spike G0. Chỉ dùng trong test.

Một số hàm đọc thuộc tính nội bộ của PyHPKE (`_kem`, `_key_schedule`)
để lấy khoá và base_nonce của context. Việc này chỉ để kiểm byte-exact
trong spike; code chạy thật không dùng PyHPKE.
"""

from __future__ import annotations

import pyhpke
from pyhpke.consts import Mode

SUITE = pyhpke.CipherSuite.new(
    pyhpke.KEMId.DHKEM_X25519_HKDF_SHA256,
    pyhpke.KDFId.HKDF_SHA256,
    pyhpke.AEADId.AES128_GCM,
)


def priv(raw: bytes):
    return SUITE.kem.deserialize_private_key(raw)


def pub(raw: bytes):
    return SUITE.kem.deserialize_public_key(raw)


def derive_key_pair(ikm: bytes):
    return SUITE.kem.derive_key_pair(ikm)


def seal(pk_raw: bytes, info: bytes, pt: bytes, ikm_e: bytes | None = None) -> tuple[bytes, bytes]:
    """Seal một lần (seq 0, aad rỗng). Có ikm_e thì khoá tạm tất định."""
    eks = derive_key_pair(ikm_e) if ikm_e is not None else None
    enc, ctx = SUITE.create_sender_context(pub(pk_raw), info=info, eks=eks)
    return enc, ctx.seal(pt, aad=b"")


def open_(sk_raw: bytes, enc: bytes, info: bytes, ct: bytes) -> bytes:
    ctx = SUITE.create_recipient_context(enc, priv(sk_raw), info=info)
    return ctx.open(ct, aad=b"")


def key_schedule(sk_raw: bytes, enc: bytes, info: bytes) -> dict:
    """Trả các giá trị trung gian của key schedule mode Base (đọc nội bộ PyHPKE)."""
    shared_secret = SUITE._kem.decap(enc, priv(sk_raw))
    _kdf, params = SUITE._key_schedule(Mode.BASE, shared_secret, info, b"", b"")
    return {
        "shared_secret": shared_secret,
        "key": params.key,
        "base_nonce": params.base_nonce,
        "exporter_secret": params.exporter_secret,
    }
