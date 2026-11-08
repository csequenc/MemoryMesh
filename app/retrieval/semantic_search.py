from sentence_transformers import SentenceTransformer
from app.models.memory import Memory, MemoryStatus

model = SentenceTransformer("all-MiniLM-L6-v2")


def memory_to_text(memory):
    parts = [
        memory.subject,
        memory.predicate,
        memory.object_value,
    ]

    if memory.context:
        parts.append(memory.context)

    return " | ".join(parts)


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
    """
    Retrieve memories relevant to a natural-language query.
    """

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
