
from app.models.memory import Memory


def normalize_label(value: str) -> str:
    """Create a consistent key for identifying graph nodes."""
    return " ".join(value.split()).casefold()


def build_graph_data(memories: list[Memory]) -> dict:
    nodes = {}
    edges = []

    for memory in memories:
        subject_id = f"entity:{normalize_label(memory.subject)}"
        object_id = f"entity:{normalize_label(memory.object_value)}"

        # Create subject node if it doesn't already exist.
        if subject_id not in nodes:
            nodes[subject_id] = {
                "data": {
                    "id": subject_id,
                    "label": memory.subject,
                    "type": "entity"
                }
            }

        # Create object node if it doesn't already exist.
        if object_id not in nodes:
            nodes[object_id] = {
                "data": {
                    "id": object_id,
                    "label": memory.object_value,
                    "type": "entity"
                }
            }

        # Every memory becomes a separate edge.
        edges.append({
            "data": {
                "id": f"memory:{memory.memory_id}",
                "source": subject_id,
                "target": object_id,
                "label": memory.predicate,

                "memory_id": memory.memory_id,
                "subject": memory.subject,
                "predicate": memory.predicate,
                "object_value": memory.object_value,

                "context": memory.context,
                "status": memory.status.value,
                "confidence": memory.confidence,
                "source_id": memory.source_id,

                "recorded_at": (
                    memory.recorded_at.isoformat()
                    if memory.recorded_at else None
                ),
                "valid_from": (
                    memory.valid_from.isoformat()
                    if memory.valid_from else None
                ),
                "valid_to": (
                    memory.valid_to.isoformat()
                    if memory.valid_to else None
                )
            }
        })

    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }
