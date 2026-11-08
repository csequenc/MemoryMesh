from app.models.memory import Memory, MemoryStatus
from app.query.answer import generate_answer


memories = [
    Memory(
        memory_id="test-memory-001",
        subject="backend",
        predicate="uses_language",
        object_value="Python 3.12",
        context="MemoryMesh project",
        source_id="test",
        confidence=1.0,
        status=MemoryStatus.UNRESOLVED
    ),
    Memory(
        memory_id="test-memory-002",
        subject="backend",
        predicate="uses_language",
        object_value="Python 3.13",
        context="MemoryMesh project",
        source_id="test",
        confidence=1.0,
        status=MemoryStatus.UNRESOLVED
    )
]

query = "What programming language does my backend use?"

result = generate_answer(
    query=query,
    retrieved_memories=memories
)

print("\nQuestion:", query)
print("\nAnswer:", result["answer"])
print("\nSource memories:", result["source_memories"])