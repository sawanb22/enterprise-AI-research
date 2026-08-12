from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings


settings = get_settings()

if settings.database_url.startswith("sqlite:///"):
    db_file = settings.database_url.removeprefix("sqlite:///")
    Path(db_file).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record):
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db():
    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        with engine.connect() as conn:
            try:
                # Check if reasoning column exists on conclusions
                result = conn.exec_driver_sql("PRAGMA table_info(conclusions)")
                columns = [row[1] for row in result.fetchall()]
                if columns and "reasoning" not in columns:
                    conn.exec_driver_sql("ALTER TABLE conclusions ADD COLUMN reasoning TEXT DEFAULT ''")
                    conn.commit()
            except Exception:
                pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
