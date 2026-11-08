from app.models.memory import MemoryStatus
from app.resolution.schemas import (
    ComparisonResult,
    MemoryRelationship,
    MemoryStatusUpdate,
    ResolutionPlan
)


def resolve_comparisons(
    result: ComparisonResult
) -> ResolutionPlan:

    relationships = [
        comparison.relationship
        for comparison in result.comparisons
    ]

    if MemoryRelationship.DUPLICATE in relationships:
        return ResolutionPlan(should_insert=False)

    updates = []

    for comparison in result.comparisons:

        if comparison.relationship == MemoryRelationship.SUPERSEDE:
            updates.append(
                MemoryStatusUpdate(
                    memory_id=comparison.memory_id,
                    status=MemoryStatus.SUPERSEDED
                )
            )

        elif comparison.relationship == MemoryRelationship.CONFLICT:
            updates.append(
                MemoryStatusUpdate(
                    memory_id=comparison.memory_id,
                    status=MemoryStatus.UNRESOLVED
                )
            )

    candidate_status = (
        MemoryStatus.UNRESOLVED
        if MemoryRelationship.CONFLICT in relationships
        else MemoryStatus.ACTIVE
    )

    return ResolutionPlan(
        should_insert=True,
        candidate_status=candidate_status,
        updates=updates
    )