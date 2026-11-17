import logging
import re
import unicodedata
from collections import Counter

from sqlalchemy.orm import Session

from app.models.memory import Memory

from app.database.memory_repository import (
    get_all_candidate_memories,
    list_memories,
    apply_resolution,
)

from app.retrieval.semantic_search import (
    candidate_nodes,
    model as embedding_model,
    retrieve_candidates,
)

from app.resolution.comparison import compare_memories
from app.resolution.resolver import resolve_comparisons

from app.ingestion.extraction import extract_memory


logger = logging.getLogger(__name__)


def _normalize_subject_key(value: str) -> str:
    """Create a comparison key without changing the stored canonical label."""
    value = unicodedata.normalize("NFKC", value).casefold().strip()

    # Ignore ordinary punctuation differences while preserving meaningful
    # technical-name characters such as +, #, . and - inside labels.
    value = re.sub(r"(?<!\w)[,;:!?]+|[,;:!?]+(?!\w)", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n,;:!?")


def _normalize_new_subject(value: str) -> str:
    """Clean spacing and surrounding punctuation for a genuinely new label."""
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value.strip(" \t\r\n,;:!?")


def _ground_subject(subject: str, nodes: list[dict]) -> tuple[str, str]:
    """Reuse a candidate's exact label only when extraction selected that label.

    Candidate retrieval can use fuzzy and semantic similarity, but those scores
    never merge entities. The extraction model must choose the canonical label.
    An unrecognized label remains a new subject.
    """
    subject_key = _normalize_subject_key(subject)

    for node in nodes:
        canonical_label = node.get("label", "")
        if subject_key and subject_key == _normalize_subject_key(canonical_label):
            return canonical_label, "existing"

    return _normalize_new_subject(subject), "new"


def _select_existing_predicates(
    raw_text: str,
    existing_memories: list[Memory],
    limit: int = 15,
) -> list[str]:
    """Select predicates using both frequency and semantic similarity."""
    if limit <= 0 or not existing_memories:
        return []

    counts = Counter(
        memory.predicate.strip()
        for memory in existing_memories
        if memory.predicate and memory.predicate.strip()
    )
    if not counts:
        return []

    # Reserve most of the slots for frequently used predicates.
    frequent = [predicate for predicate, _ in counts.most_common(limit)]
    selected = frequent[: min(8, limit)]

    # Fill the remaining slots with predicates most similar to the input.
    remaining = [predicate for predicate in counts if predicate not in selected]
    if remaining and len(selected) < limit:
        embeddings = embedding_model.encode(
            [raw_text] + remaining,
            normalize_embeddings=True,
        )
        query_embedding = embeddings[0]
        predicate_embeddings = embeddings[1:]
        ranked = sorted(
            zip(remaining, predicate_embeddings),
            key=lambda item: float(item[1] @ query_embedding),
            reverse=True,
        )

        for predicate, _ in ranked:
            if predicate not in selected:
                selected.append(predicate)
            if len(selected) >= limit:
                break

    # If there were fewer than eight distinct predicates, fill any remaining
    # slots from the frequency ranking without introducing duplicates.
    for predicate in frequent:
        if len(selected) >= limit:
            break
        if predicate not in selected:
            selected.append(predicate)

    return selected[:limit]


def process_memory(
    db: Session,
    candidate: Memory,
    top_k: int = 5,
    source_text: str | None = None,
):
    # Step 1: Get active and unresolved memories for conflict resolution.
    existing_memories = get_all_candidate_memories(db)

    # Step 2: Retrieve semantically relevant memories.
    retrieved = retrieve_candidates(
        candidate=candidate,
        existing_memories=existing_memories,
        top_k=top_k,
    )

    retrieved_memories = [memory for memory, score in retrieved]

    # Step 3: Compare candidate against retrieved memories.
    comparison_result = compare_memories(
        candidate=candidate,
        retrieved_memories=retrieved_memories,
        source_text=source_text,
    )

    # Step 4: Generate resolution plan.
    plan = resolve_comparisons(comparison_result)

    # Step 5: Apply plan to SQLite.
    saved_memory = apply_resolution(
        db=db,
        candidate=candidate,
        plan=plan,
    )

    return {
        "comparisons": comparison_result,
        "plan": plan,
        "saved_memory": saved_memory,
    }


def process_user_input(
    db: Session,
    user_input: str,
    top_k: int = 5,
):
    # Step 1: Read all non-deleted memories. Graph nodes are derived from all
    # retained memories, including superseded history, so grounding uses the
    # same node population as the graph itself.
    all_memories = list_memories(db)

    # Step 2: Find possible existing subject nodes before extraction.
    nodes = candidate_nodes(
        raw_text=user_input,
        existing_memories=all_memories,
        k=25,
    )

    # Step 3: Supply a compact vocabulary of existing predicates as well.
    predicates = _select_existing_predicates(
        raw_text=user_input,
        existing_memories=all_memories,
        limit=15,
    )

    # Step 4: Extract with candidate graph nodes and predicates available.
    extracted = extract_memory(
        user_input,
        candidate_nodes=nodes,
        existing_predicates=predicates,
    )

    # Step 5: Resolve the subject to an exact canonical label when the
    # extraction selected one of the supplied candidates. Similarity alone
    # never causes a merge; an unknown LLM label is treated as a new node.
    original_subject = extracted.subject
    canonical_subject, grounding_result = _ground_subject(
        original_subject,
        nodes,
    )
    extracted.subject = canonical_subject

    logger.info(
        "Subject grounding result: '%s' -> '%s' (%s)",
        original_subject,
        canonical_subject,
        grounding_result,
    )

    # Step 6: Construct the memory using the canonical subject label.
    candidate = Memory(
        subject=canonical_subject,
        predicate=extracted.predicate,
        object_value=extracted.object_value,
        context=extracted.context,
        source_id="user_input",
        confidence=extracted.confidence,
        valid_from=extracted.valid_from,
        valid_to=extracted.valid_to,
    )

    # Step 7: Run the existing memory comparison and resolution pipeline.
    result = process_memory(
        db=db,
        candidate=candidate,
        top_k=top_k,
        source_text=user_input,
    )

    return {
        "extraction": extracted,
        **result,
    }
