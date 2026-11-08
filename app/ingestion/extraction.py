
import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.llm.client import create_chat_completion


class MemoryExtraction(BaseModel):
    subject: str
    predicate: str
    object_value: str
    context: Optional[str] = None
    confidence: float = Field(ge=0, le=1)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


def extract_memory(user_input: str) -> MemoryExtraction:

    messages = [
        {
            "role": "system",
            "content": """

You are a structured memory extraction engine.

Extract ONE intended information unit from the user's input.

Return these fields:

1. subject:
   Identify the actual entity or component being described.

   IMPORTANT — Preserve the actual entity in possessive
   and ownership-based statements.

   When a statement describes a property, attribute,
   or relationship belonging to a named entity, that
   named entity must remain the subject.

   Examples:

   "Jagriti's class is CSE-19"
   subject: Jagriti
   predicate: currently_in_class
   object_value: CSE-19

   "Jagriti's class changed to CSE-11"
   subject: Jagriti
   predicate: currently_in_class
   object_value: CSE-11

   "Rahul's birthday is 12th March"
   subject: Rahul
   predicate: birthday
   object_value: 12th March

   "My laptop uses an NVIDIA GPU"
   subject: laptop
   predicate: uses_gpu
   object_value: NVIDIA GPU

   Do NOT turn the property being described into the
   subject. For example, do not extract "class" as the
   subject from "Jagriti's class changed to CSE-11".

   If the input describes a component belonging to a project,
   use the component as subject and the project as context.

   If the input describes the project itself, keep the
   complete project name as the subject.

   Do not include environment labels such as production,
   development, or testing in the subject when they describe
   the environment in which a component operates.
   Represent them in context instead.

   Examples:

   "MemoryMesh backend uses Python 3.12"
   subject: backend
   context: MemoryMesh project

   "My RAG project uses FAISS"
   subject: RAG project
   context: null

   "The production backend uses Python 3.15"
   subject: backend
   context: production environment

   "The development backend uses Python 3.13"
   subject: backend
   context: development environment

2. predicate:
   Represent the underlying relationship or property,
   not the exact wording used by the user.
   Use concise snake_case names.

   Examples:
   - "uses Python" -> uses_language
   - "uses FAISS for vector search" -> uses_vector_search_engine
   - "is an AI memory engine" -> type
   - "class is CSE-19" -> currently_in_class
   - "birthday is 7th June" -> birthday

   When a property changes, preserve the same predicate
   that represents the underlying property.

   For example:
   "Jagriti's class changed to CSE-11"
   must use currently_in_class, NOT changed_to.

3. object_value:
   The actual value or information associated with
   the subject.

4. context:
   Additional information that meaningfully identifies
   the scope of the memory.
   Do not repeat information already represented by subject.
   Return null if no meaningful context is available.

5. confidence:
   Estimate how confidently you extracted the intended
   information and preserved its meaning.

   Use a value between 0 and 1.
   - High: information is explicit and unambiguous.
   - Medium: some interpretation was necessary.
   - Low: the intended information is ambiguous.

   This measures extraction confidence, not source reliability.

6. valid_from:
   Extract the date/time when the fact became true,
   but ONLY when a concrete date or date/time is explicitly
   provided in the user's input.

   Examples:
   - "Switched to Python 3.12 on October 15, 2026"
     -> 2026-10-15T00:00:00Z
   - "Started using Python 3.12 yesterday"
     -> null
   - "Started using Python 3.12 last month"
     -> null

   Do not resolve relative dates using the current date.
   Do not infer dates.
   If only a date is provided, use midnight UTC.

7. valid_to:
   Extract the date/time when the fact stopped being true,
   following exactly the same rules as valid_from.

   Return null if no concrete end date/time is explicitly
   provided.

Rules:
- Represent the resulting factual state, not the action
  used to describe it.
- Different phrasings of the same fact should produce
  consistent subject-predicate-object representations.
- Avoid generic predicates such as "is" or "has"
  when a more meaningful property name is available.
- Do not put redundant information in context.
- Do not invent information or assumptions.
- Prefer concise, clear values.
- Extract only one intended information unit.
- For this version, treat all inputs as established facts,
  including statements about possible future changes.
- Temporal fields must only contain explicitly stated,
  concrete dates or date/times. Never calculate or infer them.

"""
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    response = create_chat_completion(
        model="openai/gpt-oss-20b",
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "memory_extraction",
                "schema": MemoryExtraction.model_json_schema()
            }
        },
        temperature=0
    )

    result = response.choices[0].message.content
    data = json.loads(result)

    for field in ("valid_from", "valid_to", "context"):
        if data.get(field) == "null":
            data[field] = None

    return MemoryExtraction.model_validate(data)
