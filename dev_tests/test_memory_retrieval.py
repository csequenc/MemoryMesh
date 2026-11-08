from app.database.connection import SessionLocal, create_tables
from app.database.memory_repository import get_all_candidate_memories
from app.retrieval.semantic_search import retrieve_candidates
from app.models.memory import Memory, MemoryStatus
from app.database.memory_repository import list_memories



create_tables()

db = SessionLocal()

try:
    # New memory that we want to compare
    candidate = Memory(
        subject="backend service",
        predicate="written_in",
        object_value="Python 3.12",
        context="production deployment",
        source_id="test_source",
        confidence=0.9
    )

    # Fetch existing memories from SQLite
    existing_memories = get_all_candidate_memories(db)

    print(f"Memories retrieved from database: {len(existing_memories)}")

    # Perform semantic retrieval
    results = retrieve_candidates(
        candidate,
        existing_memories,
        top_k=5
    )

    print("\nRelevant candidates:")

    for memory, score in results:
        print(
            f"{memory.subject} | "
            f"{memory.predicate} | "
            f"{memory.object_value} | "
            f"Score: {score:.4f}"
        )

finally:
    db.close()