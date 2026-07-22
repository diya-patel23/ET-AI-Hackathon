"""
Thin compliance agent (Tier 2 per the architecture doc): a small, hardcoded
rule set rather than a general regulation-ingestion engine. Each rule is a
(pattern check + LLM judgment) pair so it still degrades gracefully without
an API key — the regex check runs either way, the LLM adds nuance on top.
"""
import re
from sqlalchemy.orm import Session

from app.models import Document
from app.llm_client import call_llm_json, llm_available

RULES = [
    {
        "rule": "Inspection date is documented",
        "standard": "Internal SOP",
        "check": lambda text: bool(re.search(r"\b(inspection date|inspected on|date of inspection)\b", text, re.I)),
    },
    {
        "rule": "Inspector/engineer is named",
        "standard": "Internal SOP",
        "check": lambda text: bool(re.search(r"\b(inspected by|engineer|technician)\s*:", text, re.I)),
    },
    {
        "rule": "PPE requirement is documented",
        "standard": "OSHA 1910.132",
        "check": lambda text: bool(re.search(r"\b(PPE|personal protective equipment)\b", text, re.I)),
    },
    {
        "rule": "No overdue certification mentioned",
        "standard": "ISO 55001",
        "check": lambda text: not bool(re.search(r"\b(certification expired|certificate expired|overdue certification)\b", text, re.I)),
    },
    {
        "rule": "Pressure/safety limits referenced where relevant",
        "standard": "OSHA 1910.169",
        "check": lambda text: True if not re.search(r"\bpressure\b", text, re.I) else bool(re.search(r"\b(psi|bar|kPa)\b", text, re.I)),
    },
]

LLM_SYSTEM = (
    "You are a compliance auditor for industrial inspection reports. For the given rule and "
    "document excerpt, decide if the document passes. Respond as JSON: "
    '{"passed": true|false, "explanation": str (1 sentence)}. Be conservative — if the excerpt '
    "doesn't clearly address the rule, say passed=false and explain what's missing."
)


def check_document(db: Session, document_id: str) -> dict:
    document = db.get(Document, document_id)
    if not document:
        return {"document_id": document_id, "filename": "", "results": [], "compliance_score": 0.0}

    text = document.raw_text or ""
    results = []
    for r in RULES:
        regex_pass = r["check"](text)
        explanation = "Pattern check " + ("passed." if regex_pass else "did not find required content.")
        passed = regex_pass

        if llm_available():
            llm_result = call_llm_json(
                LLM_SYSTEM,
                f"RULE: {r['rule']} (standard: {r['standard']})\n\nDOCUMENT EXCERPT:\n{text[:3000]}",
                max_tokens=200,
            )
            if llm_result and isinstance(llm_result, dict) and "passed" in llm_result:
                passed = bool(llm_result["passed"])
                explanation = llm_result.get("explanation", explanation)

        results.append({
            "rule": r["rule"],
            "standard": r["standard"],
            "passed": passed,
            "explanation": explanation,
        })

    score = round(100 * sum(1 for r in results if r["passed"]) / len(results), 1) if results else 0.0

    return {
        "document_id": document_id,
        "filename": document.filename,
        "results": results,
        "compliance_score": score,
    }
