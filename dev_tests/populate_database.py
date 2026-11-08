
from app.database.connection import SessionLocal, create_tables
from app.database.memory_repository import list_memories
from app.models.memory import MemoryStatus
from app.ingestion.memory_pipeline import process_user_input


statements = [
    # New facts
    "The MemoryMesh project uses SQLite as its database.",
    "The MemoryMesh project uses all-MiniLM-L6-v2 for embeddings.",
    "The MemoryMesh API is built with FastAPI.",
    "The MemoryMesh frontend uses React and TypeScript.",

    # Potential updates or conflicts
    "The production backend uses Python 3.14.",
    "The production backend uses Python 3.15.",

    # Duplicate
    "The MemoryMesh project uses SQLite as its database.",

    # More independent facts
    "The MemoryMesh graph visualization uses Cytoscape.js.",
    "The MemoryMesh development server uses Uvicorn.",
    "The MemoryMesh source code is written in Python and TypeScript.",
]


def main():
    create_tables()

    with SessionLocal() as db:
        for index, statement in enumerate(statements, start=1):
            print(f"\n{'=' * 60}")
            print(f"Statement {index}/{len(statements)}")
            print(statement)

            try:
                result = process_user_input(
                    db=db,
                    user_input=statement,
                    top_k=5
                )

                extraction = result["extraction"]
                plan = result["plan"]
                saved_memory = result["saved_memory"]

                print(
                    f"Extracted: {extraction.subject} | "
                    f"{extraction.predicate} | "
                    f"{extraction.object_value}"
                )

                if saved_memory:
                    print(f"Saved status: {saved_memory.status.value}")
                else:
                    print("Not inserted (likely duplicate).")

                print(f"Existing memories updated: {len(plan.updates)}")

                for update in plan.updates:
                    print(
                        f"  {update.memory_id} -> "
                        f"{update.status.value}"
                    )

            except Exception as error:
                print(f"FAILED: {error}")

        print(f"\n{'=' * 60}")
        print("DATABASE SUMMARY")

        memories = list_memories(db)

        for status in MemoryStatus:
            count = sum(m.status == status for m in memories)
            print(f"{status.value}: {count}")

        print(f"Total memories: {len(memories)}")


if __name__ == "__main__":
    main()
