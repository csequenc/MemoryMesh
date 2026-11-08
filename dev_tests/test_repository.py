from app.models.memory import MemoryStatus
from app.database.connection import SessionLocal
from app.database.memory_repository import (
    list_memories,
    update_memory_status
)


with SessionLocal() as db:

    # Retrieve all memories
    memories = list_memories(db)

    print("All memories:")
    for memory in memories:
        print(memory.subject, memory.object_value, memory.status)

    # Retrieve only active memories
    active_memories = list_memories(
        db, MemoryStatus.ACTIVE
    )

    print("\nActive memories:", len(active_memories))

    # Update the first memory, if one exists
    if memories:
        updated = update_memory_status(
            db,
            memories[0].memory_id,
            MemoryStatus.SUPERSEDED
        )

        print("\nUpdated memory:", updated.model_dump())