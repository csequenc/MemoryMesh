
from app.ingestion.extraction import extract_memory

test_inputs = [
    "I switched the MemoryMesh backend to Python 3.12 on October 15, 2026.",
    "I started using Python 3.12 yesterday.",
    "I used Python 3.12 from October 15, 2026 until November 1, 2026.",
    "My backend uses Python 3.12."
]

for text in test_inputs:
    result = extract_memory(text)

    print("\nInput:", text)
    print("Valid from:", result.valid_from)
    print("Valid to:", result.valid_to)
    print("Confidence:", result.confidence)