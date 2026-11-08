from app.models.memory import Memory, MemoryStatus


memory = Memory(
    subject="backend",
    predicate="uses_language",
    object_value="Python 3.10",
    source_id="user_input",
    confidence=0.95
)

print(memory.model_dump())