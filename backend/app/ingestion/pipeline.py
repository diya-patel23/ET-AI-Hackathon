import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import DOCS_DIR
from app.models import Document, Chunk
from app.ingestion.detect import detect_file_type
from app.ingestion.parsers import parse_document
from app.ingestion.ocr import ocr_image
from app.ingestion.chunker import chunk_text
from app.ingestion.entity_extractor import extract_entities_and_relations
from app.vectorstore import chroma_client
from app.graph import store as graph_store
from app.llm_client import llm_available


def ingest_file(
    db: Session,
    source_path: str,
    original_filename: str,
    plant: str | None = None,
    department: str | None = None,
    engineer: str | None = None,
    doc_category: str | None = None,
    risk_level: str | None = None,
) -> Document:
    file_type = detect_file_type(original_filename)

    # persist a copy of the original under our managed docs directory
    dest = Path(DOCS_DIR) / f"{Path(source_path).stem}_{Path(original_filename).name}"
    if str(Path(source_path).resolve()) != str(dest.resolve()):
        shutil.copyfile(source_path, dest)

    # extract text
    if file_type == "image":
        raw_text = ocr_image(str(dest))
    else:
        raw_text = parse_document(str(dest), file_type)

    document = Document(
        filename=original_filename,
        file_type=file_type,
        plant=plant,
        department=department,
        engineer=engineer,
        doc_category=doc_category,
        risk_level=risk_level,
        raw_text=raw_text,
        storage_path=str(dest),
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    if not raw_text:
        return document  # nothing further to index, but the document record exists

    # chunk + embed + store in vector db
    chunks = chunk_text(raw_text)
    vector_ids = [f"{document.id}::{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "document_id": document.id,
            "filename": original_filename,
            "chunk_index": i,
            "plant": plant or "",
            "doc_category": doc_category or "",
        }
        for i in range(len(chunks))
    ]
    chroma_client.add_chunks(vector_ids, chunks, metadatas)

    for i, (c, vid) in enumerate(zip(chunks, vector_ids)):
        db.add(Chunk(document_id=document.id, chunk_index=i, text=c, vector_id=vid))
    db.commit()

    # entity extraction + knowledge graph update (LLM enrichment only if configured)
    extraction = extract_entities_and_relations(raw_text, use_llm_enrichment=llm_available())
    graph_store.ingest_extraction(db, extraction, document.id)

    return document
