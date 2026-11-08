from app.models.memory import MemoryStatus
from app.resolution.schemas import (
    ComparisonResult,
    MemoryComparison,
    MemoryRelationship
)
from app.resolution.resolver import resolve_comparisons


result = ComparisonResult(
    comparisons=[
        MemoryComparison(
            memory_id="memory_1",
            relationship=MemoryRelationship.SUPERSEDE,
            reason="The new memory replaces the old value."
        ),
        MemoryComparison(
            memory_id="memory_2",
            relationship=MemoryRelationship.CONFLICT,
            reason="The values contradict each other."
        ),
        MemoryComparison(
            memory_id="memory_3",
            relationship=MemoryRelationship.COEXIST,
            reason="Both memories can be true."
        )
    ]
)

plan = resolve_comparisons(result)

print(plan)

assert plan.should_insert is True
assert plan.candidate_status == MemoryStatus.UNRESOLVED

assert len(plan.updates) == 2

updates = {
    update.memory_id: update.status
    for update in plan.updates
}

assert updates["memory_1"] == MemoryStatus.SUPERSEDED
assert updates["memory_2"] == MemoryStatus.UNRESOLVED
assert "memory_3" not in updates

print("All resolver tests passed!")

duplicate_result = ComparisonResult(
    comparisons=[
        MemoryComparison(
            memory_id="memory_1",
            relationship=MemoryRelationship.SUPERSEDE,
            reason="The new memory replaces the old value."
        ),
        MemoryComparison(
            memory_id="memory_2",
            relationship=MemoryRelationship.DUPLICATE,
            reason="The information already exists."
        ),
        MemoryComparison(
            memory_id="memory_3",
            relationship=MemoryRelationship.CONFLICT,
            reason="The values contradict each other."
        )
    ]
)

duplicate_plan = resolve_comparisons(duplicate_result)

print(duplicate_plan)

assert duplicate_plan.should_insert is False
assert duplicate_plan.candidate_status is None
assert duplicate_plan.updates == []

print("Duplicate short-circuit test passed!")