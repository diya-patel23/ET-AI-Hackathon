"""
Builds the knowledge graph's raw material: (entity, entity, relation_type) triples.

Two passes, and the app is fully useful after just the first one:

1. Rule-based co-occurrence extraction (regex). Deterministic, needs no LLM,
   runs on every document. This is what makes the demo work even with zero
   API key configured — this alone is enough to populate a real graph across
   your seeded documents, because industrial documents follow predictable
   conventions (equipment codes, "Engineer: <name>", "Plant <n>", etc).

2. Optional LLM enrichment pass (only runs if an API key is configured) that
   reads the same chunk and can surface relationships the regexes miss, e.g.
   implicit causal language ("the pump seized after the seal failed").

Entity vocabulary and relation types match the schema documented in the
architecture doc: Equipment, Part, Plant, Department, Engineer, Incident,
FailureCode, Standard / uses, located_in, maintained_by, failed_because,
part_of, governed_by, preceded_by.
"""
import re
from app.llm_client import call_llm_json, llm_available

EQUIPMENT_RE = re.compile(r"\b(Pump|Compressor|Motor|Turbine|Boiler|Conveyor|Generator|Valve|Fan|Heat Exchanger)\s+([A-Z]{1,3}\d{2,4})\b")
PART_RE = re.compile(r"\b(Bearing|Seal|Gasket|Impeller|Rotor|Filter|Belt|Coupling|Shaft)\s+([A-Z]?\d{1,4})\b")
PLANT_RE = re.compile(r"\bPlant\s+(\d{1,2}|[A-Z])\b")
DEPT_RE = re.compile(r"\bDepartment:\s*([A-Za-z &/]+)", re.IGNORECASE)
ENGINEER_RE = re.compile(r"\b(?:Engineer|Technician|Inspected by|Performed by)\s*:[ \t]*([A-Za-z.]+(?:[ \t]+[A-Za-z.]+){0,3})", re.IGNORECASE)
FAILURE_CODE_RE = re.compile(r"\bFC-\d{2,5}\b")
STANDARD_RE = re.compile(r"\b(OSHA(?:\s\d{4}(?:\.\d+)?)?|ISO\s?\d{4,5}|API\s?\d{3,4})\b")


def _clean(name: str) -> str:
    return " ".join(name.split()).strip().rstrip(".,;")


def extract_from_text(text: str) -> dict:
    """Rule-based pass. Returns {entities: [{name, entity_type}], relations: [{source, source_type, target, target_type, relation_type}]}"""
    equipment = {f"{m.group(1)} {m.group(2)}" for m in EQUIPMENT_RE.finditer(text)}
    parts = {f"{m.group(1)} {m.group(2)}" for m in PART_RE.finditer(text)}
    plants = {f"Plant {m.group(1)}" for m in PLANT_RE.finditer(text)}
    departments = {_clean(m.group(1)) for m in DEPT_RE.finditer(text)}
    engineers = {_clean(m.group(1)) for m in ENGINEER_RE.finditer(text)}
    failure_codes = {m.group(0) for m in FAILURE_CODE_RE.finditer(text)}
    standards = {m.group(0) for m in STANDARD_RE.finditer(text)}

    entities = []
    for n in equipment:
        entities.append({"name": n, "entity_type": "Equipment"})
    for n in parts:
        entities.append({"name": n, "entity_type": "Part"})
    for n in plants:
        entities.append({"name": n, "entity_type": "Plant"})
    for n in departments:
        entities.append({"name": n, "entity_type": "Department"})
    for n in engineers:
        entities.append({"name": n, "entity_type": "Engineer"})
    for n in failure_codes:
        entities.append({"name": n, "entity_type": "FailureCode"})
    for n in standards:
        entities.append({"name": n, "entity_type": "Standard"})

    relations = []
    for eq in equipment:
        for p in parts:
            relations.append({"source": eq, "source_type": "Equipment", "target": p, "target_type": "Part", "relation_type": "uses"})
        for pl in plants:
            relations.append({"source": eq, "source_type": "Equipment", "target": pl, "target_type": "Plant", "relation_type": "located_in"})
        for eng in engineers:
            relations.append({"source": eq, "source_type": "Equipment", "target": eng, "target_type": "Engineer", "relation_type": "maintained_by"})
        for fc in failure_codes:
            relations.append({"source": eq, "source_type": "Equipment", "target": fc, "target_type": "FailureCode", "relation_type": "failed_because"})
        for st in standards:
            relations.append({"source": eq, "source_type": "Equipment", "target": st, "target_type": "Standard", "relation_type": "governed_by"})

    return {"entities": entities, "relations": relations}


LLM_ENRICH_SYSTEM = (
    "You extract structured relationships from industrial maintenance and safety documents. "
    "Only extract entities/relations that are explicitly supported by the text. "
    "Allowed entity_type values: Equipment, Part, Plant, Department, Engineer, Incident, FailureCode, Standard. "
    "Allowed relation_type values: uses, located_in, maintained_by, failed_because, part_of, governed_by, preceded_by."
)


def enrich_with_llm(text: str) -> dict:
    """Optional second pass. Returns the same shape as extract_from_text, or
    an empty result if no LLM is configured or parsing fails."""
    if not llm_available():
        return {"entities": [], "relations": []}
    prompt = (
        "Extract additional entities and relationships from this industrial document excerpt "
        "that a simple regex pass would miss (e.g. implicit causal chains). "
        'Return JSON: {"entities": [{"name": str, "entity_type": str}], '
        '"relations": [{"source": str, "source_type": str, "target": str, "target_type": str, "relation_type": str}]}\n\n'
        f"TEXT:\n{text[:3000]}"
    )
    result = call_llm_json(LLM_ENRICH_SYSTEM, prompt, max_tokens=800)
    if not result or not isinstance(result, dict):
        return {"entities": [], "relations": []}
    return {
        "entities": result.get("entities", []) or [],
        "relations": result.get("relations", []) or [],
    }


def extract_entities_and_relations(text: str, use_llm_enrichment: bool = False) -> dict:
    base = extract_from_text(text)
    if use_llm_enrichment:
        extra = enrich_with_llm(text)
        base["entities"].extend(extra["entities"])
        base["relations"].extend(extra["relations"])
    return base
