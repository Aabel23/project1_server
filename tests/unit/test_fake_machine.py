import sys
from pathlib import Path
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).parents[2]))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fake_machine import FakeMachine

def test_fake_machine_signs_canonical_requests():
    machine = FakeMachine("http://hub", 1, uuid4(), Ed25519PrivateKey.generate())
    headers = machine.headers("GET", "/v1/machine/self")
    assert headers["X-Flexmix-Device-Uuid"] == str(machine.uuid)
    assert headers["X-Flexmix-Device-Signature"]
