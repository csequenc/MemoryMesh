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
BACKUP_PATH = BASE_DIR / "memorymesh.object_similarity_backup.db"
REPORT_PATH = BASE_DIR / "object_similarity_evaluation_report.json"


# Each case starts with exactly one seeded memory.
# The original database is restored after the evaluation.
#
# This suite focuses on object-value interpretation while keeping
# subject, predicate, and context as controlled as possible.
#
# Expected outcomes:
# DUPLICATE  = same underlying fact / equivalent object wording
# SUPERSEDE  = explicit replacement or migration
# UNRESOLVED = conflicting values without clear replacement intent
# ADD        = distinct facts that can coexist


CASES = [
    # Equivalent object names / wording
    {
        "id": "OS01",
        "category": "object_equivalence",
        "expected": "DUPLICATE",
        "seed": (
            "database",
            "uses_database",
            "PostgreSQL",
            "MemoryMesh production backend",
        ),
        "input": (
            "The production backend of MemoryMesh uses Postgres as its database."
        ),
    },
    {
        "id": "OS02",
        "category": "object_equivalence",
        "expected": "DUPLICATE",
        "seed": (
            "frontend",
            "uses_framework",
            "React",
            "Phoenix application",
        ),
        "input": "The Phoenix frontend is built with React.js.",
    },
    {
        "id": "OS03",
        "category": "object_equivalence",
        "expected": "DUPLICATE",
        "seed": (
            "vector database",
            "uses_vector_engine",
            "Qdrant",
            "Mercury project",
        ),
        "input": "Mercury uses the Qdrant vector database.",
    },

    # Similar-looking objects that are not equivalent
    {
        "id": "OS04",
        "category": "similar_but_distinct",
        "expected": "UNRESOLVED",
        "seed": (
            "backend",
            "uses_language",
            "Python 3.12",
            "MemoryMesh production backend",
        ),
        "input": "The MemoryMesh production backend uses Python 3.13.",
    },
    {
        "id": "OS05",
        "category": "similar_but_distinct",
        "expected": "UNRESOLVED",
        "seed": (
            "API",
            "uses_framework",
            "FastAPI",
            "MemoryMesh production API",
        ),
        "input": "The MemoryMesh production API uses Django.",
    },
    {
        "id": "OS06",
        "category": "similar_but_distinct",
        "expected": "UNRESOLVED",
        "seed": (
            "search service",
            "uses_search_engine",
            "Elasticsearch",
            "production search service",
        ),
        "input": "The production search service uses OpenSearch.",
    },
    {
        "id": "OS07",
        "category": "similar_but_distinct",
        "expected": "UNRESOLVED",
        "seed": (
            "vector search service",
            "uses_vector_engine",
            "Qdrant",
            "Mercury production environment",
        ),
        "input": "Mercury's production vector search service uses Weaviate.",
    },

    # Explicit replacement: similar/different values, clear temporal intent
    {
        "id": "OS08",
        "category": "explicit_replacement",
        "expected": "SUPERSEDE",
        "seed": (
            "backend",
            "uses_language",
            "Python 3.12",
            "MemoryMesh production backend",
        ),
        "input": (
            "We upgraded the MemoryMesh production backend from Python 3.12 "
            "to Python 3.13."
        ),
    },
    {
        "id": "OS09",
        "category": "explicit_replacement",
        "expected": "SUPERSEDE",
        "seed": (
            "API",
            "uses_framework",
            "FastAPI",
            "MemoryMesh production API",
        ),
        "input": (
            "We replaced FastAPI with Django for the MemoryMesh production API."
        ),
    },
    {
        "id": "OS10",
        "category": "explicit_replacement",
        "expected": "SUPERSEDE",
        "seed": (
            "search service",
            "uses_search_engine",
            "Elasticsearch",
            "production search service",
        ),
        "input": (
            "The production search service has migrated from Elasticsearch "
            "to OpenSearch."
        ),
    },

    # Similar or identical object values, but different scopes/purposes
    {
        "id": "OS11",
        "category": "contextual_coexistence",
        "expected": "ADD",
        "seed": (
            "payment service",
            "uses_payment_gateway",
            "Stripe",
            "one-time payments",
        ),
        "input": (
            "The payment service also uses Stripe for recurring subscription "
            "payments."
        ),
    },
    {
        "id": "OS12",
        "category": "contextual_coexistence",
        "expected": "ADD",
        "seed": (
            "backend",
            "uses_language",
            "Python 3.12",
            "development environment",
        ),
        "input": (
            "The backend uses Python 3.13 in the production environment."
        ),
    },
    {
        "id": "OS13",
        "category": "contextual_coexistence",
        "expected": "ADD",
        "seed": (
            "cache service",
            "uses_technology",
            "Redis",
            "caching",
        ),
        "input": (
            "The cache service also uses Redis as a message queue."
        ),
    },

    # Object values that are semantically related but belong to distinct facts
    {
        "id": "OS14",
        "category": "related_but_distinct",
        "expected": "ADD",
        "seed": (
            "analytics service",
            "exports_format",
            "CSV",
            "analytics export functionality",
        ),
        "input": "The analytics service also exports reports in JSON format.",
    },
    {
        "id": "OS15",
        "category": "related_but_distinct",
        "expected": "ADD",
        "seed": (
            "application",
            "supports_language",
            "English",
            "default interface language",
        ),
        "input": (
            "The application additionally supports Hindi as an interface language."
        ),
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
        source_id="object_similarity_evaluation_seed",
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
    # Keep this mapping consistent with the existing evaluation.py.
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
        "seed": {
            "subject": case["seed"][0],
            "predicate": case["seed"][1],
            "object_value": case["seed"][2],
            "context": case["seed"][3],
        },
        "input": case["input"],
    }

    db: Session = SessionLocal()

    try:
        # Isolate this case from every other case.
        db.execute(delete(MemoryModel))
        seed_memory = create_seed_memory(case)
        seed_memory_id = seed_memory.memory_id
        db.add(seed_memory)
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
            "seed_memory_id": seed_memory_id,
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
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    if BACKUP_PATH.exists():
        raise FileExistsError(
            f"Backup already exists: {BACKUP_PATH}\n"
            "Inspect it before running; the script will not overwrite it."
        )

    print("Creating database backup...")
    shutil.copy2(DB_PATH, BACKUP_PATH)

    results = []

    try:
        Base.metadata.create_all(bind=engine)

        print(f"\nRunning {len(CASES)} object-similarity cases...\n")

        for index, case in enumerate(CASES, start=1):
            print(
                f"[{index}/{len(CASES)}] "
                f"{case['id']} ({case['category']}) - {case['input']}"
            )

            result = run_case(case)
            results.append(result)

            status = "PASS" if result["passed"] else "FAIL"
            print(
                f"    {status}: expected={result['expected']}, "
                f"actual={result['actual']}\n"
            )

        passed = sum(1 for result in results if result["passed"])
        failed = len(results) - passed
        errors = sum(1 for result in results if "error" in result)

        category_summary = {}
        for category in sorted({case["category"] for case in CASES}):
            category_results = [
                result for result in results if result["category"] == category
            ]
            category_summary[category] = {
                "total": len(category_results),
                "passed": sum(
                    1 for result in category_results if result["passed"]
                ),
                "failed": sum(
                    1 for result in category_results if not result["passed"]
                ),
            }

        report = {
            "evaluation": "object_similarity",
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "category_summary": category_summary,
            "results": results,
        }

        REPORT_PATH.write_text(
            json.dumps(report, indent=2, default=str),
            encoding="utf-8",
        )

        print("=" * 55)
        print(f"TOTAL:  {len(results)}")
        print(f"PASSED: {passed}")
        print(f"FAILED: {failed}")
        print(f"ERRORS: {errors}")
        print("=" * 55)

        print("\nCategory summary:")
        for category, summary in category_summary.items():
            print(
                f"  {category}: {summary['passed']}/{summary['total']} passed"
            )

        print(f"\nReport saved to: {REPORT_PATH}")

    finally:
        # Close DB connections before restoring the original database.
        engine.dispose()

        print("\nRestoring original database...")
        shutil.copy2(BACKUP_PATH, DB_PATH)
        BACKUP_PATH.unlink()

        print("Original database restored.")


if __name__ == "__main__":
    main()
