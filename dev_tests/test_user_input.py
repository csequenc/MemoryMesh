from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.database.memory_model import MemoryModel
from app.database.memory_repository import list_memories
from app.ingestion.memory_pipeline import process_memory
from app.models.memory import Memory


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


test_cases = [
    {
        "name": "Test 1: Project name vs project description",
        "existing_context": "MemoryMesh",
        "candidate_context": "MemoryMesh project",
        "expected": "DUPLICATE"
    },
    {
        "name": "Test 2: Backend vs project context",
        "existing_context": "MemoryMesh backend",
        "candidate_context": "MemoryMesh project",
        "expected": "DUPLICATE"
    },
    {
        "name": "Test 3: Different environments",
        "existing_context": "Production environment",
        "candidate_context": "Development environment",
        "expected": "COEXIST"
    }
]


with TestingSession() as db:

    for test in test_cases:

        print("\n" + "=" * 60)
        print(test["name"])
        print("=" * 60)

        # Create existing memory
        existing = Memory(
            subject="backend",
            predicate="uses_language",
            object_value="Python 3.13",
            context=test["existing_context"],
            source_id="test",
            confidence=1.0
        )

        db.add(
            MemoryModel(**existing.model_dump())
        )
        db.commit()

        # Create candidate with a different context
        candidate = Memory(
            subject="backend",
            predicate="uses_language",
            object_value="Python 3.13",
            context=test["candidate_context"],
            source_id="test",
            confidence=1.0
        )

        result = process_memory(
            db=db,
            candidate=candidate
        )

        actual = (
            result["comparisons"].comparisons[0].relationship.value
        )

        print("Existing context:", test["existing_context"])
        print("Candidate context:", test["candidate_context"])
        print("Expected:", test["expected"])
        print("Actual:", actual)
        print("Reason:", result["comparisons"].comparisons[0].reason)

        print(
            "Test result:",
            "PASS" if actual == test["expected"] else "MISMATCH"
        )

        # Reset database for the next independent test
        db.query(MemoryModel).delete()
        db.commit()


print("\nAll context comparison tests completed!")