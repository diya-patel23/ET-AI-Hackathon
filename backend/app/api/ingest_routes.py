import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.ingestion.pipeline import ingest_file
from app.schemas import DocumentOut
from app.config import MAX_UPLOAD_MB

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


@router.post("", response_model=DocumentOut)
async def ingest(
    file: UploadFile = File(...),
    plant: str | None = Form(None),
    department: str | None = Form(None),
    engineer: str | None = Form(None),
    doc_category: str | None = Form(None),
    risk_level: str | None = Form(None),
    db: Session = Depends(get_db),
):
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_UPLOAD_MB}MB limit")

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        document = ingest_file(
            db,
            source_path=tmp_path,
            original_filename=file.filename,
            plant=plant,
            department=department,
            engineer=engineer,
            doc_category=doc_category,
            risk_level=risk_level,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return document
