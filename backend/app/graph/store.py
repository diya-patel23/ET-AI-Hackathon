"""
Knowledge graph store. Implemented as entity/relationship tables in the same
SQLite/Postgres database rather than a separate Neo4j instance — see the
architecture doc for why this is the right tradeoff for a one-week build.

The entity/relation vocabulary is deliberately identical to what a Neo4j
schema would use (see entity_extractor.py), so upgrading later is a matter of
writing Cypher CREATE statements from these same rows, not a redesign.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.models import Entity, Relationship


def get_or_create_entity(db: Session, name: str, entity_type: str) -> Entity:
    existing = db.execute(
        select(Entity).where(Entity.name == name, Entity.entity_type == entity_type)
    ).scalar_one_or_none()
    if existing:
        return existing
    entity = Entity(name=name, entity_type=entity_type, attributes={})
    db.add(entity)
    db.flush()
    return entity


def upsert_relationship(db: Session, source: Entity, target: Entity, relation_type: str,
                         source_document_id: str | None, confidence: float = 1.0) -> Relationship:
    existing = db.execute(
        select(Relationship).where(
            Relationship.source_entity_id == source.id,
            Relationship.target_entity_id == target.id,
            Relationship.relation_type == relation_type,
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    rel = Relationship(
        source_entity_id=source.id,
        target_entity_id=target.id,
        relation_type=relation_type,
        source_document_id=source_document_id,
        confidence=confidence,
    )
    db.add(rel)
    db.flush()
    return rel


def ingest_extraction(db: Session, extraction: dict, document_id: str) -> None:
    """Takes the output of entity_extractor.extract_entities_and_relations and
    writes it into the graph tables."""
    name_type_to_entity: dict[tuple[str, str], Entity] = {}

    for e in extraction.get("entities", []):
        name, etype = e.get("name"), e.get("entity_type")
        if not name or not etype:
            continue
        ent = get_or_create_entity(db, name, etype)
        name_type_to_entity[(name, etype)] = ent

    for r in extraction.get("relations", []):
        s_name, s_type = r.get("source"), r.get("source_type")
        t_name, t_type = r.get("target"), r.get("target_type")
        rel_type = r.get("relation_type")
        if not all([s_name, s_type, t_name, t_type, rel_type]):
            continue
        source = name_type_to_entity.get((s_name, s_type)) or get_or_create_entity(db, s_name, s_type)
        target = name_type_to_entity.get((t_name, t_type)) or get_or_create_entity(db, t_name, t_type)
        upsert_relationship(db, source, target, rel_type, document_id)

    db.commit()


def get_entity_by_name(db: Session, name: str) -> Entity | None:
    return db.execute(
        select(Entity).where(Entity.name.ilike(f"%{name}%"))
    ).scalars().first()


def get_entity_neighbors(db: Session, entity_id: str) -> tuple[list[Relationship], list[Entity]]:
    rels = db.execute(
        select(Relationship).where(
            or_(Relationship.source_entity_id == entity_id, Relationship.target_entity_id == entity_id)
        )
    ).scalars().all()
    neighbor_ids = set()
    for r in rels:
        neighbor_ids.add(r.source_entity_id)
        neighbor_ids.add(r.target_entity_id)
    neighbor_ids.discard(entity_id)
    neighbors = []
    if neighbor_ids:
        neighbors = db.execute(select(Entity).where(Entity.id.in_(neighbor_ids))).scalars().all()
    return list(rels), list(neighbors)


def search_entities(db: Session, query: str, limit: int = 20) -> list[Entity]:
    return db.execute(
        select(Entity).where(Entity.name.ilike(f"%{query}%")).limit(limit)
    ).scalars().all()
