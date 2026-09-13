from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

DATABASE_PATH = Path(settings.database_url.replace("sqlite:///", "")).resolve()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
    """PRAGMAs SQLite : WAL, concurrence, cache et timeouts (une fois par connexion)."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA cache_size=-10000")
    cursor.execute(f"PRAGMA busy_timeout={settings.database_busy_timeout_ms}")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401  (enregistre les modèles)

    Base.metadata.create_all(bind=engine)
