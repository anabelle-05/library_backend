# api/service/embedding_service.py
"""
Embedding service using SentenceTransformers (BAAI/bge-base-en-v1.5).
Output dimension: 768 — update VectorField(dimensions=768) in models.py.
"""

import logging
import os
from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")
EMBEDDINGS_ENABLED = os.getenv("EMBEDDINGS_ENABLED", "false").lower() == "true"
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load the embedding model only when first needed.
    This prevents heavy imports during Django startup.
    """
    if not EMBEDDINGS_ENABLED:
        logger.warning("Embeddings are disabled.")
        return None

    try:
        import transformers
        transformers.logging.set_verbosity_error()

        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", EMBEDDING_MODEL_NAME)
        model = SentenceTransformer(EMBEDDING_MODEL_NAME, token=HF_TOKEN)
        logger.info("Embedding model loaded successfully")
        return model
    except Exception as exc:
        logger.exception("Failed to load SentenceTransformer model: %s", exc)
        return None


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate a 768-dimension embedding vector for the given text.
    Returns None on failure so callers handle it gracefully.
    """
    if not text or not text.strip():
        return None

    model = get_embedding_model()
    if model is None:
        logger.warning("Embedding model not loaded; skipping embedding.")
        return None

    try:
        vector = model.encode(
            text.strip(),
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return vector.tolist()
    except Exception as exc:
        logger.warning("Embedding generation failed: %s", exc)
        return None


def _semantic_search(model_class, query: str, top_k: int = 5):
    from pgvector.django import CosineDistance

    query_vector = generate_embedding(query)
    if query_vector is None:
        return model_class.objects.none()

    return (
        model_class.objects
        .exclude(embedding=None)
        .annotate(similarity=CosineDistance("embedding", query_vector))
        .order_by("similarity")[:top_k]
    )


def semantic_search_physical_books(query: str, top_k: int = 5):
    from api.models import PhysicalBook
    return _semantic_search(PhysicalBook, query, top_k)


def semantic_search_digital_resources(query: str, top_k: int = 5):
    from api.models import DigitalResource
    return _semantic_search(DigitalResource, query, top_k)


def semantic_search_research(query: str, top_k: int = 5):
    from api.models import ResearchRepository
    return _semantic_search(ResearchRepository, query, top_k)