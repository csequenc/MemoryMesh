
from app.models.memory import Memory, MemoryStatus
from app.database.connection import SessionLocal, create_tables
from app.database.memory_repository import create_memory, get_memory


# Create the database and tables.
create_tables()

# Create a memory using our Pydantic model.
memory = Memory(
    subject="backend",
    predicate="uses_language",
    object_value="Python 3.10",
    source_id="user_input",
    confidence=0.95
)

# Save and retrieve it.
with SessionLocal() as db:
    saved_memory = create_memory(db, memory)

    retrieved_memory = get_memory(
        db, saved_memory.memory_id
    )

    print("Saved:", saved_memory.model_dump())
    print("Retrieved:", retrieved_memory.model_dump())

    assert retrieved_memory is not None
    assert retrieved_memory.memory_id == memory.memory_id
    assert retrieved_memory.object_value == "Python 3.10"
    assert retrieved_memory.status == MemoryStatus.ACTIVE

    print("\nDatabase round trip successful!")
