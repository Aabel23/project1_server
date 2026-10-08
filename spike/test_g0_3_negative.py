"""G0.3: test âm. Mọi ca phải mở thất bại và chỉ ném đúng loại lỗi đã biết.

Lớp HPKE (thư viện):
- đổi 1 bit ở từng vị trí của M (info đổi), enc, ct;
- cắt cụt ct ở mọi độ dài;
- đổi nhãn của info (năm nhãn còn lại, nhãn gần giống, bỏ băm).
  cryptography chỉ được ném InvalidTag.
  PyHPKE (chỉ là tham chiếu) được ném OpenError hoặc ValueError (enc không
  phải điểm hợp lệ); ghi nhận trong bằng chứng.

Lớp FM1 (envelope đầy đủ, qua fm1_ref.open_request):
- đổi 1 bit ở từng vị trí của envelope; cắt cụt ở mọi độ dài.
  Chỉ được ném FM1Error (FrameError, SignatureError, OpenError).
"""

from __future__ import annotations

import collections
import os

import pytest
from cryptography.exceptions import InvalidTag
from pyhpke.exceptions import OpenError as PyOpenError

import fm1_ref as F
import pyhpke_ref as P

SK = F.x25519_priv(bytes(range(32)))
SK_RAW = F.raw_priv(SK)
PK = SK.public_key()
SIGN = F.ed25519_priv(bytes(range(32, 64)))

M = F.build_m({
    "audience": "fmx-test", "server_kid": "a1b2c3d4e5f60718", "credential_kid": "0011223344556677",
    "route_id": "AGENT_STOCK_PATH", "attempt_id": bytes(16), "issued_at": 1_790_000_000_000,
    "server_epoch_seen": bytes(range(16)),
})
PT = F.inner_request(bytes(16), b'{"stock":[{"ingredient_id":1,"amount":500}]}')
ENC, CT = F.hpke_seal(PK, M, PT)

seen = collections.Counter()


def _flip(data: bytes, bit: int) -> bytes:
    b = bytearray(data)
    b[bit // 8] ^= 1 << (bit % 8)
    return bytes(b)


def _must_fail_both(m: bytes, enc: bytes, ct: bytes, info: bytes | None = None):
    """cryptography: chỉ InvalidTag. PyHPKE: OpenError hoặc ValueError."""
    info = F.hpke_info(m) if info is None else info
    from cryptography.hazmat.primitives.hpke import AEAD, KDF, KEM, Suite
    suite = Suite(KEM.X25519, KDF.HKDF_SHA256, AEAD.AES_128_GCM)
    with pytest.raises(InvalidTag):
        suite.decrypt(enc + ct, SK, info=info)
    seen["cryptography:InvalidTag"] += 1
    try:
        P.open_(SK_RAW, enc, info, ct)
    except PyOpenError:
        seen["pyhpke:OpenError"] += 1
    except ValueError:
        seen["pyhpke:ValueError"] += 1
    else:
        pytest.fail("PyHPKE mở được gói đã bị sửa")


def test_goi_goc_mo_duoc():
    assert F.hpke_open(SK, M, ENC, CT) == PT
    assert P.open_(SK_RAW, ENC, F.hpke_info(M), CT) == PT


def test_doi_1_bit_trong_m():
    for bit in range(len(M) * 8):
        _must_fail_both(_flip(M, bit), ENC, CT)


def test_doi_1_bit_trong_enc():
    for bit in range(len(ENC) * 8):
        enc = _flip(ENC, bit)
        _must_fail_both(M, enc, CT)


def test_doi_1_bit_trong_ct():
    for bit in range(len(CT) * 8):
        _must_fail_both(M, ENC, _flip(CT, bit))


def test_cat_cut_ct():
    for n in range(len(CT)):
        _must_fail_both(M, ENC, CT[:n])


def test_doi_nhan():
    h = F.sha256(M)
    infos = [F.tuple_(lbl, h) for lbl in F.LABELS if lbl != F.LABEL_REQ]
    infos += [
        F.lp(b"fm1-reqx") + F.lp(h),
        F.lp(b"fm1-re") + F.lp(h),
        F.lp(b"FM1-REQ") + F.lp(h),
        F.lp(b"fm1-req") + F.lp(M),            # bỏ băm
        F.lp(b"fm1-req") + F.lp(h) + F.lp(b""),  # thêm trường rỗng
        b"fm1-req" + h,                          # không bọc LP
    ]
    for info in infos:
        assert info != F.hpke_info(M)
        _must_fail_both(M, ENC, CT, info=info)


def _envelope():
    env, m = F.seal_request(
        {"audience": "fmx-test", "server_kid": "a1b2c3d4e5f60718", "credential_kid": "0011223344556677",
         "route_id": "AGENT_STOCK_PATH", "attempt_id": os.urandom(16), "issued_at": 1_790_000_000_000,
         "server_epoch_seen": b""},
        b'{"stock":[]}', os.urandom(16), PK, SIGN)
    return env


def test_envelope_doi_1_bit_moi_vi_tri():
    env = _envelope()
    F.open_request(env, SK, SIGN.public_key())
    stages = collections.Counter()
    for bit in range(len(env) * 8):
        try:
            F.open_request(_flip(env, bit), SK, SIGN.public_key())
        except F.FM1Error as exc:
            stages[exc.stage] += 1
        else:
            pytest.fail(f"envelope đổi bit {bit} vẫn mở được")
    seen.update({f"fm1:{k}": v for k, v in stages.items()})
    assert sum(stages.values()) == len(env) * 8


def test_envelope_cat_cut_va_thua_byte():
    env = _envelope()
    for n in range(len(env)):
        with pytest.raises(F.FM1Error):
            F.open_request(env[:n], SK, SIGN.public_key())
    with pytest.raises(F.FrameError):
        F.open_request(env + b"\x00", SK, SIGN.public_key())


def test_zz_in_thong_ke():
    """In thống kê loại lỗi để chép vào bằng chứng (chạy cuối file)."""
    print("\nTHONG_KE_G0_3", dict(sorted(seen.items())))
    assert seen["cryptography:InvalidTag"] > 0
