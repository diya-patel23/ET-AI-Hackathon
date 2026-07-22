import math
import re
from sqlalchemy.orm import Session

from app.vectorstore import chroma_client
from app.llm_client import call_llm, llm_available
from app.graph.store import search_entities
from app.ingestion.entity_extractor import extract_from_text

SYSTEM_PROMPT = (
    "You are an industrial operations copilot. Answer the engineer's question using ONLY the "
    "provided document excerpts. Rules you must follow:\n"
    "1. Use ONLY facts explicitly stated in the excerpts — do not infer, speculate, or guess.\n"
    "2. If the excerpts do not contain the answer, say exactly: "
    "'The available documents do not contain information about [topic]. "
    "Try uploading relevant records for that equipment.' — then STOP. Do not suggest possible causes.\n"
    "3. Reference specific equipment IDs, dates, and source documents in your answer.\n"
    "4. Keep the answer concise — a few sentences to a short paragraph."
)

# Equipment ID pattern — e.g. P204, C602, T710, M410, B501, V220
_EQUIP_RE = re.compile(r'\b([A-Z]\d{3,4})\b')


def _extract_equipment_ids(text: str) -> set[str]:
    """Pull equipment IDs like P204, C602 from a query string."""
    return set(_EQUIP_RE.findall(text.upper()))


def answer_query(db: Session, query: str, history: list[dict] | None = None) -> dict:
    results = chroma_client.query(query, n_results=10)

    docs = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0] if results.get("distances") else []

    if not docs:
        return {
            "answer": "No ingested documents matched this question yet. Try uploading relevant "
                      "maintenance logs, inspection reports, or manuals first.",
            "citations": [],
            "confidence": 0.0,
            "related_entities": [],
        }

    # Re-rank: chunks whose filename/text mentions a queried equipment ID float to top.
    # This ensures "Why did P204 fail?" always surfaces P204 documents even when
    # generic pump-related chunks score slightly higher by vector distance alone.
    queried_equip = _extract_equipment_ids(query)
    if queried_equip:
        def _rank_key(item):
            _, text, meta, dist = item
            fname = (meta.get("filename") or "").upper()
            # Boost: -1 if any queried equipment ID appears in filename or text
            boost = -1 if any(eq in fname or eq in text.upper() for eq in queried_equip) else 0
            return (boost, dist)
        ranked = sorted(zip(range(len(docs)), docs, metadatas, distances), key=_rank_key)
        _, docs, metadatas, distances = zip(*ranked) if ranked else ([], [], [], [])
        docs, metadatas, distances = list(docs), list(metadatas), list(distances)

    # Use top 6 chunks so the prompt stays focused
    docs, metadatas, distances = docs[:6], metadatas[:6], distances[:6]

    context_blocks = []
    citations = []
    for i, (doc_text, meta) in enumerate(zip(docs, metadatas)):
        context_blocks.append(f"[Source {i+1}: {meta.get('filename')}]\n{doc_text}")
        citations.append({
            "document_id": meta.get("document_id"),
            "filename": meta.get("filename"),
            "snippet": doc_text[:280],
        })

    context = "\n\n".join(context_blocks)
    prompt = f"QUESTION: {query}\n\nDOCUMENT EXCERPTS:\n{context}\n\nAnswer the question using the excerpts above."
    answer = call_llm(SYSTEM_PROMPT, prompt, max_tokens=600)

    # Confidence from vector distances.
    #
    # ChromaDB returns L2 (squared Euclidean) distances by default. These are
    # unbounded positive numbers — NOT in [0, 1] — so the old "1.0 - avg_dist"
    # formula always returned 0% whenever distances exceeded 1.0 (which is the
    # norm with real embedding models including sentence-transformers + Ollama).
    #
    # Fix: exponential decay  conf = exp(-best_dist)
    #   dist = 0.0  →  conf = 1.00  (perfect / duplicate match)
    #   dist = 0.5  →  conf = 0.61  (very relevant)
    #   dist = 1.0  →  conf = 0.37  (relevant)
    #   dist = 2.0  →  conf = 0.14  (loosely related)
    #   dist → ∞    →  conf → 0.00  (no match)
    #
    # We use the best (minimum) distance so one highly-relevant chunk produces
    # a meaningful score even if the other retrieved chunks are less relevant.
    if distances:
        best_dist = min(distances)
        confidence = math.exp(-best_dist)
        confidence = max(0.0, min(1.0, confidence))
    else:
        confidence = 0.5

    if not llm_available():
        confidence = min(confidence, 0.4)  # answer is unsynthesized without LLM

    # related entities: pull any known entities mentioned across the retrieved chunks
    related_names = set()
    for doc_text in docs:
        extraction = extract_from_text(doc_text)
        for e in extraction["entities"]:
            related_names.add(e["name"])

    return {
        "answer": answer,
        "citations": citations,
        "confidence": round(confidence, 2),
        "related_entities": sorted(related_names)[:10],
    }
