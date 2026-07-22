from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Entity
from app.graph.store import get_entity_neighbors, search_entities
from app.schemas import EntityGraph, EntityOut

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/search", response_model=list[EntityOut])
def graph_search(name: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return search_entities(db, name)


@router.get("/entity/{entity_id}", response_model=EntityGraph)
def graph_entity(entity_id: str, db: Session = Depends(get_db)):
    entity = db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    rels, neighbors = get_entity_neighbors(db, entity_id)
    return {"entity": entity, "relationships": rels, "neighbors": neighbors}
