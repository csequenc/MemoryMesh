
import json
import shutil
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database.connection import Base, engine, SessionLocal
from app.database.memory_model import MemoryModel
from app.ingestion.memory_pipeline import process_user_input


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "memorymesh.db"
BACKUP_PATH = BASE_DIR / "memorymesh.evaluation_backup.db"
REPORT_PATH = BASE_DIR / "evaluation_report.json"


# Each case starts with exactly one seeded memory.
# The original database is restored after the evaluation.

CASES = [
    # DUPLICATE
    {
        "id": "D01",
        "category": "duplicate",
        "expected": "DUPLICATE",
        "seed": ("backend", "uses_language", "Python 3.12", "MemoryMesh project"),
        "input": "Python 3.12 is the language used by the MemoryMesh backend.",
    },
    {
        "id": "D02",
        "category": "duplicate",
        "expected": "DUPLICATE",
        "seed": ("API", "uses_framework", "FastAPI", "MemoryMesh project"),
        "input": "FastAPI is the framework behind the MemoryMesh API.",
    },
    {
        "id": "D03",
        "category": "duplicate",
        "expected": "DUPLICATE",
        "seed": (
            "graph visualization",
            "uses_graph_visualization_library",
            "Cytoscape.js",
            "MemoryMesh project",
        ),
        "input": "Cytoscape.js powers the MemoryMesh graph visualization.",
    },
    {
        "id": "D04",
        "category": "duplicate",
        "expected": "DUPLICATE",
        "seed": (
            "MemoryMesh project",
            "uses_embedding_model",
            "all-MiniLM-L6-v2",
            None,
        ),
        "input": "The embedding model for MemoryMesh is all-MiniLM-L6-v2.",
    },
    {
        "id": "D05",
        "category": "duplicate",
        "expected": "DUPLICATE",
        "seed": (
            "Mercury project",
            "uses_vector_search_engine",
            "Qdrant",
            None,
        ),
        "input": "Qdrant is the vector search engine used by Mercury.",
    },

    # CONFLICT
    {
        "id": "C01",
        "category": "conflict",
        "expected": "UNRESOLVED",
        "seed": ("backend", "uses_language", "Python 3.12", "MemoryMesh project"),
        "input": "The MemoryMesh backend uses Java.",
    },
    {
        "id": "C02",
        "category": "conflict",
        "expected": "UNRESOLVED",
        "seed": ("API", "uses_framework", "FastAPI", "MemoryMesh project"),
        "input": "The MemoryMesh API uses Django.",
    },
    {
        "id": "C03",
        "category": "conflict",
        "expected": "UNRESOLVED",
        "seed": (
            "Mercury project",
            "uses_vector_search_engine",
            "Qdrant",
            None,
        ),
        "input": "The Mercury project uses Weaviate for vector search.",
    },
    {
        "id": "C04",
        "category": "conflict",
        "expected": "ADD",
        "seed": (
            "search service",
            "uses_indexing_engine",
            "Elasticsearch",
            None,
        ),
        "input": "The search service uses OpenSearch.",
    },
    {
        "id": "C05",
        "category": "conflict",
        "expected": "UNRESOLVED",
        "seed": (
            "billing service",
            "uses_payment_gateway",
            "Razorpay",
            None,
        ),
        "input": "The billing service uses PayPal as its payment gateway.",
    },

    # SUPERSESSION
    {
        "id": "S01",
        "category": "supersession",
        "expected": "SUPERSEDE",
        "seed": ("backend", "uses_language", "Python 3.12", "MemoryMesh project"),
        "input": "The MemoryMesh backend has migrated from Python 3.12 to Python 3.13.",
    },
    {
        "id": "S02",
        "category": "supersession",
        "expected": "SUPERSEDE",
        "seed": ("API", "uses_framework", "FastAPI", "MemoryMesh project"),
        "input": "We replaced FastAPI with Django for the MemoryMesh API.",
    },
    {
        "id": "S03",
        "category": "supersession",
        "expected": "SUPERSEDE",
        "seed": (
            "Mercury project",
            "uses_vector_search_engine",
            "Qdrant",
            None,
        ),
        "input": "Mercury has switched its vector search engine from Qdrant to Weaviate.",
    },
    {
        "id": "S04",
        "category": "supersession",
        "expected": "SUPERSEDE",
        "seed": (
            "search service",
            "uses_search_engine",
            "Elasticsearch",
            None,
        ),
        "input": "We migrated the search service from Elasticsearch to OpenSearch.",
    },
    {
        "id": "S05",
        "category": "supersession",
        "expected": "SUPERSEDE",
        "seed": ("frontend", "uses_framework", "Vue", "Phoenix project"),
        "input": "The Phoenix frontend has been migrated from Vue to React.",
    },

    # CONTEXT / COEXISTENCE
    {
        "id": "X01",
        "category": "context",
        "expected": "ADD",
        "seed": ("backend", "uses_language", "Python 3.12", "MemoryMesh project"),
        "input": "The MemoryMesh frontend uses TypeScript.",
    },
    {
        "id": "X02",
        "category": "context",
        "expected": "ADD",
        "seed": (
            "payment service",
            "uses_payment_gateway",
            "Razorpay",
            "one-time payments",
        ),
        "input": (
            "The payment service also uses Stripe specifically "
            "for recurring subscription payments."
        ),
    },
    {
        "id": "X03",
        "category": "context",
        "expected": "ADD",
        "seed": (
            "analytics service",
            "supports_csv_exports",
            "CSV exports",
            None,
        ),
        "input": "The analytics service also supports JSON exports.",
    },
    {
        "id": "X04",
        "category": "context",
        "expected": "ADD",
        "seed": (
            "application",
            "supports_language",
            "English",
            "default interface language",
        ),
        "input": (
            "The application also supports Hindi "
            "as an additional interface language."
        ),
    },
    {
        "id": "X05",
        "category": "context",
        "expected": "ADD",
        "seed": (
            "backend",
            "uses_language",
            "Python 3.14",
            "development environment",
        ),
        "input": "The backend uses Python 3.15 in production.",
    },

    # UNRELATED
    {
        "id": "U01",
        "category": "unrelated",
        "expected": "ADD",
        "seed": ("API", "uses_framework", "FastAPI", "MemoryMesh project"),
        "input": "The analytics service supports CSV exports.",
    },
    {
        "id": "U02",
        "category": "unrelated",
        "expected": "ADD",
        "seed": (
            "Mercury project",
            "uses_vector_search_engine",
            "Qdrant",
            None,
        ),
        "input": "The documentation website uses Markdown.",
    },
    {
        "id": "U03",
        "category": "unrelated",
        "expected": "ADD",
        "seed": (
            "search service",
            "uses_indexing_engine",
            "Elasticsearch",
            None,
        ),
        "input": "The authentication service supports OAuth 2.0.",
    },
    {
        "id": "U04",
        "category": "unrelated",
        "expected": "ADD",
        "seed": (
            "billing service",
            "uses_payment_gateway",
            "Razorpay",
            None,
        ),
        "input": "The deployment pipeline runs automated tests.",
    },
    {
        "id": "U05",
        "category": "unrelated",
        "expected": "ADD",
        "seed": ("frontend", "uses_framework", "Vue", "Phoenix project"),
        "input": "The notification service uses Amazon SES for email.",
    },
]


