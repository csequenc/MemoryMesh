
from app.database.connection import SessionLocal
from app.database.memory_repository import get_all_candidate_memories
from app.retrieval.semantic_search import retrieve_for_query


with SessionLocal() as db:

    memories = get_all_candidate_memories(db)

    query = "What programming language does my backend use?"

    results = retrieve_for_query(
        query=query,
        existing_memories=memories,
        top_k=5
    )

    print("\nQuery:", query)
    print("\nRetrieved memories:")

    for memory, score in results:
        print("-" * 40)
        print("Memory:", memory.subject, memory.predicate, memory.object_value)
        print("Context:", memory.context)
        print("Status:", memory.status.value)
        print("Similarity:", round(score, 4))
