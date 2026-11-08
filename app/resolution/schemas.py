from enum import Enum
from pydantic import BaseModel, Field
from app.models.memory import MemoryStatus



class MemoryRelationship(str, Enum):
    DUPLICATE = "DUPLICATE"
    SUPERSEDE = "SUPERSEDE"
    COEXIST = "COEXIST"
    CONFLICT = "CONFLICT"
    UNRELATED = "UNRELATED"


class MemoryComparison(BaseModel):
    memory_id: str
    relationship: MemoryRelationship
    reason: str


class ComparisonResult(BaseModel):
    comparisons: list[MemoryComparison] = Field(default_factory=list)


class MemoryStatusUpdate(BaseModel):
    memory_id: str
    status: MemoryStatus


class ResolutionPlan(BaseModel):
    should_insert: bool
    candidate_status: MemoryStatus | None = None
    updates: list[MemoryStatusUpdate] = Field(default_factory=list)