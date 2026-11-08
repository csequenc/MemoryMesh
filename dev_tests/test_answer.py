from app.database.connection import SessionLocal
from app.database.memory_repository import get_all_candidate_memories
from app.retrieval.semantic_search import retrieve_for_query
from app.query.answer import generate_answer


query = "What programming language does my backend use?"

with SessionLocal() as db:
    memories = get_all_candidate_memories(db)

    retrieved_results = retrieve_for_query(
        query=query,
        existing_memories=memories,
        top_k=5
    )

    retrieved_memories = [
        memory for memory, score in retrieved_results
    ]

    result = generate_answer(
        query=query,
        retrieved_memories=retrieved_memories
    )

    print("\nQuestion:", query)
    print("\nAnswer:", result["answer"])

    print("\nSource memories:")
    for memory_id in result["source_memories"]:
        print(memory_id)