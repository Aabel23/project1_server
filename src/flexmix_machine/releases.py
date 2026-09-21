from __future__ import annotations
import base64, hashlib, json, os, shutil
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

class ReleaseError(ValueError): pass

def _canonical(manifest: dict) -> bytes:
    return json.dumps({k: manifest[k] for k in ("version", "digest", "target")}, sort_keys=True, separators=(",", ":")).encode()

class ReleaseManager:
    def __init__(self, root: Path, *, target: str, trusted_public_key_b64: str):
        self.root, self.target = Path(root), target; self.trusted = Ed25519PublicKey.from_public_bytes(base64.b64decode(trusted_public_key_b64, validate=True)); self.root.mkdir(parents=True, exist_ok=True)
        self.active = self.root / "active"; self.previous = self.root / "previous"

    def verify(self, manifest: dict, artifact: bytes) -> None:
        if not isinstance(manifest.get("version"), int) or manifest["version"] < 1 or manifest.get("target") != self.target: raise ReleaseError("invalid release target/version")
        try: self.trusted.verify(base64.b64decode(manifest["signature"], validate=True), _canonical(manifest))
        except Exception as exc: raise ReleaseError("invalid release signature") from exc
        if hashlib.sha256(artifact).hexdigest() != manifest.get("digest"): raise ReleaseError("release digest mismatch")
        if self.active.exists() and (self.active / "manifest.json").exists() and manifest["version"] <= json.loads((self.active / "manifest.json").read_text())["version"]: raise ReleaseError("release downgrade")

    def activate(self, manifest: dict, artifact: bytes) -> None:
        self.verify(manifest, artifact); staging = self.root / f".staging-{manifest['version']}"; shutil.rmtree(staging, ignore_errors=True); staging.mkdir()
        (staging / "artifact.bin").write_bytes(artifact); (staging / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))
        if self.active.exists():
            shutil.rmtree(self.previous, ignore_errors=True); os.replace(self.active, self.previous)
        os.replace(staging, self.active)

    def rollback(self) -> None:
        if not self.previous.exists(): raise ReleaseError("no previous release")
        if self.active.exists(): shutil.rmtree(self.active)
        os.replace(self.previous, self.active)
