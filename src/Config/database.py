from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def create_tables() -> None:
    """Create all tables defined in Base metadata."""
    try:
        import src.models  # noqa: F401 — ensure all models are registered
        Base.metadata.create_all(bind=engine)
        print("Database tables created/verified successfully.")
    except Exception as e:
        print(f"WARNING: Could not create database tables: {e}")
        print("The server will continue, but database-dependent features may fail.")


def get_db() -> Generator[Session, Any, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
