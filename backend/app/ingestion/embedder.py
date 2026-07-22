"""
Embeddings, with automatic fallback.

Primary: sentence-transformers (all-MiniLM-L6-v2) — real semantic embeddings.
Needs a one-time model download from huggingface.co on first run.

Fallback: scikit-learn's HashingVectorizer — a stateless bag-of-words hash,
zero network access required, works instantly offline. This matters for real
industrial deployments too: many plants run on air-gapped or heavily
restricted networks, so a system that degrades to "still works, just less
semantically smart" instead of "crashes" is a genuine feature, not just a demo
convenience.

Both paths expose the same `embed_texts(list[str]) -> list[list[float]]`
interface, so nothing downstream (vectorstore, RAG copilot) needs to know
which one is active. Whichever backend is picked, it is used consistently for
the life of the process (don't mix vector spaces).
"""
import logging
from app.config import EMBEDDING_BACKEND

logger = logging.getLogger("embedder")

_backend_name = None
_model = None
_hasher = None


def _try_load_sentence_transformers():
    global _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        return True
    except Exception as e:
        logger.warning("sentence-transformers unavailable, falling back to TF-IDF hashing: %s", e)
        return False


def _init():
    global _backend_name, _hasher
    if _backend_name is not None:
        return

    if EMBEDDING_BACKEND in ("auto", "sentence-transformers") and _try_load_sentence_transformers():
        _backend_name = "sentence-transformers"
    else:
        from sklearn.feature_extraction.text import HashingVectorizer
        _hasher = HashingVectorizer(n_features=384, alternate_sign=False, norm="l2")
        _backend_name = "tfidf-hashing"

    logger.info("Embedding backend active: %s", _backend_name)


def embedding_backend_name() -> str:
    _init()
    return _backend_name


def embed_texts(texts: list[str]) -> list[list[float]]:
    _init()
    if not texts:
        return []
    if _backend_name == "sentence-transformers":
        return _model.encode(texts, convert_to_numpy=True).tolist()
    else:
        matrix = _hasher.transform(texts)
        return matrix.toarray().tolist()
