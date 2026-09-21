import base64, hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from flexmix_machine.releases import ReleaseManager, ReleaseError
import json
def test_signed_release_activate_and_rollback(tmp_path):
    key=Ed25519PrivateKey.generate(); pub=base64.b64encode(key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode(); a=b"one"; b=b"two"
    def manifest(v,data):
        m={"version":v,"digest":hashlib.sha256(data).hexdigest(),"target":"machine"}; raw=json.dumps(m,sort_keys=True,separators=(",",":")).encode(); m["signature"]=base64.b64encode(key.sign(raw)).decode(); return m
    r=ReleaseManager(tmp_path,target="machine",trusted_public_key_b64=pub); r.activate(manifest(1,a),a); r.activate(manifest(2,b),b); r.rollback(); assert (r.active/"artifact.bin").read_bytes()==a
    try:r.activate(manifest(1,a),a)
    except ReleaseError:pass
    else: raise AssertionError
