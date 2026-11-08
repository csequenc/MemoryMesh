from app.database.connection import SessionLocal, create_tables
from app.models.memory import Memory
from app.ingestion.memory_pipeline import process_memory


create_tables()

db = SessionLocal()

try:
    candidate = Memory(
        subject="backend",
        predicate="uses_language",
        object_value="Python 3.14",
        context="production environment",
        source_id="pipeline_test_2",
        confidence=0.95
    )

    result = process_memory(db, candidate)

    print("\nDecision:")
    print(result["decision"].model_dump())

    print("\nSaved memory:")
    print(result["saved_memory"])

finally:
    db.close()