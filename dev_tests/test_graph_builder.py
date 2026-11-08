
from app.database.connection import SessionLocal
from app.database.memory_repository import list_memories
from app.graph.graph_builder import build_graph_data

db = SessionLocal()

try:
    memories = list_memories(db)

    graph = build_graph_data(memories)

    print("\nGRAPH SUMMARY")
    print("-" * 40)
    print("Total memories:", len(memories))
    print("Total nodes:", len(graph["nodes"]))
    print("Total edges:", len(graph["edges"]))

    print("\nNODES")
    print("-" * 40)

    for node in graph["nodes"]:
        print(node["data"]["id"], "->", node["data"]["label"])

    print("\nEDGES")
    print("-" * 40)

    for edge in graph["edges"]:
        data = edge["data"]

        print(
            f'{data["subject"]} '
            f'--{data["predicate"]}--> '
            f'{data["object_value"]}'
        )
        print("Status:", data["status"])
        print("Context:", data["context"])
        print("Memory ID:", data["memory_id"])
        print()

finally:
    db.close()
