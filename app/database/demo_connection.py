import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base, BASE_DIR


PERSONAL_DATABASE_PATH = (
    BASE_DIR / "memorymesh.db"
).resolve()

configured_path = os.getenv("MEMORYMESH_DEMO_DB_PATH")

if configured_path:
    DEMO_DATABASE_PATH = Path(configured_path).expanduser()

    if not DEMO_DATABASE_PATH.is_absolute():
        DEMO_DATABASE_PATH = BASE_DIR / DEMO_DATABASE_PATH
else:
    DEMO_DATABASE_PATH = BASE_DIR / "memorymesh_demo.db"

DEMO_DATABASE_PATH = DEMO_DATABASE_PATH.resolve()

if DEMO_DATABASE_PATH == PERSONAL_DATABASE_PATH:
    raise RuntimeError(
        "The demo database cannot use the personal database path."
    )

DEMO_DATABASE_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

DEMO_DATABASE_URL = (
    f"sqlite:///{DEMO_DATABASE_PATH.as_posix()}"
)

demo_engine = create_engine(
    DEMO_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

DemoSessionLocal = sessionmaker(
    bind=demo_engine,
    autoflush=False,
    autocommit=False
)


def create_demo_tables():
    from app.database.memory_model import MemoryModel

    Base.metadata.create_all(bind=demo_engine)


def get_demo_db():
    db = DemoSessionLocal()

    try:
        yield db
    finally:
        db.close()
