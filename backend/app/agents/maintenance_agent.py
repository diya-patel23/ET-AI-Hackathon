from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import MaintenanceEvent
from app.graph.store import get_entity_by_name
from app.llm_client import call_llm

SYSTEM_PROMPT = (
    "You are a maintenance planning assistant. Given an equipment risk score and its maintenance "
    "history, write a short (2-4 sentence), plain-language recommendation for a maintenance manager. "
    "Be concrete about what to check and roughly when. Do not invent specific numbers not given to you."
)


def _risk_level(score: float) -> str:
    if score >= 0.7:
        return "High"
    if score >= 0.4:
        return "Medium"
    return "Low"


def compute_risk(db: Session, entity_id: str) -> dict:
    """No-LLM risk computation. Cheap enough to call for every piece of
    equipment (used by the dashboard's fleet-wide stats), unlike `assess`
    which also generates an LLM narrative."""
    events = list(db.execute(
        select(MaintenanceEvent).where(MaintenanceEvent.equipment_id == entity_id)
        .order_by(MaintenanceEvent.event_date.desc())
    ).scalars().all())

    today = date.today()
    last_event = events[0] if events else None
    days_since = (today - last_event.event_date).days if last_event else None

    one_year_ago = today - timedelta(days=365)
    failures_last_year = [e for e in events if e.event_type == "failure" and e.event_date >= one_year_ago]

    last_failure_severity = 0.0
    for e in events:
        if e.event_type == "failure":
            last_failure_severity = min(1.0, (e.downtime_hours or 0) / 48.0)  # 48h downtime ~ max severity
            break

    # simple, explainable, defensible scoring — explicitly NOT presented as a trained ML model.
    recency_component = min(1.0, (days_since or 400) / 365) if days_since is not None else 0.6
    frequency_component = min(1.0, len(failures_last_year) / 3)
    severity_component = last_failure_severity

    risk_score = round(0.4 * recency_component + 0.35 * frequency_component + 0.25 * severity_component, 2)
    risk_level = _risk_level(risk_score)

    recommended_next_date = None
    if last_event:
        interval_days = 90 if risk_level == "High" else 180 if risk_level == "Medium" else 365
        recommended_next_date = last_event.event_date + timedelta(days=interval_days)

    return {
        "events": events,
        "days_since": days_since,
        "failures_last_year": failures_last_year,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "recommended_next_date": recommended_next_date,
    }


def assess(db: Session, equipment_name: str) -> dict:
    entity = get_entity_by_name(db, equipment_name)
    if not entity:
        return {
            "equipment_name": equipment_name,
            "risk_score": 0.0,
            "risk_level": "Unknown",
            "days_since_last_maintenance": None,
            "failure_count_last_year": 0,
            "recommendation": "No records found for this equipment. Ingest maintenance logs that "
                               "reference it, or check the spelling of the equipment name.",
            "recommended_next_date": None,
        }

    computed = compute_risk(db, entity.id)
    events = computed["events"]
    days_since = computed["days_since"]
    failures_last_year = computed["failures_last_year"]
    risk_score = computed["risk_score"]
    risk_level = computed["risk_level"]
    recommended_next_date = computed["recommended_next_date"]

    history_summary = "\n".join(
        f"- {e.event_date} | {e.event_type} | {e.description} | downtime={e.downtime_hours}h"
        for e in events[:10]
    ) or "No maintenance history recorded."

    prompt = (
        f"Equipment: {equipment_name}\n"
        f"Risk score: {risk_score} ({risk_level})\n"
        f"Days since last maintenance event: {days_since}\n"
        f"Failures in last 12 months: {len(failures_last_year)}\n"
        f"Recent history:\n{history_summary}\n\n"
        "Write the recommendation."
    )
    recommendation = call_llm(SYSTEM_PROMPT, prompt, max_tokens=300)

    return {
        "equipment_name": equipment_name,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "days_since_last_maintenance": days_since,
        "failure_count_last_year": len(failures_last_year),
        "recommendation": recommendation,
        "recommended_next_date": recommended_next_date,
    }
