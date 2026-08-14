import pytest
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_engine


@pytest.fixture(scope="session")
def engine():
    """Session-scoped database engine connected to PostgreSQL."""
    eng = get_engine()
    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture
def db_session(engine):
    """
    Function-scoped database session running in an isolated transaction.
    Rolls back changes after each test to keep database state pristine.
    """
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = Session()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
