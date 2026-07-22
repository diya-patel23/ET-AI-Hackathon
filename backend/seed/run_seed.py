"""
Run this once to stand up a fully populated demo:

    cd backend
    python -m seed.run_seed

It generates synthetic documents, ingests every one of them through the exact
same pipeline a real upload uses (so ingestion, chunking, embeddings, and the
knowledge graph are all populated for real), then seeds the structured
maintenance_events table from the generated CSV so the Maintenance
Intelligence and Root Cause Analysis agents have real history to reason over.
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal, init_db
from app.ingestion.pipeline import ingest_file
from app.models import Document, MaintenanceEvent
from app.graph.store import get_entity_by_name
from seed.generate_seed_data import main as generate_docs, OUT_DIR


def ingest_generated_documents(db):
    doc_files = sorted(OUT_DIR.glob("*.txt")) + sorted(OUT_DIR.glob("*.csv"))
    print(f"Ingesting {len(doc_files)} generated documents through the real pipeline...")

    for path in doc_files:
        category = (
            "maintenance_log" if "maintenance_log" in path.name
            else "inspection" if "inspection_report" in path.name
            else "safety" if "safety_manual" in path.name
            else "manual" if "oem_manual" in path.name
            else "maintenance_log" if "maintenance_events" in path.name
            else "general"
        )
        plant = None
        for p in ("Plant 1", "Plant 2", "Plant 3"):
            if p.replace(" ", "").lower() in path.read_text(encoding="utf-8").replace(" ", "").lower()[:400]:
                plant = p
                break

        ingest_file(
            db,
            source_path=str(path),
            original_filename=path.name,
            doc_category=category,
            plant=plant,
        )
    print("Document ingestion complete.")


def seed_structured_events(db):
    csv_path = OUT_DIR / "maintenance_events_master.csv"
    if not csv_path.exists():
        print("No maintenance_events_master.csv found — skipping structured event seeding.")
        return

    filename_to_doc_id = {
        d.filename: d.id for d in db.query(Document).all()
    }

    count = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity = get_entity_by_name(db, row["equipment"])
            if not entity:
                continue  # entity extraction should have created it during ingestion; skip if not found
            source_doc_id = filename_to_doc_id.get(f"maintenance_log_{row['equipment'].split()[-1]}.txt")
            event = MaintenanceEvent(
                equipment_id=entity.id,
                event_date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                event_type=row["event_type"],
                description=row["description"],
                downtime_hours=float(row["downtime_hours"] or 0),
                failure_code=row["failure_code"] or None,
                source_document_id=source_doc_id,
            )
            db.add(event)
            count += 1
    db.commit()
    print(f"Seeded {count} structured maintenance events.")


def main():
    init_db()
    generate_docs()

    db = SessionLocal()
    try:
        ingest_generated_documents(db)
        seed_structured_events(db)
    finally:
        db.close()

    print("\nSeed complete. Start the API with `uvicorn app.main:app --reload` and try:")
    print('  POST /api/chat  {"query": "Why did Pump P204 fail?"}')
    print('  POST /api/agents/root-cause  {"equipment_name": "Pump P204"}')
    print('  POST /api/agents/maintenance  {"equipment_name": "Pump P204"}')


if __name__ == "__main__":
    main()
