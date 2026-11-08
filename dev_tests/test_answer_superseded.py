from app.models.memory import Memory, MemoryStatus
from app.query.answer import generate_answer


memories = [
    Memory(
        memory_id="old-memory",
        subject="backend",
        predicate="uses_language",
        object_value="Python 3.12",
        source_id="test",
        confidence=1.0,
        status=MemoryStatus.SUPERSEDED
    )
]

result = generate_answer(
    query="What programming language does my backend use?",
    retrieved_memories=memories
)

print("Answer:", result["answer"])
print("Source memories:", result["source_memories"])