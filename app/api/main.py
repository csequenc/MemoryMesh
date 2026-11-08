from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.database.connection import SessionLocal
from app.database.memory_repository import (
    list_memories,
    get_all_candidate_memories,
    delete_memories_for_entity,
    delete_memory,
    update_memory_fields,
)
from app.graph.graph_builder import build_graph_data
from app.models.memory import MemoryStatus
from app.retrieval.semantic_search import retrieve_for_query
from app.query.answer import generate_answer
from app.ingestion.memory_pipeline import process_user_input


app = FastAPI(
    title="MemoryMesh API",
    description="API for the MemoryMesh memory engine",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class DeleteNodeRequest(BaseModel):
    node_id: str = Field(min_length=1)
    
class DeleteEdgeRequest(BaseModel):
    memory_id: str = Field(min_length=1)
    
class MemoryUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str | None = None
    predicate: str | None = None
    object_value: str | None = None
    context: str | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None

    @field_validator("subject", "predicate", "object_value")
    @classmethod
    def validate_required_text(cls, value):
        if value is not None and not value.strip():
            raise ValueError("This field cannot be empty.")

        return value.strip() if value is not None else value


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def serialize_memory(memory):
    if memory is None:
        return None

    return {
        "memory_id": memory.memory_id,
        "subject": memory.subject,
        "predicate": memory.predicate,
        "object_value": memory.object_value,
        "context": memory.context,
        "status": memory.status.value,
        "confidence": memory.confidence,
    }


@app.get("/")
def root():
    return {
        "message": "MemoryMesh API is running"
    }


@app.get("/api/graph")
def get_graph(db: Session = Depends(get_db)):
    memories = list_memories(db)
    graph = build_graph_data(memories)

    return graph

@app.get("/api/memories")
def get_all_memories(db: Session = Depends(get_db)):
    memories = list_memories(db)

    return [
        {
            "memory_id": memory.memory_id,
            "subject": memory.subject,
            "predicate": memory.predicate,
            "object_value": memory.object_value,
            "context": memory.context,
            "source_id": memory.source_id,
            "status": memory.status.value,
            "confidence": memory.confidence,
            "valid_from": (
                memory.valid_from.isoformat()
                if memory.valid_from else None
            ),
            "valid_to": (
                memory.valid_to.isoformat()
                if memory.valid_to else None
            ),
            "recorded_at": (
                memory.recorded_at.isoformat()
                if memory.recorded_at else None
            ),
        }
        for memory in memories
    ]


@app.patch("/api/memories/{memory_id}")
def edit_memory(
    memory_id: str,
    request: MemoryUpdateRequest,
    db: Session = Depends(get_db)
):
    try:
        updated_memory = update_memory_fields(
            db=db,
            memory_id=memory_id,
            updates=request.model_dump(exclude_unset=True)
        )

        if updated_memory is None:
            raise HTTPException(
                status_code=404,
                detail="Memory not found."
            )

        return {
            "success": True,
            "memory": serialize_memory(updated_memory),
            "valid_from": (
                updated_memory.valid_from.isoformat()
                if updated_memory.valid_from else None
            ),
            "valid_to": (
                updated_memory.valid_to.isoformat()
                if updated_memory.valid_to else None
            ),
            "recorded_at": (
                updated_memory.recorded_at.isoformat()
                if updated_memory.recorded_at else None
            ),
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

@app.delete("/api/graph/node")
def delete_graph_node(
    request: DeleteNodeRequest,
    db: Session = Depends(get_db)
):
    try:
        deleted_count = delete_memories_for_entity(
            db=db,
            node_id=request.node_id
        )

        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="No connected memories found for this entity."
            )

        return {
            "success": True,
            "deleted_memories": deleted_count,
            "node_id": request.node_id
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
        
@app.delete("/api/graph/edge")
def delete_graph_edge(
    request: DeleteEdgeRequest,
    db: Session = Depends(get_db)
):
    try:
        deleted = delete_memory(db, request.memory_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Relationship not found."
            )

        return {
            "success": True,
            "deleted_memory_id": request.memory_id
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/api/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    # Explicit command for adding information to memory.
    remember_command = "/remember"

    if (
        message == remember_command
        or message.startswith(remember_command + " ")
        or message.startswith(remember_command + "\n")
    ):
        memory_input = message[len(remember_command):].strip()

        if not memory_input:
            raise HTTPException(
                status_code=400,
                detail="Please provide information after /remember."
            )

        result = process_user_input(
            db=db,
            user_input=memory_input
        )

        plan = result["plan"]
        saved_memory = result["saved_memory"]

        # Duplicate: candidate was not inserted.
        if not plan.should_insert:

            duplicate = next(
                (
                    comparison
                    for comparison in result["comparisons"].comparisons
                    if comparison.relationship.value == "DUPLICATE"
                ),
                None
            )

            reason = (
                duplicate.reason
                if duplicate
                else "An identical memory already exists."
            )

            return {
                "type": "memory",
                "action": "DUPLICATE",
                "status": "DUPLICATE",
                "answer": (
                    "I didn't save a new memory because "
                    f"{reason}"
                ),
                "sources": [],
                "memory": None,
                "updated_memories": []
            }

        status = plan.candidate_status.value

        updated_memories = [
            {
                "memory_id": update.memory_id,
                "status": update.status.value
            }
            for update in plan.updates
        ]

        if status == "UNRESOLVED":
            action = "ADDED_UNRESOLVED"

            answer = (
                "I saved this memory, but marked it UNRESOLVED "
                "because it conflicts with existing information:\n\n"
                f"{saved_memory.subject} → "
                f"{saved_memory.predicate} → "
                f"{saved_memory.object_value}"
            )

        else:
            action = "ADDED"

            answer = (
                f"Memory saved successfully:\n\n"
                f"{saved_memory.subject} → "
                f"{saved_memory.predicate} → "
                f"{saved_memory.object_value}"
            )

            superseded_count = sum(
                1 for update in plan.updates
                if update.status == MemoryStatus.SUPERSEDED
            )

            unresolved_count = sum(
                1 for update in plan.updates
                if update.status == MemoryStatus.UNRESOLVED
            )

            if superseded_count:
                answer += (
                    f"\n\nUpdated {superseded_count} "
                    "existing memory/memories to SUPERSEDED."
                )

            if unresolved_count:
                answer += (
                    f"\n\nMarked {unresolved_count} "
                    "existing memory/memories as UNRESOLVED."
                )

        return {
            "type": "memory",
            "action": action,
            "status": status,
            "answer": answer,
            "sources": [],
            "memory": serialize_memory(saved_memory),
            "updated_memories": updated_memories
        }

    # Normal messages use the existing question-answering pipeline.
    memories = get_all_candidate_memories(db)

    active_memories = [
        memory for memory in memories
        if memory.status == MemoryStatus.ACTIVE
    ]

    retrieved = retrieve_for_query(
        query=message,
        existing_memories=active_memories,
        top_k=5
    )

    retrieved_memories = [
        memory for memory, score in retrieved
    ]

    result = generate_answer(
        query=message,
        retrieved_memories=retrieved_memories
    )

    retrieved_scores = {
        memory.memory_id: score
        for memory, score in retrieved
    }

    memory_lookup = {
        memory.memory_id: memory
        for memory in retrieved_memories
    }

    sources = []

    for memory_id in result["source_memories"]:
        memory = memory_lookup.get(memory_id)

        if memory is None:
            continue

        sources.append({
            "memory_id": memory.memory_id,
            "subject": memory.subject,
            "predicate": memory.predicate,
            "object_value": memory.object_value,
            "context": memory.context,
            "status": memory.status.value,
            "similarity": round(
                retrieved_scores[memory_id], 4
            )
        })

    return {
        "type": "answer",
        "answer": result["answer"],
        "sources": sources
    }