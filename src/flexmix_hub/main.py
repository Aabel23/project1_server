from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from flexmix_hub.api.fleet import router as fleet_router
from flexmix_hub.api.health import router
from flexmix_hub.api.machine import router as machine_router
from flexmix_hub.api.state import router as state_router
from flexmix_hub.api.events import router as events_router
from flexmix_hub.api.commands import router as commands_router
from flexmix_hub.api.monitoring import router as monitoring_router
from flexmix_hub.api.backups import router as backups_router
from flexmix_hub.api.catalogue import router as catalogue_router
from flexmix_hub.api.overview import router as overview_router
from flexmix_hub.api.releases import router as releases_router
from flexmix_hub.api.dashboard import router as dashboard_router
from flexmix_hub.config import Settings
from flexmix_hub.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app_settings = settings or Settings()
        engine = create_database_engine(app_settings)
        app.state.settings = app_settings
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        app_settings.backup_root.mkdir(parents=True, exist_ok=True)
        try:
            app_settings.backup_root.chmod(0o700)
        except OSError:
            pass
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(
        title="FlexMix Hub foundation", lifespan=lifespan,
        docs_url=None, redoc_url=None, openapi_url=None,
    )
    app.include_router(router)
    app.include_router(fleet_router)
    app.include_router(machine_router)
    app.include_router(state_router)
    app.include_router(events_router)
    app.include_router(commands_router)
    app.include_router(monitoring_router)
    app.include_router(backups_router)
    app.include_router(catalogue_router)
    app.include_router(overview_router)
    app.include_router(releases_router)
    app.include_router(dashboard_router)
    app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")
    return app
