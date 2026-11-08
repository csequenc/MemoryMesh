
from app.database.connection import SessionLocal, create_tables
from app.database.memory_repository import list_memories
from app.models.memory import MemoryStatus
from app.ingestion.memory_pipeline import process_user_input
from app.database.memory_repository import get_all_candidate_memories
from app.retrieval.semantic_search import retrieve_for_query
from app.query.answer import generate_answer


def display_memories(db, status=None):

    memories = list_memories(db, status=status)

    if not memories:
        print("\nNo memories found.")
        return

    print(f"\nFound {len(memories)} memories:\n")

    for index, memory in enumerate(memories, start=1):

        print(f"Memory {index}")
        print(f"ID: {memory.memory_id}")
        print(f"Subject: {memory.subject}")
        print(f"Predicate: {memory.predicate}")
        print(f"Value: {memory.object_value}")
        print(f"Context: {memory.context}")
        print(f"Status: {memory.status.value}")
        print(f"Confidence: {memory.confidence}")
        print("-" * 45)


def display_result(result):

    print("\n--- Extraction ---")
    print(result["extraction"])

    print("\n--- Comparisons ---")

    comparisons = result["comparisons"].comparisons

    if not comparisons:
        print("No relevant existing memories found.")
    else:
        for comparison in comparisons:
            print(f"Memory ID: {comparison.memory_id}")
            print(f"Relationship: {comparison.relationship.value}")
            print(f"Reason: {comparison.reason}")
            print()

    print("--- Resolution ---")

    plan = result["plan"]

    if not plan.should_insert:
        print("DUPLICATE: Memory was not inserted.")
        return

    for update in plan.updates:
        print(
            f"Updated memory {update.memory_id}: "
            f"{update.status.value}"
        )

    saved_memory = result["saved_memory"]

    if saved_memory:
        print(f"New memory saved as: {saved_memory.status.value}")
        print(f"Memory ID: {saved_memory.memory_id}")
        

def answer_question(db, query):
    memories = get_all_candidate_memories(db)

    results = retrieve_for_query(
        query=query,
        existing_memories=memories,
        top_k=5
    )

    retrieved_memories = [
        memory for memory, score in results
    ]

    result = generate_answer(
        query=query,
        retrieved_memories=retrieved_memories
    )

    print("\n--- Answer ---")
    print(result["answer"])

    print("\n--- Source Memories ---")
    for memory_id in result["source_memories"]:
        print(memory_id)


def main():

    create_tables()

    print("=" * 45)
    print("          MemoryMesh CLI")
    print("=" * 45)

    print("\nCommands:")
    print("  memories   - Show all memories")
    print("  active     - Show active memories")
    print("  unresolved - Show unresolved memories")
    print("  exit       - Quit MemoryMesh")
    print("  ask <question> - Ask MemoryMesh a question")

    with SessionLocal() as db:

        while True:

            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            command = user_input.lower()

            if command == "exit":
                print("\nMemoryMesh closed.")
                break

            elif command == "memories":
                display_memories(db)

            elif command == "active":
                display_memories(
                    db,
                    status=MemoryStatus.ACTIVE
                )

            elif command == "unresolved":
                display_memories(
                    db,
                    status=MemoryStatus.UNRESOLVED
                )
                
            elif command.startswith("ask "):
                query = user_input[4:].strip()

                if query:
                    try:
                        answer_question(db, query)
                    except Exception as error:
                        print(f"\nError answering question: {error}")
                else:
                    print("Please provide a question.")

            else:

                try:
                    result = process_user_input(
                        db=db,
                        user_input=user_input
                    )

                    display_result(result)

                except Exception as error:
                    print(f"\nError processing input: {error}")


if __name__ == "__main__":
    main()
