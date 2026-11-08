
from app.models.memory import Memory, MemoryStatus
from app.query.answer import generate_answer


memories = [
    Memory(
        memory_id="conflict-001",
        subject="backend",
        predicate="uses_language",
        object_value="Python 3.12",
        context="MemoryMesh project",
        source_id="test",
        confidence=1.0,
        status=MemoryStatus.UNRESOLVED
    ),
    Memory(
        memory_id="conflict-002",
        subject="backend",
        predicate="uses_language",
        object_value="Python 3.13",
        context="MemoryMesh project",
        source_id="test",
        confidence=1.0,
        status=MemoryStatus.UNRESOLVED
    )
]

result = generate_answer(
    query="What programming language does my backend use?",
    retrieved_memories=memories
)

print("\nAnswer:", result["answer"])
print("Relevant source IDs:", result["source_memories"])
