
from app.database.connection import SessionLocal
from app.database.memory_repository import list_memories

db = SessionLocal()

try:
    memories = list_memories(db)

    for memory in memories:
        print("\n" + "=" * 60)
        print(f"Memory ID:   {memory.memory_id}")
        print(f"Subject:     {memory.subject}")
        print(f"Predicate:   {memory.predicate}")
        print(f"Object:      {memory.object_value}")
        print(f"Context:     {memory.context}")
        print(f"Source:      {memory.source_id}")
        print(f"Confidence:  {memory.confidence}")
        print(f"Status:      {memory.status.value}")
        print(f"Valid From:  {memory.valid_from}")
        print(f"Valid To:    {memory.valid_to}")
        print(f"Recorded At: {memory.recorded_at}")

    print("\n" + "=" * 60)
    print(f"Total memories: {len(memories)}")

finally:
    db.close()
