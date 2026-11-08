
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.database.memory_model import MemoryModel
from app.database.memory_repository import (
    create_memory,
    list_memories
)

from app.models.memory import Memory
from app.ingestion.memory_pipeline import process_memory


# 1. Create isolated in-memory database
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSession = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base.metadata.create_all(bind=engine)


with TestingSession() as db:

    # 2. Insert an existing memory
    old_memory = Memory(
        subject="backend",
        predicate="uses_language",
        object_value="Python 3.10",
        source_id="test",
        confidence=0.95,
        context="MemoryMesh project"
    )

    create_memory(db, old_memory)

    # 3. Create a new candidate
    candidate = Memory(
        subject="backend",
        predicate="uses_language",
        object_value="Python 3.12",
        source_id="test",
        confidence=0.98,
        context="MemoryMesh project"
    )

    # 4. Run the complete pipeline
    result = process_memory(
        db=db,
        candidate=candidate
    )

    # 5. Inspect comparison results
    print("\nLLM comparisons:")
    print(result["comparisons"])

    # 6. Inspect resolution plan
    print("\nResolution plan:")
    print(result["plan"])

    # 7. Inspect saved candidate
    print("\nSaved candidate:")
    print(result["saved_memory"])

    # 8. Inspect final database
    print("\nFinal database state:")

    for memory in list_memories(db):
        print(
            memory.subject,
            "|",
            memory.predicate,
            "|",
            memory.object_value,
            "|",
            memory.status
        )

print("\nPipeline test completed!")
