"""Small HTTP-only machine simulator for exercising the prototype Hub APIs."""
from __future__ import annotations
import argparse, base64, json, os, tarfile, tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4
import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from flexmix_hub.infrastructure.security.device_identity import request_payload

class FakeMachine:
    def __init__(self, base_url: str, mid: int, device_uuid: UUID, key: Ed25519PrivateKey):
        self.base = base_url.rstrip("/"); self.mid = mid; self.uuid = device_uuid; self.key = key
        self.client = httpx.Client(timeout=5)

    def headers(self, method: str, path: str) -> dict[str, str]:
        sig = self.key.sign(request_payload(method, path, self.uuid))
        return {"X-Flexmix-Device-Uuid": str(self.uuid), "X-Flexmix-Device-Signature": base64.b64encode(sig).decode()}

    def call(self, method: str, path: str, **kwargs):
        headers = self.headers(method, path); headers.update(kwargs.pop("headers", {}))
        response = self.client.request(method, self.base + path, headers=headers, **kwargs)
        response.raise_for_status(); return response

    def run(self) -> None:
        self.call("GET", "/v1/machine/self")
        self.call("GET", "/v1/state")
        # Simulate disconnect/reconnect without involving local selling logic.
        self.client.close()
        self.client = httpx.Client(timeout=5)
        event = {"event_id": str(uuid4()), "cursor": 1, "serial": "FAKE-1", "status": "used", "drink_id": "fake", "price_cents": 0, "occurred_at": datetime.now(timezone.utc).isoformat()}
        ack = self.call("POST", "/v1/events", json={"cursor_from": 0, "cursor_to": 1, "rows": [event]}).json()
        if ack.get("ack") != "ok" or ack.get("cursor_to") != 1: raise RuntimeError("invalid event ACK")
        commands = self.call("GET", "/v1/commands/poll").json().get("commands", [])
        for command in commands:
            self.call("POST", "/v1/commands/ack", json={"command_id": command["command_id"], "status": "acknowledged"})
        self.call("POST", "/v1/beat", json={"reported_at": datetime.now(timezone.utc).isoformat(), "status": "ok", "schema_version": "fake", "selling_available": True})
        with tempfile.TemporaryDirectory() as td:
            package = Path(td) / "fake.tar.gz"
            with tarfile.open(package, "w:gz") as archive:
                payload = Path(td) / "backup.json"; payload.write_text(json.dumps({"mid": self.mid}))
                archive.add(payload, arcname="machine_profile.json")
            self.call("POST", "/v1/backups", content=package.read_bytes(), headers={"Content-Type": "application/gzip", "X-Flexmix-Backup-Id": f"fake-{uuid4().hex}", "X-Flexmix-Backup-Time": datetime.now(timezone.utc).isoformat()})

def load_key() -> Ed25519PrivateKey:
    encoded = os.getenv("FLEXMIX_MACHINE_PRIVATE_KEY_B64")
    if encoded:
        return Ed25519PrivateKey.from_private_bytes(base64.b64decode(encoded, validate=True))
    raise SystemExit("Set FLEXMIX_MACHINE_PRIVATE_KEY_B64 for the registered test machine")

def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--mid", type=int, required=True); parser.add_argument("--hub", default=os.getenv("FLEXMIX_HUB_URL", "http://127.0.0.1:8001")); parser.add_argument("--device-uuid", default=os.getenv("FLEXMIX_DEVICE_UUID"))
    args = parser.parse_args(); uid = UUID(args.device_uuid) if args.device_uuid else (_ for _ in ()).throw(SystemExit("Set FLEXMIX_DEVICE_UUID for the registered test machine"))
    FakeMachine(args.hub, args.mid, uid, load_key()).run(); print(f"fake machine MID {args.mid}: PASS")
if __name__ == "__main__": main()
