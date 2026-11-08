from app.database.connection import SessionLocal
from app.ingestion.memory_pipeline import process_user_input

db = SessionLocal()

try:
    result = process_user_input(
        db,
        "I started using Python 3.12 for my MemoryMesh backend on October 15, 2026."
    )

    print("Extraction:")
    print(result["extraction"])

    print("\nSaved memory:")
    print(result["saved_memory"])

    if result["saved_memory"]:
        print("\nTemporal fields:")
        print("Valid from:", result["saved_memory"].valid_from)
        print("Valid to:", result["saved_memory"].valid_to)
        print("Recorded at:", result["saved_memory"].recorded_at)

finally:
    db.close()