
from app.models.memory import Memory
from app.resolution.comparison import compare_memories


test_cases = [
    {
        "name": "Atlas",
        "existing": ("database", "uses_database", "PostgreSQL"),
        "candidate": ("database", "migrated_to", "MySQL"),
    },
    {
        "name": "Nova",
        "existing": ("cache", "uses_cache", "Redis"),
        "candidate": ("cache", "migrated_to", "Memcached"),
    },
    {
        "name": "Orion",
        "existing": ("API", "uses_framework", "FastAPI"),
        "candidate": ("API", "migrated_to", "Django"),
    },
    {
        "name": "Phoenix",
        "existing": ("frontend", "uses_framework", "React"),
        "candidate": ("frontend", "migrated_to", "Vue"),
    },
    {
        "name": "Mercury",
        "existing": ("vector_database", "uses_database", "FAISS"),
        "candidate": ("vector_database", "migrated_to", "Qdrant"),
    },
]


for case in test_cases:
    existing_data = case["existing"]
    candidate_data = case["candidate"]

    existing = Memory(
        subject=existing_data[0],
        predicate=existing_data[1],
        object_value=existing_data[2],
        source_id="test",
        confidence=1.0,
    )

    candidate = Memory(
        subject=candidate_data[0],
        predicate=candidate_data[1],
        object_value=candidate_data[2],
        source_id="test",
        confidence=1.0,
    )

    result = compare_memories(
        candidate=candidate,
        retrieved_memories=[existing],
    )

    comparison = result.comparisons[0]
    
    
additional_cases = [
    {
        "name": "Conflict",
        "existing": ("backend", "uses_language", "Python 3.12", None),
        "candidate": ("backend", "uses_language", "Python 3.13", None),
        "expected": "CONFLICT",
    },
    {
        "name": "Coexist",
        "existing": (
            "backend", "uses_language", "Python 3.12",
            "production environment"
        ),
        "candidate": (
            "backend", "uses_language", "Python 3.13",
            "development environment"
        ),
        "expected": "COEXIST",
    },
    {
        "name": "Unrelated",
        "existing": (
            "service", "supports_csv_exports", "CSV exports", None
        ),
        "candidate": (
            "service", "generates_weekly_reports",
            "weekly reports", None
        ),
        "expected": "UNRELATED",
    },
    {
        "name": "Duplicate",
        "existing": (
            "backend", "uses_language", "Python 3.12", None
        ),
        "candidate": (
            "backend", "runs_on", "Python 3.12", None
        ),
        "expected": "DUPLICATE",
    },
]


for case in additional_cases:
    existing_data = case["existing"]
    candidate_data = case["candidate"]

    existing = Memory(
        subject=existing_data[0],
        predicate=existing_data[1],
        object_value=existing_data[2],
        context=existing_data[3],
        source_id="test",
        confidence=1.0,
    )

    candidate = Memory(
        subject=candidate_data[0],
        predicate=candidate_data[1],
        object_value=candidate_data[2],
        context=candidate_data[3],
        source_id="test",
        confidence=1.0,
    )

    result = compare_memories(
        candidate=candidate,
        retrieved_memories=[existing],
    )

    comparison = result.comparisons[0]
    actual = comparison.relationship.value
    expected = case["expected"]

    print("=" * 55)
    print(f"Test:     {case['name']}")
    print(f"Expected: {expected}")
    print(f"Actual:   {actual}")
    print(f"Reason:   {comparison.reason}")
    print(
        "Result:   ",
        "PASS" if actual == expected else "FAIL"
    )

