"""Database engine, session factory, and Base."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

_connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
Base = declarative_base()


def init_db() -> None:
    """Create all tables (idempotent)."""
    import models  # noqa: F401  (register models on Base)
    Base.metadata.create_all(bind=engine)


def get_session():
    """FastAPI dependency that yields a session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
