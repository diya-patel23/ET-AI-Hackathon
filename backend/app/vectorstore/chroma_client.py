"""
Thin wrapper around ChromaDB. Embeddings are computed ourselves via
app.ingestion.embedder (so the sentence-transformers/TF-IDF fallback logic is
in one place) and passed in explicitly, rather than letting Chroma manage its
own embedding function.
"""
import chromadb
from app.config import CHROMA_DIR
from app.ingestion.embedder import embed_texts

_client = None
_collection = None

COLLECTION_NAME = "industrial_chunks"


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_or_create_collection(name=COLLECTION_NAME)
    return _collection


def add_chunks(vector_ids: list[str], texts: list[str], metadatas: list[dict]) -> None:
    if not texts:
        return
    embeddings = embed_texts(texts)
    col = _get_collection()
    col.add(ids=vector_ids, embeddings=embeddings, documents=texts, metadatas=metadatas)


def query(text: str, n_results: int = 5, where: dict | None = None) -> dict:
    col = _get_collection()
    embedding = embed_texts([text])[0]
    return col.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where=where,
    )


def delete_by_document(document_id: str) -> None:
    col = _get_collection()
    col.delete(where={"document_id": document_id})


def count() -> int:
    return _get_collection().count()
