from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from flexmix_hub.config import Settings


def create_database_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url(), pool_pre_ping=True,
        pool_size=5, max_overflow=0, pool_timeout=5,
        connect_args={"connect_timeout": 5, "read_timeout": 5, "write_timeout": 5},
        echo=False, hide_parameters=True,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session(request: Request) -> Iterator[Session]:
    # Transactions must be explicitly committed by a future caller.
    # close() rolls back any uncommitted transaction, including on exceptions.
    with request.app.state.session_factory() as session:
        yield session
