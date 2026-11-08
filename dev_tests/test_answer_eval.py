
from app.models.memory import Memory, MemoryStatus
from app.retrieval.semantic_search import retrieve_for_query
from app.query.answer import generate_answer


memories = [
    Memory(
        memory_id="m1",
        subject="backend",
        predicate="uses_language",
        object_value="Python 3.13",
        context="MemoryMesh project",
        source_id="test",
        confidence=1.0
    ),
    Memory(
        memory_id="m2",
        subject="RAG project",
        predicate="uses_vector_search_engine",
        object_value="FAISS",
        context="RAG project",
        source_id="test",
        confidence=1.0
    ),
    Memory(
        memory_id="m3",
        subject="RAG project",
        predicate="uses_llm_provider",
        object_value="Groq",
        context="RAG project",
        source_id="test",
        confidence=1.0
    ),
    Memory(
        memory_id="m5",
        subject="MemoryMesh",
        predicate="uses_database",
        object_value="SQLite",
        context="MemoryMesh project",
        source_id="test",
        confidence=1.0
    )
]


queries = [
    "What programming language does the MemoryMesh backend use?",
    "What database does my RAG project use?",
    "What database does MemoryMesh use?",
    "What technologies does my RAG project use?"
]


for query in queries:
    print("\n" + "=" * 60)
    print("Question:", query)

    retrieved_results = retrieve_for_query(
        query=query,
        existing_memories=memories,
        top_k=5
    )

    retrieved_memories = [
        memory for memory, score in retrieved_results
    ]

    print("\nRetrieved IDs:", [
        memory.memory_id for memory in retrieved_memories
    ])

    result = generate_answer(
        query=query,
        retrieved_memories=retrieved_memories
    )

    print("\nAnswer:", result["answer"])
    print("Relevant source IDs:", result["source_memories"])
