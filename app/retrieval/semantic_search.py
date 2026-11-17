import logging
import os
import re
import threading
from difflib import SequenceMatcher

import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

from app.models.memory import Memory, MemoryStatus


logger = logging.getLogger(__name__)

# This repository contains only the quantized ONNX graph and tokenizer for the
# original sentence-transformers/all-MiniLM-L6-v2 model. Pin the revision so a
# future upstream update cannot silently change embeddings.
MODEL_REPO_ID = "monju-lab/all-MiniLM-L6-v2-onnx"
MODEL_REVISION = "4600d32e31da9a0416f247a9de80cf695c56debc"
MODEL_FILENAME = "onnx/model_quint8_avx2.onnx"
TOKENIZER_FILENAME = "tokenizer.json"
MODEL_MAX_LENGTH = 256
MODEL_DIMENSION = 384
ENCODE_BATCH_SIZE = 16


class QuantizedSentenceEncoder:
    """SentenceTransformer-compatible encode wrapper using quantized ONNX.

    It keeps the all-MiniLM-L6-v2 embedding model and its mean-pooling plus
    L2-normalization behavior, without importing PyTorch or Transformers.
    The model is downloaded and initialized only on the first encode call so
    the API can bind its port before the model is loaded.
    """

    def __init__(self):
        self._session = None
        self._tokenizer = None
        self._load_lock = threading.Lock()
        self._tokenizer_lock = threading.Lock()

    def _ensure_loaded(self):
        if self._session is not None and self._tokenizer is not None:
            return

        with self._load_lock:
            if self._session is not None and self._tokenizer is not None:
                return

            logger.info("Preparing quantized all-MiniLM-L6-v2 ONNX model")

            model_path = hf_hub_download(
                repo_id=MODEL_REPO_ID,
                filename=MODEL_FILENAME,
                revision=MODEL_REVISION,
            )
            tokenizer_path = hf_hub_download(
                repo_id=MODEL_REPO_ID,
                filename=TOKENIZER_FILENAME,
                revision=MODEL_REVISION,
            )

            tokenizer = Tokenizer.from_file(tokenizer_path)
            tokenizer.enable_truncation(max_length=MODEL_MAX_LENGTH)
            pad_id = tokenizer.token_to_id("[PAD]")
            tokenizer.enable_padding(
                pad_id=0 if pad_id is None else pad_id,
                pad_token="[PAD]",
            )

            # Limit ONNX Runtime's thread pools and allocator arenas for the
            # 512 MB hosting environment. Sequential CPU inference is enough
            # for this small embedding model and a recruiter demo workload.
            session_options = ort.SessionOptions()
            session_options.intra_op_num_threads = 1
            session_options.inter_op_num_threads = 1
            session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            session_options.graph_optimization_level = (
                ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
            )
            session_options.enable_cpu_mem_arena = False
            session_options.enable_mem_pattern = False

            session = ort.InferenceSession(
                model_path,
                sess_options=session_options,
                providers=["CPUExecutionProvider"],
            )

            self._tokenizer = tokenizer
            self._session = session
            logger.info("Quantized all-MiniLM-L6-v2 ONNX model is ready")

    def encode(
        self,
        sentences,
        normalize_embeddings: bool = False,
        batch_size: int = ENCODE_BATCH_SIZE,
        **_kwargs,
    ):
        """Encode one string or a list of strings into 384-dim embeddings."""
        single_input = isinstance(sentences, str)
        texts = [sentences] if single_input else list(sentences)

        if not texts:
            empty = np.empty((0, MODEL_DIMENSION), dtype=np.float32)
            return empty

        self._ensure_loaded()
        safe_batch_size = max(1, int(batch_size))
        embedding_batches = []

        for start in range(0, len(texts), safe_batch_size):
            batch = [str(text) for text in texts[start:start + safe_batch_size]]

            # Tokenizer configuration is mutable, so serialize encode_batch
            # calls while allowing ONNX inference to remain thread-safe.
            with self._tokenizer_lock:
                encoded = self._tokenizer.encode_batch(batch)

            input_ids = np.asarray(
                [item.ids for item in encoded],
                dtype=np.int64,
            )
            attention_mask = np.asarray(
                [item.attention_mask for item in encoded],
                dtype=np.int64,
            )
            token_type_ids = np.zeros_like(input_ids, dtype=np.int64)

            token_embeddings = self._session.run(
                None,
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "token_type_ids": token_type_ids,
                },
            )[0]

            # SentenceTransformers' all-MiniLM-L6-v2 configuration uses
            # attention-masked mean pooling followed by L2 normalization.
            weights = attention_mask[..., None].astype(np.float32)
            summed = (token_embeddings * weights).sum(axis=1)
            counts = np.clip(weights.sum(axis=1), 1e-9, None)
            pooled = summed / counts

            if normalize_embeddings:
                norms = np.linalg.norm(pooled, axis=1, keepdims=True)
                pooled = pooled / np.clip(norms, 1e-12, None)

            embedding_batches.append(pooled.astype(np.float32, copy=False))

        embeddings = np.concatenate(embedding_batches, axis=0)
        return embeddings[0] if single_input else embeddings


