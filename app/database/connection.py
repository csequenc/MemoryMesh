
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Store the database in the project's root directory.
BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_URL = f"sqlite:///{BASE_DIR / 'memorymesh.db'}"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass


def create_tables():
    # Import the model so SQLAlchemy knows about the table.
    from app.database.memory_model import MemoryModel

    Base.metadata.create_all(bind=engine)
