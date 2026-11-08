from app.models.memory import Memory, MemoryStatus
from app.retrieval.semantic_search import retrieve_for_query


# Synthetic test memories.
# These are only for evaluation and won't be saved to SQLite.

memories = [
    Memory(
        memory_id="m1",
        subject="backend",
        predicate="uses_language",
        object_value="Python 3.13",
        context="MemoryMesh project",
        source_id="test",
        confidence=1.0,
        status=MemoryStatus.ACTIVE
    ),
    Memory(
        memory_id="m2",
        subject="RAG project",
        predicate="uses_vector_search_engine",
        object_value="FAISS",
        context="RAG project",
        source_id="test",
        confidence=1.0,
        status=MemoryStatus.ACTIVE
    ),
    Memory(
        memory_id="m3",
        subject="RAG project",
        predicate="uses_llm_provider",
        object_value="Groq",
        context="RAG project",
        source_id="test",
        confidence=1.0,
        status=MemoryStatus.ACTIVE
    ),
    Memory(
        memory_id="m4",
        subject="frontend",
        predicate="uses_framework",
        object_value="React",
        context="College project",
        source_id="test",
        confidence=1.0,
        status=MemoryStatus.ACTIVE
    ),
    Memory(
        memory_id="m5",
        subject="MemoryMesh",
        predicate="uses_database",
        object_value="SQLite",
        context="MemoryMesh project",
        source_id="test",
        confidence=1.0,
        status=MemoryStatus.ACTIVE
    ),
]


# Each query has manually defined relevant memory IDs.
evaluation_data = [
    {
        "query": "What programming language does the MemoryMesh backend use?",
        "relevant_ids": ["m1"]
    },
    {
        "query": "Which language is my backend written in?",
        "relevant_ids": ["m1"]
    },
    {
        "query": "Which vector search engine powers my RAG project?",
        "relevant_ids": ["m2"]
    },
    {
        "query": "What LLM provider does my RAG project use?",
        "relevant_ids": ["m3"]
    },
    {
        "query": "Which frontend framework does my college project use?",
        "relevant_ids": ["m4"]
    },
    {
        "query": "Which technologies does my RAG project use?",
        "relevant_ids": ["m2", "m3"]
    },
    {
        "query": "What database does MemoryMesh use?",
        "relevant_ids": ["m5"]
    },
    {
        "query": "What database does my RAG project use?",
        "relevant_ids": []
    },
]


true_positives = 0
false_positives = 0
false_negatives = 0

no_answer_correct = 0
no_answer_total = 0


for item in evaluation_data:
    query = item["query"]
    relevant_ids = set(item["relevant_ids"])

    results = retrieve_for_query(
        query=query,
        existing_memories=memories,
        top_k=5
    )

    retrieved_ids = {
        memory.memory_id for memory, score in results
    }

    tp = len(retrieved_ids & relevant_ids)
    fp = len(retrieved_ids - relevant_ids)
    fn = len(relevant_ids - retrieved_ids)

    true_positives += tp
    false_positives += fp
    false_negatives += fn

    if not relevant_ids:
        no_answer_total += 1
        if not retrieved_ids:
            no_answer_correct += 1

    print("\n" + "=" * 60)
    print("Query:", query)
    print("Expected:", relevant_ids)

    print("Retrieved:")
    if not results:
        print("No memories found.")
    else:
        for memory, score in results:
            print(
                f"{memory.memory_id} | "
                f"{memory.object_value} | "
                f"Score: {score:.4f}"
            )

    print(f"TP: {tp} | FP: {fp} | FN: {fn}")


precision = (
    true_positives / (true_positives + false_positives)
    if true_positives + false_positives > 0
    else 0
)

recall = (
    true_positives / (true_positives + false_negatives)
    if true_positives + false_negatives > 0
    else 0
)


print("\n" + "=" * 60)
print("EVALUATION RESULTS")
print("=" * 60)

print(f"Precision: {precision:.2%}")
print(f"Recall:    {recall:.2%}")

print(
    f"No-answer queries: "
    f"{no_answer_correct}/{no_answer_total} correct"
)