from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.db import get_db
from app.models import Document, Entity
from app.vectorstore import chroma_client

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search(
    q: str = Query(..., min_length=1),
    mode: str = Query("hybrid", pattern="^(semantic|keyword|hybrid)$"),
    db: Session = Depends(get_db),
):
    semantic_results = []
    if mode in ("semantic", "hybrid"):
        raw = chroma_client.query(q, n_results=8)
        docs = raw.get("documents", [[]])[0]
        metas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0] if raw.get("distances") else [None] * len(docs)
        for text, meta, dist in zip(docs, metas, distances):
            semantic_results.append({
                "type": "semantic_chunk",
                "document_id": meta.get("document_id"),
                "filename": meta.get("filename"),
                "snippet": text[:300],
                "score": round(1 - dist, 3) if dist is not None else None,
            })

    keyword_results = []
    entity_results = []
    if mode in ("keyword", "hybrid"):
        like = f"%{q}%"
        docs = db.execute(
            select(Document).where(
                or_(Document.raw_text.ilike(like), Document.filename.ilike(like))
            ).limit(10)
        ).scalars().all()
        for d in docs:
            keyword_results.append({
                "type": "keyword_document",
                "document_id": d.id,
                "filename": d.filename,
                "snippet": (d.raw_text or "")[:300],
            })

        entities = db.execute(
            select(Entity).where(Entity.name.ilike(like)).limit(10)
        ).scalars().all()
        for e in entities:
            entity_results.append({
                "type": "entity",
                "entity_id": e.id,
                "name": e.name,
                "entity_type": e.entity_type,
            })

    return {
        "query": q,
        "mode": mode,
        "semantic_results": semantic_results,
        "keyword_results": keyword_results,
        "entity_results": entity_results,
    }
