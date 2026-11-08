
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.database.memory_repository import (
    create_memory,
    list_memories,
    apply_resolution
)
from app.models.memory import Memory, MemoryStatus
from app.resolution.schemas import (
    ComparisonResult,
    MemoryComparison,
    MemoryRelationship
)
from app.resolution.resolver import resolve_comparisons


# 1. Create an isolated in-memory SQLite database
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


# 2. Seed existing memories
with TestingSession() as db:

    old_memory = Memory(
        subject="backend",
        predicate="uses_language",
        object_value="Python 3.10",
        source_id="test",
        confidence=0.95
    )

    conflict_memory = Memory(
        subject="backend",
        predicate="uses_framework",
        object_value="Django",
        source_id="test",
        confidence=0.95
    )

    coexist_memory = Memory(
        subject="frontend",
        predicate="uses_language",
        object_value="JavaScript",
        source_id="test",
        confidence=0.95
    )

    create_memory(db, old_memory)
    create_memory(db, conflict_memory)
    create_memory(db, coexist_memory)


    # 3. Create a new candidate
    candidate = Memory(
        subject="backend",
        predicate="uses_language",
        object_value="Python 3.12",
        source_id="test",
        confidence=0.98
    )


    # 4. Simulate LLM comparison results
    # No actual Groq API call is made here.
    result = ComparisonResult(
        comparisons=[
            MemoryComparison(
                memory_id=old_memory.memory_id,
                relationship=MemoryRelationship.SUPERSEDE,
                reason="Updated Python version."
            ),
            MemoryComparison(
                memory_id=conflict_memory.memory_id,
                relationship=MemoryRelationship.CONFLICT,
                reason="Conflicting framework information."
            ),
            MemoryComparison(
                memory_id=coexist_memory.memory_id,
                relationship=MemoryRelationship.COEXIST,
                reason="Different subject."
            )
        ]
    )


    # 5. Generate resolution plan
    plan = resolve_comparisons(result)

    print("Resolution plan:")
    print(plan)


    # 6. Apply plan to SQLite
    saved_candidate = apply_resolution(db, candidate, plan)

    print("\nSaved candidate:")
    print(saved_candidate)


    # 7. Inspect final database state
    memories = list_memories(db)

    print("\nDatabase after resolution:")

    for memory in memories:
        print(
            memory.subject,
            "|",
            memory.predicate,
            "|",
            memory.object_value,
            "|",
            memory.status
        )


    # 8. Verify expected results
    final_memories = {
        memory.memory_id: memory
        for memory in memories
    }

    assert final_memories[old_memory.memory_id].status == MemoryStatus.SUPERSEDED

    assert final_memories[conflict_memory.memory_id].status == MemoryStatus.UNRESOLVED

    assert final_memories[coexist_memory.memory_id].status == MemoryStatus.ACTIVE

    assert saved_candidate is not None
    assert saved_candidate.status == MemoryStatus.UNRESOLVED

    assert len(memories) == 4

    print("\nAll database integration tests passed!")

