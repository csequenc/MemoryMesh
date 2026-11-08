
import json
from pathlib import Path

from app.database.connection import SessionLocal, create_tables
from app.ingestion.memory_pipeline import process_user_input

from dev_tests.dataset import DATASET


RESULTS_PATH = Path(__file__).with_name("evaluation_results.json")


def load_results():
    if not RESULTS_PATH.exists():
        return []

    with open(RESULTS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def save_results(results):
    with open(RESULTS_PATH, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4, ensure_ascii=False)


def run_evaluation():

    results = load_results()

    completed_ids = {
        result["id"]
        for result in results
    }

    remaining = [
        item for item in DATASET
        if item["id"] not in completed_ids
    ]

    print("=" * 65)
    print("             MEMORYMESH EVALUATION")
    print("=" * 65)

    print(f"Total statements: {len(DATASET)}")
    print(f"Already completed: {len(completed_ids)}")
    print(f"Remaining: {len(remaining)}")
    print(f"Database: Existing MemoryMesh database")
    print()

    if not remaining:
        print("All statements have already been processed.")
        return

    confirmation = input(
        "This will modify your existing database.\n"
        "Type RUN to continue: "
    )

    if confirmation != "RUN":
        print("Evaluation cancelled.")
        return

    create_tables()

    with SessionLocal() as db:

        for item in remaining:

            print("\n" + "=" * 65)
            print(f"Statement {item['id']}/50")
            print(f"Category: {item['category']}")
            print(f"Input: {item['input']}")
            print("-" * 65)

            record = {
                **item,
                "success": False
            }

            try:
                result = process_user_input(
                    db=db,
                    user_input=item["input"],
                    top_k=5
                )

                extraction = result["extraction"]
                comparisons = result["comparisons"]
                plan = result["plan"]
                saved_memory = result["saved_memory"]

                record["extraction"] = extraction.model_dump(
                    mode="json"
                )

                record["comparisons"] = comparisons.model_dump(
                    mode="json"
                )

                record["resolution_plan"] = plan.model_dump(
                    mode="json"
                )

                record["saved_memory"] = (
                    saved_memory.model_dump(mode="json")
                    if saved_memory is not None
                    else None
                )

                record["success"] = True

                print("\nExtraction:")
                print(
                    f"{extraction.subject} "
                    f"{extraction.predicate} "
                    f"{extraction.object_value}"
                )
                print(f"Context: {extraction.context}")

                print("\nComparisons:")

                if not comparisons.comparisons:
                    print("No existing memories retrieved.")

                for comparison in comparisons.comparisons:
                    print(
                        f"- {comparison.relationship.value}: "
                        f"{comparison.reason}"
                    )

                print("\nResolution plan:")
                print(f"Should insert: {plan.should_insert}")
                print(f"Candidate status: {plan.candidate_status}")
                print(f"Updates: {len(plan.updates)}")

                for update in plan.updates:
                    print(
                        f"- {update.memory_id} -> "
                        f"{update.status.value}"
                    )

                if saved_memory:
                    print(
                        f"\nSaved memory: "
                        f"{saved_memory.memory_id}"
                    )
                    print(
                        f"Saved status: "
                        f"{saved_memory.status.value}"
                    )
                else:
                    print("\nCandidate was not inserted.")

            except Exception as error:
                record["error"] = str(error)

                print(f"\nFAILED: {error}")

            results.append(record)

            # Persist progress after every statement.
            save_results(results)

    successful = sum(
        1 for result in results
        if result["success"]
    )

    failed = len(results) - successful

    print("\n" + "=" * 65)
    print("             EVALUATION SUMMARY")
    print("=" * 65)

    print(f"Processed: {len(results)}/50")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Results saved to: {RESULTS_PATH}")


if __name__ == "__main__":
    run_evaluation()
