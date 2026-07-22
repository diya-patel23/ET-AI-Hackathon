from collections import Counter
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db import get_db
from app.models import Document, Entity, MaintenanceEvent
from app.schemas import DashboardStats
from app.agents.maintenance_agent import compute_risk

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db)):
    total_documents = db.execute(select(func.count(Document.id))).scalar_one()

    equipment_entities = db.execute(
        select(Entity).where(Entity.entity_type == "Equipment")
    ).scalars().all()
    total_equipment = len(equipment_entities)

    total_incidents = db.execute(
        select(func.count(MaintenanceEvent.id)).where(MaintenanceEvent.event_type == "failure")
    ).scalar_one()

    high_risk_count = 0
    for eq in equipment_entities:
        risk = compute_risk(db, eq.id)
        if risk["risk_level"] == "High":
            high_risk_count += 1

    docs = db.execute(select(Document.doc_category)).scalars().all()
    docs_by_category = dict(Counter(d or "uncategorized" for d in docs))

    # failure trend: failures per month over the last 12 months
    one_year_ago = date.today() - timedelta(days=365)
    failure_events = db.execute(
        select(MaintenanceEvent.event_date).where(
            MaintenanceEvent.event_type == "failure",
            MaintenanceEvent.event_date >= one_year_ago,
        )
    ).scalars().all()
    month_counts = Counter(d.strftime("%Y-%m") for d in failure_events)
    failure_trend = [{"month": k, "failures": v} for k, v in sorted(month_counts.items())]

    return {
        "total_documents": total_documents,
        "total_equipment": total_equipment,
        "total_incidents": total_incidents,
        "open_high_risk_equipment": high_risk_count,
        "compliance_score_avg": 0.0,  # populated once compliance checks have been run on ingested inspections
        "docs_by_category": docs_by_category,
        "failure_trend": failure_trend,
    }
