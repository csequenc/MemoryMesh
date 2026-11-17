
import numpy as np

from app.models.memory import Memory, MemoryStatus
from app.retrieval import semantic_search


def make_memory(
    subject,
    predicate="uses",
    object_value="Python",
    context=None,
    status=MemoryStatus.ACTIVE,
):
    return Memory.model_construct(
        subject=subject,
        predicate=predicate,
        object_value=object_value,
        context=context,
        status=status,
    )


class FakeEmbeddingModel:
    def encode(self, text, normalize_embeddings=True):
        if isinstance(text, list):
            return np.zeros((len(text), 2), dtype=np.float32)

        return np.zeros(2, dtype=np.float32)


def setup_fake_embeddings(monkeypatch):
    monkeypatch.setattr(
        semantic_search,
        "model",
        FakeEmbeddingModel(),
    )

    monkeypatch.setattr(
        semantic_search,
        "_get_node_embedding",
        lambda label: np.zeros(2, dtype=np.float32),
    )


def test_node_labels_collect_subjects_only():
    memories = [
        make_memory("Alice", object_value="Python"),
        make_memory("Bob", object_value="FastAPI"),
        make_memory("Alice", object_value="PostgreSQL"),
    ]

    nodes = semantic_search._node_labels(memories)

    labels = [node["label"] for node in nodes.values()]

    assert labels == ["Alice", "Bob"]
    assert "Python" not in labels
    assert "FastAPI" not in labels
    assert "PostgreSQL" not in labels


def test_repeated_subject_is_collected_once():
    memories = [
        make_memory("Alice", predicate="uses", object_value="Python"),
        make_memory("Alice", predicate="knows", object_value="FastAPI"),
        make_memory("Alice", predicate="uses", object_value="PostgreSQL"),
    ]

    nodes = semantic_search._node_labels(memories)

    assert len(nodes) == 1

    alice = next(iter(nodes.values()))

    assert alice["label"] == "Alice"
    assert alice["connections"] == 3
    assert len(alice["examples"]) == 2


def test_exact_subject_mention_is_returned(monkeypatch):
    setup_fake_embeddings(monkeypatch)

    memories = [
        make_memory("Alice"),
        make_memory("Bob"),
    ]

    candidates = semantic_search.candidate_nodes(
        raw_text="Alice is learning Python",
        existing_memories=memories,
        min_score=0.99,
        fallback_minimum=0,
    )

    labels = [candidate["label"] for candidate in candidates]

    assert "Alice" in labels
    assert "Bob" not in labels


def test_object_value_is_not_returned_as_subject_candidate(monkeypatch):
    setup_fake_embeddings(monkeypatch)

    memories = [
        make_memory("Alice", object_value="Python"),
    ]

    candidates = semantic_search.candidate_nodes(
        raw_text="Python",
        existing_memories=memories,
        min_score=0.99,
        fallback_minimum=0,
    )

    labels = [candidate["label"] for candidate in candidates]

    assert "Python" not in labels
    assert "Alice" not in labels


def test_fallback_candidates_are_marked_as_fallback(monkeypatch):
    setup_fake_embeddings(monkeypatch)

    memories = [
        make_memory("Alice"),
        make_memory("Bob"),
        make_memory("Charlie"),
    ]

    candidates = semantic_search.candidate_nodes(
        raw_text="completely unrelated sentence",
        existing_memories=memories,
        min_score=1.1,
        fallback_minimum=2,
    )

    assert len(candidates) == 2
    assert all(candidate["fallback"] is True for candidate in candidates)


def test_fallback_prefers_most_connected_subjects(monkeypatch):
    setup_fake_embeddings(monkeypatch)

    memories = [
        make_memory("Alice"),
        make_memory("Bob"),
        make_memory("Bob"),
        make_memory("Bob"),
        make_memory("Charlie"),
        make_memory("Charlie"),
    ]

    candidates = semantic_search.candidate_nodes(
        raw_text="unrelated input",
        existing_memories=memories,
        min_score=1.1,
        fallback_minimum=2,
    )

    labels = [candidate["label"] for candidate in candidates]

    assert labels[0] == "Bob"
    assert labels[1] == "Charlie"
    assert all(candidate["fallback"] for candidate in candidates)


def test_candidate_limit_is_respected(monkeypatch):
    setup_fake_embeddings(monkeypatch)

    memories = [
        make_memory(f"Subject {index}")
        for index in range(30)
    ]

    candidates = semantic_search.candidate_nodes(
        raw_text="unrelated input",
        existing_memories=memories,
        k=25,
        min_score=1.1,
        fallback_minimum=30,
    )

    assert len(candidates) == 25


def test_full_context_retrieval_still_uses_complete_memory_text(monkeypatch):
    captured = {}

    class RetrievalModel:
        def encode(self, texts, normalize_embeddings=True):
            captured["texts"] = texts

            return np.array(
                [
                    [1.0, 0.0],  # New candidate
                    [0.0, 1.0],  # Existing memory 1
                    [1.0, 0.0],  # Existing memory 2
                ],
                dtype=np.float32,
            )

    monkeypatch.setattr(
        semantic_search,
        "model",
        RetrievalModel(),
    )

    candidate = make_memory(
        "Alice",
        predicate="uses_language",
        object_value="Python",
        context="Backend project",
    )

    memory_1 = make_memory(
        "Bob",
        predicate="studies",
        object_value="Mathematics",
        context="College",
    )

    memory_2 = make_memory(
        "Alice",
        predicate="uses_language",
        object_value="Python",
        context="Backend project",
    )

    results = semantic_search.retrieve_candidates(
        candidate,
        [memory_1, memory_2],
        top_k=1,
    )

    # Full-context text is still used for comparison retrieval.
    assert captured["texts"][0] == (
        "Alice | uses_language | Python | Backend project"
    )

    assert captured["texts"][1] == (
        "Bob | studies | Mathematics | College"
    )

    assert captured["texts"][2] == (
        "Alice | uses_language | Python | Backend project"
    )

    assert len(results) == 1
    assert results[0][0] is memory_2
    assert results[0][1] == 1.0
