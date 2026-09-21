from alembic import context

from flexmix_hub.config import Settings
from flexmix_hub.infrastructure.database.base import Base
from flexmix_hub.infrastructure.database.session import create_database_engine
from flexmix_hub.modules.fleet.models import FleetMidAllocation, MachineRegistry  # noqa: F401
from flexmix_hub.modules.catalogue.models import (  # noqa: F401
    CatalogueDrink,
    CatalogueIngredient,
    CatalogueRecipeAction,
    DesiredStateMeta,
)
from flexmix_hub.modules.events.models import MachineOrderEvent  # noqa: F401
from flexmix_hub.modules.commands.models import MachineCommand  # noqa: F401
from flexmix_hub.modules.monitoring.models import MachineHeartbeat  # noqa: F401
from flexmix_hub.modules.backups.models import BackupMetadata  # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    # SQL generation needs only the dialect, not credentials or a live database.
    context.configure(
        dialect_name="mysql", target_metadata=target_metadata,
        literal_binds=True, compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_database_engine(Settings())
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection, target_metadata=target_metadata,
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
