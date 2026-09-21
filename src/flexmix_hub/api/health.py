from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Process liveness; no database or machine dependency."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(request: Request) -> JSONResponse:
    """Development DB connectivity only, not schema/business readiness."""
    try:
        request.app.state.settings.release_root.mkdir(parents=True, exist_ok=True)
        with request.app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        # Driver errors can contain connection details: never return/log them here.
        return JSONResponse({"status": "unavailable"}, status_code=503)
    return JSONResponse({"status": "ok"})
