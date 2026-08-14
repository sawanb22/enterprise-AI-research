from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from .config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None


def create_dialect_engine(database_url: str):
    """
    Create a PostgreSQL engine configured appropriately for Supabase / PostgreSQL.
    Uses NullPool for the Supabase Transaction Pooler (port 6543) and QueuePool for direct connections.
    """
    if "pooler.supabase.com" in database_url or ":6543" in database_url:
        # Supabase Transaction Pooler (PgBouncer) on port 6543
        # Use NullPool to avoid prepared statement conflicts with transaction mode pooling
        return create_engine(
            database_url,
            poolclass=NullPool,
        )
    else:
        # Direct PostgreSQL connection (e.g. port 5432 or local PostgreSQL)
        return create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_recycle=300,
            pool_pre_ping=True,
        )


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_dialect_engine(settings.database_url)
    return _engine


# Expose module-level engine and SessionLocal for session management
engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    eng = get_engine()
    Base.metadata.create_all(bind=eng)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
