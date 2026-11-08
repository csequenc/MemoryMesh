from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


class MemoryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    UNRESOLVED = "UNRESOLVED"
    REJECTED = "REJECTED"


class Memory(BaseModel):

    memory_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )

    subject: str
    predicate: str
    object_value: str
    
    context: Optional[str] = None

    source_id: str
    confidence: float = Field(ge=0, le=1)

    status: MemoryStatus = MemoryStatus.ACTIVE

    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None

    recorded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    

    
