"""
Alembic Environment — Async-compatible with KnowledgeGPT models.
Uses asyncpg + SQLAlchemy async engine.
"""
import asyncio
from logging.config import fileConfig
# pyrefly: ignore [missing-import]
from sqlalchemy import pool
# pyrefly: ignore [missing-import]
from sqlalchemy.engine import Connection
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os
import sys

# ─── Make app importable ──────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ─── Import all models to register them with Base.metadata ───────────────────
from app.core.database import Base  # noqa: E402
from app.models import (  # noqa: E402, F401
    user,
    knowledge_base,
    document,
    conversation,
    message,
    feedback,
    analytics,
)

# ─── Alembic Config ───────────────────────────────────────────────────────────
config = context.config

# Read DATABASE_URL from environment (overrides alembic.ini for Docker)
database_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
# asyncpg requires postgresql+asyncpg:// scheme
if database_url and database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    In offline mode we don't need an actual DB connection — Alembic emits
    the SQL statements to stdout / file.
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


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
