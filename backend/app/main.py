import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.db import init_db
from app.api import (
    ingest_routes,
    document_routes,
    search_routes,
    chat_routes,
    agent_routes,
    graph_routes,
    dashboard_routes,
)

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Unified Asset & Operations Brain",
    description="Industrial Knowledge Intelligence Platform API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    from app.llm_client import llm_available
    from app.ingestion.embedder import embedding_backend_name
    return {
        "status": "ok",
        "llm_configured": llm_available(),
        "embedding_backend": embedding_backend_name(),
    }


app.include_router(ingest_routes.router)
app.include_router(document_routes.router)
app.include_router(search_routes.router)
app.include_router(chat_routes.router)
app.include_router(agent_routes.router)
app.include_router(graph_routes.router)
app.include_router(dashboard_routes.router)
