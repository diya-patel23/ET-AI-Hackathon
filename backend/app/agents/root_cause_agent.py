from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import MaintenanceEvent, Document
from app.graph.store import get_entity_by_name, get_entity_neighbors
from app.vectorstore import chroma_client
from app.llm_client import call_llm_json, call_llm, llm_available

SYSTEM_PROMPT = (
    "You are a root cause analysis engine for industrial equipment failures. Given a timeline of "
    "maintenance events and supporting document excerpts, construct an explainable causal chain "
    "from the earliest contributing factor to the final failure/shutdown. "
    'Respond as JSON: {"chain": [{"stage": str, "evidence": str, "source_number": int|null}], '
    '"summary": str, "confidence": number between 0 and 1}. '
    "source_number refers to the numbered SOURCES list you were given. Only use evidence that is "
    "actually present in the sources — do not invent maintenance history."
)


def analyze(db: Session, equipment_name: str | None, failure_description: str | None) -> dict:
    entity = get_entity_by_name(db, equipment_name) if equipment_name else None

    events: list[MaintenanceEvent] = []
    if entity:
        events = list(db.execute(
            select(MaintenanceEvent).where(MaintenanceEvent.equipment_id == entity.id)
            .order_by(MaintenanceEvent.event_date)
        ).scalars().all())

    search_text = equipment_name or failure_description or ""
    vector_results = chroma_client.query(search_text, n_results=5) if search_text else {}
    doc_chunks = vector_results.get("documents", [[]])[0] if vector_results else []
    doc_metas = vector_results.get("metadatas", [[]])[0] if vector_results else []

    # build a numbered source list combining structured events and unstructured chunks
    sources = []
    for ev in events:
        doc = db.get(Document, ev.source_document_id) if ev.source_document_id else None
        sources.append({
            "label": f"Maintenance event {ev.event_date}: {ev.event_type} — {ev.description}",
            "document_id": ev.source_document_id,
            "filename": doc.filename if doc else None,
        })
    for text, meta in zip(doc_chunks, doc_metas):
        sources.append({
            "label": text[:400],
            "document_id": meta.get("document_id"),
            "filename": meta.get("filename"),
        })

    if not sources:
        return {
            "equipment_name": equipment_name,
            "chain": [],
            "summary": "No maintenance history or related documents found for this equipment yet. "
                       "Ingest maintenance logs or inspection reports that mention it first.",
            "confidence": 0.0,
        }

    if llm_available():
        numbered = "\n".join(f"[{i+1}] {s['label']}" for i, s in enumerate(sources))
        prompt = (
            f"EQUIPMENT: {equipment_name or 'unspecified'}\n"
            f"FAILURE DESCRIPTION (if provided): {failure_description or 'n/a'}\n\n"
            f"SOURCES:\n{numbered}\n\n"
            "Build the causal chain."
        )
        result = call_llm_json(SYSTEM_PROMPT, prompt, max_tokens=1000)
    else:
        result = None

    if result and isinstance(result, dict) and result.get("chain"):
        chain = []
        for stage in result["chain"]:
            src_num = stage.get("source_number")
            src = sources[src_num - 1] if src_num and 0 < src_num <= len(sources) else None
            chain.append({
                "stage": stage.get("stage", ""),
                "evidence": stage.get("evidence", ""),
                "source_document_id": src["document_id"] if src else None,
                "source_filename": src["filename"] if src else None,
            })
        return {
            "equipment_name": equipment_name,
            "chain": chain,
            "summary": result.get("summary", ""),
            "confidence": float(result.get("confidence", 0.5)),
        }

    # rule-based fallback: chronological maintenance events as the chain, no LLM narrative
    chain = [
        {
            "stage": ev.event_type,
            "evidence": ev.description,
            "source_document_id": ev.source_document_id,
            "source_filename": db.get(Document, ev.source_document_id).filename if ev.source_document_id else None,
        }
        for ev in events
    ]
    return {
        "equipment_name": equipment_name,
        "chain": chain,
        "summary": call_llm(
            "Summarize this maintenance timeline in 2-3 sentences, plainly, without inventing details.",
            "\n".join(s["label"] for s in sources),
        ) if chain else "No structured maintenance timeline available; see related documents instead.",
        "confidence": 0.4 if chain else 0.2,
    }
