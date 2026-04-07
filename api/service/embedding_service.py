# api/service/embedding_service.py
"""
Embedding service using SentenceTransformers (BAAI/bge-base-en-v1.5).
Output dimension: 768 — update VectorField(dimensions=768) in models.py.
"""

# Move these together at the top
import logging
import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# Token is read from environment, never hardcoded
HF_TOKEN = os.getenv("HF_TOKEN")


logger = logging.getLogger(__name__)

# Load model once at module level (reused across all requests)
try:
    import transformers
    transformers.logging.set_verbosity_error()
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer("BAAI/bge-base-en-v1.5", token=HF_TOKEN)
except Exception as exc:
    _model = None
    logger.error("Failed to load SentenceTransformer model: %s", exc)


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate a 768-dimension embedding vector for the given text.
    Returns None on failure so callers handle it gracefully.
    """
    if _model is None:
        logger.warning("Embedding model not loaded; skipping embedding.")
        return None

    if not text or not text.strip():
        return None

    try:
        vector = _model.encode(text.strip(), normalize_embeddings=True)
        return vector.tolist()
    except Exception as exc:
        logger.warning("Embedding generation failed: %s", exc)
        return None


# ── Semantic search helpers (pgvector cosine distance) ──────────────────────

def semantic_search_physical_books(query: str, top_k: int = 5):
    from api.models import PhysicalBook
    from pgvector.django import CosineDistance

    query_vector = generate_embedding(query)
    if query_vector is None:
        return PhysicalBook.objects.none()

    return (
        PhysicalBook.objects
        .exclude(embedding=None)
        .annotate(similarity=CosineDistance("embedding", query_vector))
        .order_by("similarity")
        [:top_k]
    )


def semantic_search_digital_resources(query: str, top_k: int = 5):
    from api.models import DigitalResource
    from pgvector.django import CosineDistance

    query_vector = generate_embedding(query)
    if query_vector is None:
        return DigitalResource.objects.none()

    return (
        DigitalResource.objects
        .exclude(embedding=None)
        .annotate(similarity=CosineDistance("embedding", query_vector))
        .order_by("similarity")
        [:top_k]
    )


def semantic_search_research(query: str, top_k: int = 5):
    from api.models import ResearchRepository
    from pgvector.django import CosineDistance

    query_vector = generate_embedding(query)
    if query_vector is None:
        return ResearchRepository.objects.none()

    return (
        ResearchRepository.objects
        .exclude(embedding=None)
        .annotate(similarity=CosineDistance("embedding", query_vector))
        .order_by("similarity")
        [:top_k]
    )