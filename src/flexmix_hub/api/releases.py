import base64, re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from flexmix_hub.api.fleet import require_prototype_enrollment_token

router = APIRouter(prefix="/v1/prototype/releases", tags=["prototype-releases"])
class ReleaseUpload(BaseModel):
    model_config = {"extra": "forbid"}
    version: int = Field(ge=1); digest: str = Field(pattern=r"^[0-9a-f]{64}$"); target: str = Field(min_length=1, max_length=128); signature: str = Field(min_length=1); artifact_b64: str = Field(min_length=1)

@router.post("")
def upload_release(payload: ReleaseUpload, request: Request, _: None = Depends(require_prototype_enrollment_token)):
    if any(key in payload.model_dump() for key in ("private_key", "signing_key", "secret_key")): raise HTTPException(400, "private signing keys are not accepted")
    try: artifact = base64.b64decode(payload.artifact_b64, validate=True)
    except ValueError as exc: raise HTTPException(400, "invalid artifact") from exc
    root = Path(request.app.state.settings.release_root); root.mkdir(parents=True, exist_ok=True); path = root / f"{payload.target}-{payload.version}.bin"; path.write_bytes(artifact)
    return {"version": payload.version, "target": payload.target, "digest": payload.digest, "artifact_path": str(path)}
