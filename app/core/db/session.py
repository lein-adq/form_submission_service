"""Database session management with SQLModel."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import SQLModel

from app.core.config.settings import settings
from app.core.db.rls import apply_rls_context


# Create engine
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)

# Service role engine for public submissions (bypasses RLS)
service_engine = None
ServiceSessionLocal = None

if settings.database_service_url:
    service_engine = create_engine(
        settings.database_service_url,
        echo=settings.database_echo,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=5,
    )
    ServiceSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=service_engine,
        class_=Session,
    )


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_service_db() -> Generator[Session, None, None]:
    """Dependency for getting service role database session (bypasses RLS)."""
    if not ServiceSessionLocal:
        raise RuntimeError("Service database URL not configured")
    db = ServiceSessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_with_rls(
    user_id: str, workspace_id: str | None = None
) -> Generator[Session, None, None]:
    """Get database session with RLS context applied."""
    db = SessionLocal()
    try:
        apply_rls_context(db, user_id=user_id, workspace_id=workspace_id)
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database (create tables)."""
    SQLModel.metadata.create_all(engine)