def create_seed_memory(case):
    subject, predicate, object_value, context = case["seed"]

    return MemoryModel(
        memory_id=str(uuid.uuid4()),
        subject=subject,
        predicate=predicate,
        object_value=object_value,
        context=context,
        source_id="evaluation_seed",
        confidence=1.0,
        status="ACTIVE",
        valid_from=None,
        valid_to=None,
        recorded_at=datetime.now(timezone.utc),
    )


def serialize_model(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def get_actual_outcome(plan):
    if not plan.should_insert:
        return "DUPLICATE"

    if plan.candidate_status == "UNRESOLVED":
        return "UNRESOLVED"

    if any(update.status == "SUPERSEDED" for update in plan.updates):
        return "SUPERSEDE"

    return "ADD"


def get_database_state(db):
    memories = db.execute(
        select(MemoryModel).order_by(MemoryModel.recorded_at)
    ).scalars().all()

    return [
        {
            "memory_id": memory.memory_id,
            "subject": memory.subject,
            "predicate": memory.predicate,
            "object_value": memory.object_value,
            "context": memory.context,
            "status": memory.status,
        }
        for memory in memories
    ]


def run_case(case):
    result_entry = {
        "id": case["id"],
        "category": case["category"],
        "expected": case["expected"],
        "actual": "ERROR",
        "passed": False,
        "input": case["input"],
    }

    db: Session = SessionLocal()

    try:
        # Isolate this test from all other test cases.
        db.execute(delete(MemoryModel))
        db.add(create_seed_memory(case))
        db.commit()

        result = process_user_input(
            db=db,
            user_input=case["input"],
            top_k=5,
        )

        plan = result["plan"]
        comparison_result = result["comparisons"]
        extraction = result["extraction"]

        actual = get_actual_outcome(plan)

        result_entry.update({
            "actual": actual,
            "passed": actual == case["expected"],
            "extraction": serialize_model(extraction),
            "retrieved_count": len(comparison_result.comparisons),
            "comparisons": [
                serialize_model(comparison)
                for comparison in comparison_result.comparisons
            ],
            "resolution_plan": serialize_model(plan),
            "final_database_state": get_database_state(db),
        })

    except Exception as error:
        db.rollback()

        result_entry["error"] = str(error)
        result_entry["traceback"] = traceback.format_exc()

    finally:
        db.close()

    return result_entry


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    if BACKUP_PATH.exists():
        raise FileExistsError(
            f"Backup already exists: {BACKUP_PATH}\n"
            "Check this backup before running again."
        )

    print("Creating database backup...")
    shutil.copy2(DB_PATH, BACKUP_PATH)

    results = []

    try:
        Base.metadata.create_all(bind=engine)

        print(f"\nRunning {len(CASES)} evaluation cases...\n")

        for index, case in enumerate(CASES, start=1):
            print(
                f"[{index}/{len(CASES)}] "
                f"{case['id']} - {case['input']}"
            )

            result = run_case(case)
            results.append(result)

            status = "PASS" if result["passed"] else "FAIL"
            print(f"    {status}: expected={result['expected']}, "
                  f"actual={result['actual']}\n")

        passed = sum(1 for result in results if result["passed"])
        failed = len(results) - passed
        errors = sum(1 for result in results if "error" in result)

        report = {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "results": results,
        }

        REPORT_PATH.write_text(
            json.dumps(report, indent=2, default=str),
            encoding="utf-8",
        )

        print("=" * 50)
        print(f"TOTAL:  {len(results)}")
        print(f"PASSED: {passed}")
        print(f"FAILED: {failed}")
        print(f"ERRORS: {errors}")
        print("=" * 50)
        print(f"\nReport saved to: {REPORT_PATH}")

    finally:
        # Close connections before restoring the original database.
        engine.dispose()

        print("\nRestoring original database...")
        shutil.copy2(BACKUP_PATH, DB_PATH)
        BACKUP_PATH.unlink()

        print("Original database restored.")


if __name__ == "__main__":
    main()
