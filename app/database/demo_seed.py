"""Populate a new public demo database with fictional sample memories."""

from datetime import datetime, timezone
from uuid import uuid4

from app.database.demo_connection import DemoSessionLocal
from app.database.memory_model import MemoryModel


DEMO_MEMORIES = [
    {
        "subject": "Ava Chen",
        "predicate": "works_at",
        "object_value": "Northstar Labs",
    },
    {
        "subject": "Marcus Lee",
        "predicate": "works_at",
        "object_value": "Northstar Labs",
    },
    {
        "subject": "Ava Chen",
        "predicate": "manages",
        "object_value": "Project Atlas",
    },
    {
        "subject": "Marcus Lee",
        "predicate": "develops",
        "object_value": "Project Atlas",
    },
    {
        "subject": "Project Atlas",
        "predicate": "is_a_product_of",
        "object_value": "Northstar Labs",
    },
    {
        "subject": "Project Atlas",
        "predicate": "uses",
        "object_value": "Python",
    },
    {
        "subject": "Project Atlas",
        "predicate": "uses",
        "object_value": "PostgreSQL",
    },
    {
        "subject": "Northstar Labs",
        "predicate": "builds",
        "object_value": "AI research software",
    },
    {
        "subject": "Ava Chen",
        "predicate": "collaborates_with",
        "object_value": "Marcus Lee",
    },
    {
        "subject": "Project Atlas",
        "predicate": "uses",
        "object_value": "semantic search",
    },
]


def seed_demo_data() -> int:
    """Seed only an empty demo database; never overwrite visitor changes."""
    with DemoSessionLocal() as db:
        existing_count = db.query(MemoryModel).count()

        if existing_count:
            return 0

        recorded_at = datetime.now(timezone.utc)
        records = [
            MemoryModel(
                memory_id=str(uuid4()),
                subject=item["subject"],
                predicate=item["predicate"],
                object_value=item["object_value"],
                context=None,
                source_id="demo_seed",
                confidence=1.0,
                status="ACTIVE",
                valid_from=None,
                valid_to=None,
                recorded_at=recorded_at,
            )
            for item in DEMO_MEMORIES
        ]

        db.add_all(records)
        db.commit()
        return len(records)
