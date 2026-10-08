"""G0.1: chạy vector RFC 9180 đầy đủ trên PyHPKE.

Suite X25519 / HKDF-SHA256 / AES-128-GCM, mode Base (RFC 9180 A.1.1).
Kiểm: cặp khoá dẫn từ ikm, enc, key schedule, 257 lần seal/open, 3 export.

Thêm (G0.4): cùng vector chạy qua hàm nội bộ `_decrypt_with_aad` của
cryptography, đúng như test upstream `test_vector_decryption` làm.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import pyhpke_ref as P

VECTOR_FILE = Path(__file__).parent / "vectors" / "rfc9180_x25519_sha256_aes128gcm_base.json"
VECTORS = json.loads(VECTOR_FILE.read_text(encoding="utf-8"))["vectors"]
H = bytes.fromhex


def test_dung_mot_vector_cua_suite():
    assert len(VECTORS) == 1
    v = VECTORS[0]
    assert (v["mode"], v["kem_id"], v["kdf_id"], v["aead_id"]) == (0, 0x20, 1, 1)
    assert len(v["encryptions"]) == 257
    assert len(v["exports"]) == 3


@pytest.mark.parametrize("v", VECTORS)
def test_khoa_dan_tu_ikm(v):
    kp_e = P.derive_key_pair(H(v["ikmE"]))
    kp_r = P.derive_key_pair(H(v["ikmR"]))
    assert kp_e.private_key.to_private_bytes() == H(v["skEm"])
    assert kp_e.public_key.to_public_bytes() == H(v["pkEm"])
    assert kp_r.private_key.to_private_bytes() == H(v["skRm"])
    assert kp_r.public_key.to_public_bytes() == H(v["pkRm"])


@pytest.mark.parametrize("v", VECTORS)
def test_key_schedule(v):
    ks = P.key_schedule(H(v["skRm"]), H(v["enc"]), H(v["info"]))
    assert ks["shared_secret"] == H(v["shared_secret"])
    assert ks["key"] == H(v["key"])
    assert ks["base_nonce"] == H(v["base_nonce"])
    assert ks["exporter_secret"] == H(v["exporter_secret"])


@pytest.mark.parametrize("v", VECTORS)
def test_seal_open_moi_lan_ma_hoa(v):
    eks = P.derive_key_pair(H(v["ikmE"]))
    enc, sender = P.SUITE.create_sender_context(P.pub(H(v["pkRm"])), info=H(v["info"]), eks=eks)
    assert enc == H(v["enc"])
    recipient = P.SUITE.create_recipient_context(enc, P.priv(H(v["skRm"])), info=H(v["info"]))
    for i, e in enumerate(v["encryptions"]):
        ct = sender.seal(H(e["pt"]), aad=H(e["aad"]))
        assert ct == H(e["ct"]), f"seal lần {i} lệch"
        assert recipient.open(H(e["ct"]), aad=H(e["aad"])) == H(e["pt"]), f"open lần {i} lệch"


@pytest.mark.parametrize("v", VECTORS)
def test_export(v):
    _enc, sender = P.SUITE.create_sender_context(
        P.pub(H(v["pkRm"])), info=H(v["info"]), eks=P.derive_key_pair(H(v["ikmE"])))
    for e in v["exports"]:
        assert sender.export(H(e["exporter_context"]), e["L"]) == H(e["exported_value"])


@pytest.mark.parametrize("v", VECTORS)
def test_cryptography_noi_bo_giai_ma_vector_dau(v):
    """Giống upstream: chỉ lần mã hoá đầu (seq 0), qua hàm nội bộ có AAD."""
    from cryptography.hazmat.bindings._rust import openssl as rust_openssl
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives.hpke import AEAD, KDF, KEM, Suite

    suite = Suite(KEM.X25519, KDF.HKDF_SHA256, AEAD.AES_128_GCM)
    e = v["encryptions"][0]
    pt = rust_openssl.hpke._decrypt_with_aad(
        suite, H(v["enc"]) + H(e["ct"]),
        X25519PrivateKey.from_private_bytes(H(v["skRm"])),
        info=H(v["info"]), aad=H(e["aad"]))
    assert pt == H(e["pt"])
