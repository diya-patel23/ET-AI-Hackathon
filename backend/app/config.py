"""
Central configuration. Everything the rest of the app reads comes through here,
so you only ever change settings in one place.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "documents"          # stored original uploads
CHROMA_DIR = DATA_DIR / "chroma"           # vector store persistence
DB_PATH = DATA_DIR / "app.db"              # sqlite file

for d in (DATA_DIR, DOCS_DIR, CHROMA_DIR):
    d.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# --- LLM ---
# LLM_PROVIDER selects the backend: "gemini" (default) or "ollama".
#   gemini  — uses Google Gemini via GEMINI_API_KEY; subject to free-tier quotas.
#   ollama  — calls a local Ollama server (no key, no quota, fully offline).
#             Install: https://ollama.com  |  then: ollama pull <model>
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()  # gemini | ollama

# Gemini — only needed when LLM_PROVIDER=gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Ollama — only needed when LLM_PROVIDER=ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Model name. For Gemini: e.g. "gemini-2.0-flash". For Ollama: e.g. "llama3.2", "mistral".
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")

# --- Embeddings ---
# "sentence-transformers" tries to use a real semantic embedding model
# (all-MiniLM-L6-v2). It needs a one-time download from huggingface.co on first
# run. If that's unavailable (offline / restricted network — common on
# industrial sites), the app automatically falls back to a TF-IDF vectorizer
# that needs no network access at all. Both implement the same interface, so
# nothing else in the app needs to know which one is active.
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "auto")  # auto | sentence-transformers | tfidf

# --- Misc ---
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
CHUNK_SIZE_CHARS = int(os.getenv("CHUNK_SIZE_CHARS", "1200"))
CHUNK_OVERLAP_CHARS = int(os.getenv("CHUNK_OVERLAP_CHARS", "150"))

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
