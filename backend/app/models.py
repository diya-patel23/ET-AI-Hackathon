import uuid
from datetime import datetime, date

from sqlalchemy import String, Text, Float, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    filename: Mapped[str] = mapped_column(String)
    file_type: Mapped[str] = mapped_column(String)          # pdf, docx, xlsx, csv, image, txt
    upload_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    plant: Mapped[str | None] = mapped_column(String, nullable=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    engineer: Mapped[str | None] = mapped_column(String, nullable=True)
    doc_category: Mapped[str | None] = mapped_column(String, nullable=True)  # maintenance_log, inspection, manual, safety, email
    risk_level: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String, nullable=True)

    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"))
    chunk_index: Mapped[int] = mapped_column()
    text: Mapped[str] = mapped_column(Text)
    vector_id: Mapped[str] = mapped_column(String)  # id used to look this chunk up in the vector store

    document: Mapped["Document"] = relationship(back_populates="chunks")


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String, index=True)
    entity_type: Mapped[str] = mapped_column(String)  # Equipment, Part, Plant, Department, Engineer, Incident, FailureCode, Standard
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    source_entity_id: Mapped[str] = mapped_column(String, ForeignKey("entities.id"))
    target_entity_id: Mapped[str] = mapped_column(String, ForeignKey("entities.id"))
    relation_type: Mapped[str] = mapped_column(String)  # uses, located_in, maintained_by, failed_because, part_of, governed_by, preceded_by
    source_document_id: Mapped[str | None] = mapped_column(String, ForeignKey("documents.id"), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)


class MaintenanceEvent(Base):
    __tablename__ = "maintenance_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    equipment_id: Mapped[str] = mapped_column(String, ForeignKey("entities.id"))
    event_date: Mapped[date] = mapped_column(Date)
    event_type: Mapped[str] = mapped_column(String)  # inspection, repair, failure, replacement
    description: Mapped[str] = mapped_column(Text)
    downtime_hours: Mapped[float] = mapped_column(Float, default=0.0)
    failure_code: Mapped[str | None] = mapped_column(String, nullable=True)
    source_document_id: Mapped[str | None] = mapped_column(String, ForeignKey("documents.id"), nullable=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)  # Engineer, MaintenanceManager, SafetyOfficer, PlantManager, Admin
