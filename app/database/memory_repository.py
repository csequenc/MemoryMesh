from datetime import timezone

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.memory import Memory, MemoryStatus
from app.database.memory_model import MemoryModel
from app.resolution.schemas import ResolutionPlan


def normalize_label(value: str) -> str:
    return " ".join(value.split()).casefold()


def to_utc(value):
    """SQLite may return a naive datetime; interpret it as UTC."""
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def to_pydantic(record: MemoryModel) -> Memory:
    return Memory(
        memory_id=record.memory_id,
        subject=record.subject,
        predicate=record.predicate,
        object_value=record.object_value,
        context=record.context,
        source_id=record.source_id,
        confidence=record.confidence,
        status=MemoryStatus(record.status),
        valid_from=to_utc(record.valid_from),
        valid_to=to_utc(record.valid_to),
        recorded_at=to_utc(record.recorded_at)
    )


def create_memory(db: Session, memory: Memory) -> Memory:
    record = MemoryModel(
        memory_id=memory.memory_id,
        subject=memory.subject,
        predicate=memory.predicate,
        object_value=memory.object_value,
        context=memory.context,
        source_id=memory.source_id,
        confidence=memory.confidence,
        status=memory.status.value,
        valid_from=memory.valid_from,
        valid_to=memory.valid_to,
        recorded_at=memory.recorded_at
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return to_pydantic(record)


def get_memory(db: Session, memory_id: str) -> Memory | None:
    record = db.get(MemoryModel, memory_id)

    if record is None:
        return None

    return to_pydantic(record)


def list_memories(
    db: Session,
    status: MemoryStatus | None = None
) -> list[Memory]:

    statement = select(MemoryModel)

    if status is not None:
        statement = statement.where(
            MemoryModel.status == status.value
        )

    records = db.scalars(statement).all()

    return [to_pydantic(record) for record in records]


def update_memory_status(
    db: Session,
    memory_id: str,
    status: MemoryStatus
) -> Memory | None:

    record = db.get(MemoryModel, memory_id)

    if record is None:
        return None

    record.status = status.value

    db.commit()
    db.refresh(record)

    return to_pydantic(record)


def get_all_candidate_memories(db: Session) -> list[Memory]:
    statement = select(MemoryModel).where(
        MemoryModel.status.in_([
            MemoryStatus.ACTIVE.value,
            MemoryStatus.UNRESOLVED.value
        ])
    )

    records = db.scalars(statement).all()

    return [to_pydantic(record) for record in records]


def delete_memories_for_entity(
    db: Session,
    node_id: str
) -> int:
    """
    Permanently delete every memory connected to a graph entity.

    The graph node ID has the format:
        entity:<normalized entity label>

    A memory is connected when the entity appears as either
    its subject or object_value.
    """

    if not node_id.startswith("entity:"):
        raise ValueError("Invalid graph node ID.")

    entity_label = node_id[len("entity:"):]

    if not entity_label:
        raise ValueError("Entity label cannot be empty.")

    normalized_entity = normalize_label(entity_label)

    records = db.scalars(
        select(MemoryModel)
    ).all()

    connected_records = [
        record
        for record in records
        if (
            normalize_label(record.subject) == normalized_entity
            or
            normalize_label(record.object_value) == normalized_entity
        )
    ]

    if not connected_records:
        return 0

    try:
        for record in connected_records:
            db.delete(record)

        db.commit()

        return len(connected_records)

    except Exception:
        db.rollback()
        raise
    
def delete_memory(
    db: Session,
    memory_id: str
) -> bool:
    """Permanently delete exactly one memory by its ID."""

    record = db.get(MemoryModel, memory_id)

    if record is None:
        return False

    try:
        db.delete(record)
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise


def apply_resolution(
    db: Session,
    candidate: Memory,
    plan: ResolutionPlan
) -> Memory | None:

    # No insertion needed (duplicate found)
    if not plan.should_insert:
        return None

    try:
        if plan.candidate_status is None:
            raise ValueError("Candidate status is required for insertion.")

        if plan.candidate_status not in (
            MemoryStatus.ACTIVE,
            MemoryStatus.UNRESOLVED
        ):
            raise ValueError("Invalid candidate status in resolution plan.")

        candidate.status = plan.candidate_status

        update_ids = [update.memory_id for update in plan.updates]

        if candidate.memory_id in update_ids:
            raise ValueError("Candidate cannot update itself.")

        if len(update_ids) != len(set(update_ids)):
            raise ValueError("Duplicate memory IDs in resolution plan.")

        for update in plan.updates:
            if update.status not in (
                MemoryStatus.SUPERSEDED,
                MemoryStatus.UNRESOLVED
            ):
                raise ValueError("Invalid status update in resolution plan.")

        # Apply individual updates to existing memories.
        for update in plan.updates:

            record = db.get(MemoryModel, update.memory_id)

            if record is None:
                raise ValueError(
                    f"Memory {update.memory_id} does not exist."
                )

            record.status = update.status.value

        # Create the new memory.
        new_record = MemoryModel(
            memory_id=candidate.memory_id,
            subject=candidate.subject,
            predicate=candidate.predicate,
            object_value=candidate.object_value,
            context=candidate.context,
            source_id=candidate.source_id,
            confidence=candidate.confidence,
            status=candidate.status.value,
            valid_from=candidate.valid_from,
            valid_to=candidate.valid_to,
            recorded_at=candidate.recorded_at
        )

        db.add(new_record)

        # Commit everything together.
        db.commit()
        db.refresh(new_record)

        return to_pydantic(new_record)

    except Exception:
        db.rollback()
        raise
    
def update_memory_fields(
    db: Session,
    memory_id: str,
    updates: dict
) -> Memory | None:
    """Update only the permitted editable fields of a memory."""

    allowed_fields = {
        "subject",
        "predicate",
        "object_value",
        "context",
        "valid_from",
        "valid_to",
    }

    if not updates:
        raise ValueError("No fields provided for update.")

    invalid_fields = set(updates) - allowed_fields

    if invalid_fields:
        raise ValueError(
            f"Fields cannot be edited: {', '.join(sorted(invalid_fields))}"
        )

    record = db.get(MemoryModel, memory_id)

    if record is None:
        return None

    try:
        for field, value in updates.items():
            setattr(record, field, value)

        db.commit()
        db.refresh(record)

        return to_pydantic(record)

    except Exception:
        db.rollback()
        raise