from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    RootCauseRequest, RootCauseResponse,
    MaintenanceRequest, MaintenanceResponse,
    ComplianceRequest, ComplianceResponse,
)
from app.agents import root_cause_agent, maintenance_agent, compliance_agent

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("/root-cause", response_model=RootCauseResponse)
def root_cause(req: RootCauseRequest, db: Session = Depends(get_db)):
    result = root_cause_agent.analyze(db, req.equipment_name, req.failure_description)
    return result


@router.post("/maintenance", response_model=MaintenanceResponse)
def maintenance(req: MaintenanceRequest, db: Session = Depends(get_db)):
    result = maintenance_agent.assess(db, req.equipment_name)
    return result


@router.post("/compliance", response_model=ComplianceResponse)
def compliance(req: ComplianceRequest, db: Session = Depends(get_db)):
    result = compliance_agent.check_document(db, req.document_id)
    return result
