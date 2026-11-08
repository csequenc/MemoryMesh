from sqlalchemy import inspect, text

from app.database.connection import engine


inspector = inspect(engine)

columns = [
    column["name"]
    for column in inspector.get_columns("memories")
]

if "context" not in columns:
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE memories ADD COLUMN context VARCHAR")
        )

    print("Context column added successfully!")

else:
    print("Context column already exists.")