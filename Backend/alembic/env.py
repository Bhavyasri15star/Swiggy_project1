import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, event
from sqlalchemy import pool

from alembic import context

# So `from core.models import Base` resolves the same way it does when
# main.py runs from the Backend/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import Base  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Same env var / fallback convention as core/database.py, so this points at
# whatever DB the app itself would connect to — no separate config to keep
# in sync.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://swiggy_user:12345@localhost:5432/swiggy_clone",
)
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Enables `alembic revision --autogenerate` to diff core/models.py against
# the live schema for future changes. Restaurant/Item/Order/OrderItem live
# in the default "public" schema; auth.users (Prisma-owned) is intentionally
# not part of this metadata at all, so autogenerate will never try to touch it.
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Same reasoning as core/database.py's connect-event listener: this
    # role's default search_path has been observed changing at the
    # database level (a side effect of AuthService's Prisma db push
    # targeting a different schema) -- when that happened to be in effect
    # while `alembic stamp head` ran, it created a full duplicate copy of
    # every table here inside the "auth" schema instead of "public",
    # since this engine (unlike core.database.engine) had no protection
    # against it. That duplication is exactly what caused AuthService's
    # own next `prisma db push` to refuse with a data-loss warning (it
    # saw tables it doesn't own sitting in its schema). This engine now
    # gets the same protection.
    @event.listens_for(connectable, "connect")
    def _set_search_path(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute('SET search_path TO "$user", public')
        cursor.close()

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
