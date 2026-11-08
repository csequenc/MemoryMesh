from app.models.memory import Memory, MemoryStatus
from app.retrieval.semantic_search import retrieve_candidates


existing_memories = [
    Memory(
        subject="backend",
        predicate="uses_language",
        object_value="Python 3.10",
        context="production environment",
        source_id="s1",
        confidence=0.9
    ),
    Memory(
        subject="frontend",
        predicate="uses_language",
        object_value="JavaScript",
        context="web application",
        source_id="s2",
        confidence=0.9
    ),
    Memory(
        subject="database",
        predicate="uses_database",
        object_value="PostgreSQL",
        context="production environment",
        source_id="s3",
        confidence=0.9
    )
]

candidate = Memory(
    subject="backend service",
    predicate="written_in",
    object_value="Python 3.12",
    context="production deployment",
    source_id="s4",
    confidence=0.9
)

results = retrieve_candidates(candidate, existing_memories)

for memory, score in results:
    print(
        f"{memory.subject} | "
        f"{memory.predicate} | "
        f"{memory.object_value} | "
        f"Score: {score:.4f}"
    )