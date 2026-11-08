
import json
from pydantic import BaseModel
from app.llm.client import create_chat_completion
from app.models.memory import Memory, MemoryStatus


class AnswerResult(BaseModel):
    answer: str
    relevant_memory_ids: list[str]


def generate_answer(
    query: str,
    retrieved_memories: list[Memory]
) -> dict:
    
    # Never use superseded memories
    retrieved_memories = [
        memory for memory in retrieved_memories
        if memory.status != MemoryStatus.SUPERSEDED
    ]

    if not retrieved_memories:
        return {
            "answer": "I don't have enough information in my memory to answer that.",
            "source_memories": []
        }

    memory_data = [
        {
            "memory_id": memory.memory_id,
            "subject": memory.subject,
            "predicate": memory.predicate,
            "object_value": memory.object_value,
            "context": memory.context,
            "status": memory.status.value
        }
        for memory in retrieved_memories
    ]

    messages = [
        {
            "role": "system",
            "content": """
You are the answer generation engine for MemoryMesh.

Your task is to determine which supplied memories are
relevant to the user's question and then answer it.

Rules for relevance:
- A memory is relevant only if it contains information
  that helps answer the specific question.
- Consider the subject, predicate, object_value and context.
- Do not treat memories as relevant merely because they
  belong to the same project.
- Distinguish between different kinds of information.
  For example, a database is not an LLM provider or
  a vector search engine.
- Respect project and scope boundaries.
- Return only IDs of memories that genuinely help
  answer the question.

Rules for answering:
- Use ONLY relevant memories.
- Never invent or assume information.
- Do not use external knowledge.
- If no relevant memories exist, say you don't have
  enough information.
- Never use SUPERSEDED memories as current facts.
- If relevant memories have UNRESOLVED status,
  communicate uncertainty clearly.
- Do not hide contradictions between relevant memories.
- Keep answers concise and direct.

Return valid structured output.
"""
        },
        {
            "role": "user",
            "content": f"""
User question:
{query}

Retrieved memories:
{json.dumps(memory_data, indent=2)}
"""
        }
    ]

    response = create_chat_completion(
        model="openai/gpt-oss-20b",
        messages=messages,
        temperature=0,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "answer_result",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "answer": {
                            "type": "string"
                        },
                        "relevant_memory_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": [
                        "answer",
                        "relevant_memory_ids"
                    ],
                    "additionalProperties": False
                }
            }
        }
    )

    raw_result = response.choices[0].message.content

    parsed_result = AnswerResult.model_validate_json(raw_result)

    # Only allow IDs that were actually retrieved.
    retrieved_ids = {
        memory.memory_id for memory in retrieved_memories
    }

    valid_ids = [
        memory_id
        for memory_id in parsed_result.relevant_memory_ids
        if memory_id in retrieved_ids
    ]

    return {
        "answer": parsed_result.answer,
        "source_memories": valid_ids
    }
