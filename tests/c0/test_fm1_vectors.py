"""C0.3: bộ vector FM1 chạy được bằng code spike của G0 (spike/fm1_ref.py).

Thứ tự kiểm theo pipeline 4.4: khung -> audience -> route -> giờ -> chữ ký
-> HPKE open -> khung bên trong và JSON. Kiểm kid còn active, high-water và
claim cần DB nên không nằm trong vector; S-FM1 test các bước đó bằng stub.

Khi S-FM1 có `fm1_encoding.py`, `fm1_crypto.py` thật, khối đó chạy lại cùng
bộ vector này bằng code của mình.
"""

from __future__ import annotations

import json
import sys

import pytest

from conftest import SPIKE_DIR, VECTOR_DIR
from server.config import routing

sys.path.insert(0, str(SPIKE_DIR))
import fm1_ref as F  # noqa: E402

FILES = sorted((VECTOR_DIR / "fm1").glob("*.json"))
VECTORS = [json.loads(p.read_text(encoding="utf-8")) for p in FILES]
H = bytes.fromhex


def _stage_of_request(v: dict):
    """Trả (stage từ chối hoặc None, kết quả khi nhận)."""
    env = H(v["request_hex"])
    keys = v["keys"]
    try:
        m, fields, enc, ct, sig = F.parse_request(env)
    except F.FM1Error as exc:
        return exc.stage, None
    if fields["audience"] != v["server_audience"] or fields["server_kid"] != v["server_kid"]:
        return "audience", None
    pol = routing.ROUTE_POLICY.get(fields["route_id"])
    if pol is None or pol.path != v["path"] or pol.mode not in (routing.MODE_FM1, routing.MODE_ENROLL):
        return "route", None
    if (pol.mode == routing.MODE_ENROLL) != (fields["credential_kid"] == F.ENROLL_KID):
        return "route", None
    if abs(fields["issued_at"] - v["server_now_ms"]) > v["window_ms"]:
        return "time", None
    try:
        F.verify_request(F.ed25519_pub(H(keys["machine_sign_pk_hex"])), m, enc, ct, sig)
        pt = F.hpke_open(F.x25519_priv(H(keys["server_kem_sk_hex"])), m, enc, ct)
        resp_key, body = F.split_inner_request(pt, pol.max_request)
        obj = F.strict_json(body, pol.max_request)
    except F.FM1Error as exc:
        return exc.stage, None
    return None, (m, fields, resp_key, body, obj)


def test_co_du_vector():
    kinds = {(v["kind"], v["expect"]) for v in VECTORS}
    assert ("request", "accept") in kinds
    assert ("request", "reject") in kinds
    assert ("response", "reject") in kinds
    assert len(VECTORS) >= 30
    assert [p.stem for p in FILES] == [v["name"] for v in VECTORS]


@pytest.mark.parametrize("v", [v for v in VECTORS if v["kind"] == "request"], ids=lambda v: v["name"])
def test_vector_request(v):
    stage, got = _stage_of_request(v)
    if v["expect"] == "reject":
        assert stage == v["stage"], v["_ghi_chu"]
        return
    assert stage is None
    m, fields, resp_key, body, _obj = got
    assert m.hex() == v["m_hex"]
    assert resp_key.hex() == v["resp_key_hex"]
    assert body.decode() == v["body_utf8"]
    assert {**fields, "attempt_id": fields["attempt_id"].hex(),
            "server_epoch_seen": fields["server_epoch_seen"].hex()} == v["m_fields"]
    # Response: seal với nonce của vector phải ra đúng từng byte, và mở lại được.
    r = v["response"]
    sealed = F.seal_response(resp_key, m, r["inner"], nonce=H(r["nonce_hex"]))
    assert sealed.hex() == r["response_hex"]
    assert F.resp_aad(m).hex() == r["aad_hex"]
    assert F.open_response(resp_key, m, sealed, fields["attempt_id"]) == r["inner"]


@pytest.mark.parametrize("v", [v for v in VECTORS if v["kind"] == "response"], ids=lambda v: v["name"])
def test_vector_response_bi_tu_choi(v):
    with pytest.raises(F.FM1Error) as info:
        F.open_response(H(v["resp_key_hex"]), H(v["m_hex"]), H(v["response_hex"]),
                        H(v["expected_attempt_id_hex"]))
    assert info.value.stage == v["stage"], v["_ghi_chu"]


def test_sau_nhan_khac_nhau_khong_ra_cung_byte():
    h = F.sha256(b"x")
    outs = {F.tuple_(label, h) for label in F.LABELS}
    assert len(outs) == 6 == len(F.LABELS)
