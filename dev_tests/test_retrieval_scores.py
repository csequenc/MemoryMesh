from app.database.connection import SessionLocal
from app.database.memory_repository import get_all_candidate_memories
from app.retrieval.semantic_search import retrieve_for_query


queries = [
    "What programming language does my backend use?",
    "What database does my project use?",
    "What frontend framework do I use?",
]

with SessionLocal() as db:
    memories = get_all_candidate_memories(db)

    for query in queries:
        print("\nQuery:", query)

        results = retrieve_for_query(
            query=query,
            existing_memories=memories,
            top_k=5
        )

        for memory, score in results:
            print(
                f"{memory.subject} | "
                f"{memory.object_value} | "
                f"Score: {score:.4f}"
            )