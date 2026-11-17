
import re
from difflib import SequenceMatcher

import numpy as np
from sentence_transformers import SentenceTransformer

from app.models.memory import Memory, MemoryStatus


model = SentenceTransformer("all-MiniLM-L6-v2")

# Node labels are stable across a process, so cache their normalized embeddings.
# This cache is intentionally in-memory; it does not change the database schema.
_node_embedding_cache: dict[str, np.ndarray] = {}


def memory_to_text(memory):
    parts = [
        memory.subject,
        memory.predicate,
        memory.object_value,
    ]

    if memory.context:
        parts.append(memory.context)

    return " | ".join(parts)


def normalize_node_label(value: str) -> str:
    """Normalize whitespace and case for node-label comparisons."""
    return " ".join(value.split()).casefold()


def _node_labels(existing_memories: list[Memory]):
    """Collect existing subject nodes and up to two example facts per node."""
    nodes: dict[str, dict] = {}

    for memory in existing_memories:
        fact = memory_to_text(memory)

        # Subject grounding only: object_value is intentionally excluded.
        label = " ".join(memory.subject.split())
        key = normalize_node_label(label)

        if not key:
            continue

        if key not in nodes:
            nodes[key] = {
                "label": label,
                "examples": [],
                "connections": 0,
            }

        nodes[key]["connections"] += 1

        if fact not in nodes[key]["examples"] and len(nodes[key]["examples"]) < 2:
            nodes[key]["examples"].append(fact)

    return nodes


def _text_phrases(text: str, max_words: int = 5) -> list[str]:
    words = re.findall(r"[\w]+(?:['’.-][\w]+)*", text.casefold())
    phrases = []

    for size in range(1, min(max_words, len(words)) + 1):
        phrases.extend(
            " ".join(words[index:index + size])
            for index in range(len(words) - size + 1)
        )

    return phrases


def _exact_label_match(label: str, text: str) -> bool:
    # Word boundaries avoid matching e.g. "Ann" inside "Annual".
    pattern = rf"(?<!\w){re.escape(label)}(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def _fuzzy_label_score(label: str, phrases: list[str]) -> float:
    if not phrases:
        return 0.0

    return max(
        SequenceMatcher(None, label.casefold(), phrase).ratio()
        for phrase in phrases
    )


def _get_node_embedding(label: str) -> np.ndarray:
    key = normalize_node_label(label)

    if key not in _node_embedding_cache:
        embedding = model.encode(
            label,
            normalize_embeddings=True
        )
        _node_embedding_cache[key] = np.asarray(embedding, dtype=np.float32)

    return _node_embedding_cache[key]


def candidate_nodes(
    raw_text: str,
    existing_memories: list[Memory],
    k: int = 25,
    min_score: float = 0.45,
    fallback_minimum: int = 5,
) -> list[dict]:
    """Find existing subject nodes that may be referenced by input text.

    Each result contains the canonical stored subject label, up to two example
    facts, a relevance score, and whether it was added by the connectivity
    fallback. Candidate selection is advisory: it does not merge or rename
    graph nodes.
    """
    if k <= 0 or not raw_text.strip() or not existing_memories:
        return []

    nodes = _node_labels(existing_memories)
    if not nodes:
        return []

    text_embedding = np.asarray(
        model.encode(raw_text, normalize_embeddings=True),
        dtype=np.float32
    )
    phrases = _text_phrases(raw_text)

    scored = []
    for key, node in nodes.items():
        label = node["label"]
        exact = _exact_label_match(label, raw_text)
        fuzzy = _fuzzy_label_score(label, phrases)
        embedding = _get_node_embedding(label)
        semantic = float(np.dot(embedding, text_embedding))

        # Exact mention dominates. Otherwise use the strongest of fuzzy and
        # embedding evidence; this only ranks candidates for the LLM.
        score = 1.0 if exact else max(fuzzy, semantic)

        scored.append({
            "label": label,
            "examples": list(node["examples"]),
            "score": float(score),
            "fallback": False,
            "connections": node["connections"],
            "_key": key,
        })

    scored.sort(
        key=lambda item: (item["score"], item["connections"]),
        reverse=True
    )

    selected = [
        item for item in scored
        if item["score"] >= min_score
    ][:k]

    # If text matching found too few plausible nodes, add the most-connected
    # remaining subject nodes as weak context. They are not automatic matches.
    if len(selected) < min(fallback_minimum, k):
        selected_keys = {item["_key"] for item in selected}
        remaining = [
            item for item in scored
            if item["_key"] not in selected_keys
        ]

        remaining.sort(
            key=lambda item: (item["connections"], item["score"]),
            reverse=True
        )

        needed = min(fallback_minimum, k) - len(selected)

        for item in remaining[:needed]:
            fallback_item = dict(item)
            fallback_item["fallback"] = True
            selected.append(fallback_item)

    return [
        {
            "label": item["label"],
            "examples": item["examples"][:2],
            "score": item["score"],
            "fallback": item["fallback"],
        }
        for item in selected[:k]
    ]


def retrieve_candidates(
    candidate,
    existing_memories,
    top_k=5
):
    existing_memories = [
        memory for memory in existing_memories
        if memory.status.value in ("ACTIVE", "UNRESOLVED")
    ]

    if not existing_memories:
        return []

    candidate_text = memory_to_text(candidate)

    existing_texts = [
        memory_to_text(memory)
        for memory in existing_memories
    ]

    embeddings = model.encode(
        [candidate_text] + existing_texts,
        normalize_embeddings=True
    )

    candidate_embedding = embeddings[0]
    existing_embeddings = embeddings[1:]

    scores = existing_embeddings @ candidate_embedding

    ranked = sorted(
        zip(existing_memories, scores),
        key=lambda item: item[1],
        reverse=True
    )

    return [
        (memory, float(score))
        for memory, score in ranked[:top_k]
    ]


def retrieve_for_query(
    query: str,
    existing_memories: list[Memory],
    top_k: int = 5
):
    """Retrieve memories relevant to a natural-language query."""

    # Only retrieve current or unresolved memories
    eligible_memories = [
        memory for memory in existing_memories
        if memory.status in (
            MemoryStatus.ACTIVE,
            MemoryStatus.UNRESOLVED
        )
    ]

    if not eligible_memories:
        return []

    # Convert memories into searchable text
    memory_texts = [
        memory_to_text(memory)
        for memory in eligible_memories
    ]

    # Generate embeddings
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    memory_embeddings = model.encode(
        memory_texts,
        normalize_embeddings=True
    )

    # Calculate cosine similarity
    scores = memory_embeddings @ query_embedding

    # Rank memories by similarity
    ranked_indices = scores.argsort()[::-1][:top_k]

    results = [
        (eligible_memories[index], float(scores[index]))
        for index in ranked_indices
    ]

    # Remove low-relevance results
    results = [
        (memory, score)
        for memory, score in results
        if score >= 0.30
    ]

    return results
