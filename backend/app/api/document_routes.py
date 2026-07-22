from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.models import Document
from app.schemas import DocumentOut

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    plant: str | None = Query(None),
    doc_category: str | None = Query(None),
    limit: int = Query(100, le=500),
):
    stmt = select(Document)
    if plant:
        stmt = stmt.where(Document.plant == plant)
    if doc_category:
        stmt = stmt.where(Document.doc_category == doc_category)
    stmt = stmt.order_by(Document.upload_date.desc()).limit(limit)
    return db.execute(stmt).scalars().all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{document_id}/text")
def get_document_text(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"document_id": document_id, "raw_text": doc.raw_text}
