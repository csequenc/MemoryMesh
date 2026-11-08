
from app.ingestion.extraction import extract_memory


test_inputs = [
    "I switched the MemoryMesh backend to Python 3.12.",
    "My RAG project uses FAISS for vector search.",
    "I work on MemoryMesh as an AI memory engine."
]

for user_input in test_inputs:

    print("\nInput:", user_input)

    extracted = extract_memory(user_input)

    print("Extracted:")
    print(extracted.model_dump())
