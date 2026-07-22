from datetime import datetime, date
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    filename: str
    file_type: str
    upload_date: datetime
    plant: str | None = None
    department: str | None = None
    engineer: str | None = None
    doc_category: str | None = None
    risk_level: str | None = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    query: str
    history: list[dict] = []


class Citation(BaseModel):
    document_id: str
    filename: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float
    related_entities: list[str]


class EntityOut(BaseModel):
    id: str
    name: str
    entity_type: str
    attributes: dict

    class Config:
        from_attributes = True


class RelationshipOut(BaseModel):
    id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    confidence: float

    class Config:
        from_attributes = True


class EntityGraph(BaseModel):
    entity: EntityOut
    relationships: list[RelationshipOut]
    neighbors: list[EntityOut]


class RootCauseRequest(BaseModel):
    equipment_name: str | None = None
    failure_description: str | None = None


class RootCauseStage(BaseModel):
    stage: str
    evidence: str
    source_document_id: str | None = None
    source_filename: str | None = None


class RootCauseResponse(BaseModel):
    equipment_name: str | None
    chain: list[RootCauseStage]
    summary: str
    confidence: float


class MaintenanceRequest(BaseModel):
    equipment_name: str


class MaintenanceResponse(BaseModel):
    equipment_name: str
    risk_score: float
    risk_level: str
    days_since_last_maintenance: int | None
    failure_count_last_year: int
    recommendation: str
    recommended_next_date: date | None


class ComplianceRequest(BaseModel):
    document_id: str


class ComplianceRuleResult(BaseModel):
    rule: str
    standard: str
    passed: bool
    explanation: str


class ComplianceResponse(BaseModel):
    document_id: str
    filename: str
    results: list[ComplianceRuleResult]
    compliance_score: float


class DashboardStats(BaseModel):
    total_documents: int
    total_equipment: int
    total_incidents: int
    open_high_risk_equipment: int
    compliance_score_avg: float
    docs_by_category: dict[str, int]
    failure_trend: list[dict]