# Preserve the existing model.encode(...) interface used by the ingestion and
# retrieval pipeline. Initialization is lazy; no model is loaded at import time.
model = QuantizedSentenceEncoder()

# Node labels are stable across a process, so cache their normalized embeddings.
# This cache is intentionally in-memory; it does not change the database schema.
_node_embedding_cache: dict[str, np.ndarray] = {}


def memory_to_text(memory):
    parts = [
        memory.subject,
        memory.predicate,
        memory.object_value,
    ]

    if memory.context:
        parts.append(memory.context)

    return " | ".join(parts)


def normalize_node_label(value: str) -> str:
    """Normalize whitespace and case for node-label comparisons."""
    return " ".join(value.split()).casefold()


def _node_labels(existing_memories: list[Memory]):
    """Collect existing subject nodes and up to two example facts per node."""
    nodes: dict[str, dict] = {}

    for memory in existing_memories:
        fact = memory_to_text(memory)

        # Subject grounding only: object_value is intentionally excluded.
        label = " ".join(memory.subject.split())
        key = normalize_node_label(label)

        if not key:
            continue

        if key not in nodes:
            nodes[key] = {
                "label": label,
                "examples": [],
                "connections": 0,
            }

        nodes[key]["connections"] += 1

        if fact not in nodes[key]["examples"] and len(nodes[key]["examples"]) < 2:
            nodes[key]["examples"].append(fact)

    return nodes


def _text_phrases(text: str, max_words: int = 5) -> list[str]:
    words = re.findall(r"[\w]+(?:['’.-][\w]+)*", text.casefold())
    phrases = []

    for size in range(1, min(max_words, len(words)) + 1):
        phrases.extend(
            " ".join(words[index:index + size])
            for index in range(len(words) - size + 1)
        )

    return phrases


def _exact_label_match(label: str, text: str) -> bool:
    # Word boundaries avoid matching e.g. "Ann" inside "Annual".
    pattern = rf"(?<!\w){re.escape(label)}(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def _fuzzy_label_score(label: str, phrases: list[str]) -> float:
    if not phrases:
        return 0.0

    return max(
        SequenceMatcher(None, label.casefold(), phrase).ratio()
        for phrase in phrases
    )


def _get_node_embedding(label: str) -> np.ndarray:
    key = normalize_node_label(label)

    if key not in _node_embedding_cache:
        embedding = model.encode(
            label,
            normalize_embeddings=True
        )
        _node_embedding_cache[key] = np.asarray(embedding, dtype=np.float32)

    return _node_embedding_cache[key]


