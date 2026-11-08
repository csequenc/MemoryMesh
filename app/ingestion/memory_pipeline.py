
from sqlalchemy.orm import Session

from app.models.memory import Memory

from app.database.memory_repository import (
    get_all_candidate_memories,
    apply_resolution
)

from app.retrieval.semantic_search import retrieve_candidates

from app.resolution.comparison import compare_memories
from app.resolution.resolver import resolve_comparisons

from app.ingestion.extraction import extract_memory


def process_memory(
    db: Session,
    candidate: Memory,
    top_k: int = 5,
    source_text: str | None = None
):

    # Step 1: Get active and unresolved memories
    existing_memories = get_all_candidate_memories(db)

    # Step 2: Retrieve semantically relevant memories
    retrieved = retrieve_candidates(
        candidate=candidate,
        existing_memories=existing_memories,
        top_k=top_k
    )

    retrieved_memories = [
        memory for memory, score in retrieved
    ]

    # Step 3: Compare candidate against retrieved memories
    comparison_result = compare_memories(
        candidate=candidate,
        retrieved_memories=retrieved_memories,
        source_text=source_text
    )

    # Step 4: Generate resolution plan
    plan = resolve_comparisons(comparison_result)

    # Step 5: Apply plan to SQLite
    saved_memory = apply_resolution(
        db=db,
        candidate=candidate,
        plan=plan
    )

    return {
        "comparisons": comparison_result,
        "plan": plan,
        "saved_memory": saved_memory
    }


def process_user_input(
    db: Session,
    user_input: str,
    top_k: int = 5
):

    # Step 1: Extract structured information
    extracted = extract_memory(user_input)

    # Step 2: Construct Memory object
    candidate = Memory(
        subject=extracted.subject,
        predicate=extracted.predicate,
        object_value=extracted.object_value,
        context=extracted.context,
        source_id="user_input",
        confidence=extracted.confidence,
        valid_from=extracted.valid_from,
        valid_to=extracted.valid_to
    )

    # Step 3: Process the extracted memory
    result = process_memory(
        db=db,
        candidate=candidate,
        top_k=top_k,
        source_text=user_input
    )

    return {
        "extraction": extracted,
        **result
    }