def candidate_nodes(
    raw_text: str,
    existing_memories: list[Memory],
    k: int = 25,
    min_score: float = 0.45,
    fallback_minimum: int = 5,
) -> list[dict]:
    """Find existing subject nodes that may be referenced by input text.

    Each result contains the canonical stored subject label, up to two example
    facts, a relevance score, and whether it was added by the connectivity
    fallback. Candidate selection is advisory: it does not merge or rename
    graph nodes.
    """
    if k <= 0 or not raw_text.strip() or not existing_memories:
        return []

    nodes = _node_labels(existing_memories)
    if not nodes:
        return []

    text_embedding = np.asarray(
        model.encode(raw_text, normalize_embeddings=True),
        dtype=np.float32
    )
    phrases = _text_phrases(raw_text)

    scored = []
    for key, node in nodes.items():
        label = node["label"]
        exact = _exact_label_match(label, raw_text)
        fuzzy = _fuzzy_label_score(label, phrases)
        embedding = _get_node_embedding(label)
        semantic = float(np.dot(embedding, text_embedding))

        # Exact mention dominates. Otherwise use the strongest of fuzzy and
        # embedding evidence; this only ranks candidates for the LLM.
        score = 1.0 if exact else max(fuzzy, semantic)

        scored.append({
            "label": label,
            "examples": list(node["examples"]),
            "score": float(score),
            "fallback": False,
            "connections": node["connections"],
            "_key": key,
        })

    scored.sort(
        key=lambda item: (item["score"], item["connections"]),
        reverse=True
    )

    selected = [
        item for item in scored
        if item["score"] >= min_score
    ][:k]

    # If text matching found too few plausible nodes, add the most-connected
    # remaining subject nodes as weak context. They are not automatic matches.
    if len(selected) < min(fallback_minimum, k):
        selected_keys = {item["_key"] for item in selected}
        remaining = [
            item for item in scored
            if item["_key"] not in selected_keys
        ]

        remaining.sort(
            key=lambda item: (item["connections"], item["score"]),
            reverse=True
        )

        needed = min(fallback_minimum, k) - len(selected)

        for item in remaining[:needed]:
            fallback_item = dict(item)
            fallback_item["fallback"] = True
            selected.append(fallback_item)

    return [
        {
            "label": item["label"],
            "examples": item["examples"][:2],
            "score": item["score"],
            "fallback": item["fallback"],
        }
        for item in selected[:k]
    ]


def retrieve_candidates(
    candidate,
    existing_memories,
    top_k=5
):
    existing_memories = [
        memory for memory in existing_memories
        if memory.status.value in ("ACTIVE", "UNRESOLVED")
    ]

    if not existing_memories:
        return []

    candidate_text = memory_to_text(candidate)

    existing_texts = [
        memory_to_text(memory)
        for memory in existing_memories
    ]

    embeddings = model.encode(
        [candidate_text] + existing_texts,
        normalize_embeddings=True
    )

    candidate_embedding = embeddings[0]
    existing_embeddings = embeddings[1:]

    scores = existing_embeddings @ candidate_embedding

    ranked = sorted(
        zip(existing_memories, scores),
        key=lambda item: item[1],
        reverse=True
    )

    return [
        (memory, float(score))
        for memory, score in ranked[:top_k]
    ]


def retrieve_for_query(
    query: str,
    existing_memories: list[Memory],
    top_k: int = 5
):
    """Retrieve memories relevant to a natural-language query."""

    # Only retrieve current or unresolved memories
    eligible_memories = [
        memory for memory in existing_memories
        if memory.status in (
            MemoryStatus.ACTIVE,
            MemoryStatus.UNRESOLVED
        )
    ]

    if not eligible_memories:
        return []

    # Convert memories into searchable text
    memory_texts = [
        memory_to_text(memory)
        for memory in eligible_memories
    ]

    # Generate embeddings
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    memory_embeddings = model.encode(
        memory_texts,
        normalize_embeddings=True
    )

    # Calculate cosine similarity
    scores = memory_embeddings @ query_embedding

    # Rank memories by similarity
    ranked_indices = scores.argsort()[::-1][:top_k]

    results = [
        (eligible_memories[index], float(scores[index]))
        for index in ranked_indices
    ]

    # Remove low-relevance results
    results = [
        (memory, score)
        for memory, score in results
        if score >= 0.30
    ]

    return results
