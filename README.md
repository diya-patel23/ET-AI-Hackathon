# Unified Asset & Operations Brain

Industrial knowledge platform for maintenance, inspection, and safety documents.

**Tech stack:** FastAPI (Python), SQLite, Chroma, Next.js, Tailwind, React Flow, Recharts.

## What it does

* Upload PDFs, DOCX, XLSX, CSV, and images
* Search documents using semantic + keyword search
* Chat with a RAG copilot
* Explore a knowledge graph of equipment, plants, engineers, parts, and standards
* Run three reasoning agents:

  * Root Cause Analysis
  * Maintenance Intelligence
  * Compliance Checker

## Features

* RAG chat
* Upload & browse documents
* Knowledge graph explorer
* RCA / Maintenance / Compliance

## Uploading Your Own Documents

Supported: PDF, DOCX, XLSX, CSV, PNG/JPG.

The current extractor recognises patterns such as:

* `Pump P204`
* `Compressor C305`
* `Engineer: Name`
* `Plant 3`
* `FC-1234`
* `OSHA 1910.132`, `ISO 55001`, `API 610`

Documents that don't follow these patterns are still ingested and searchable.

## What Was Verified

* End-to-end ingestion pipeline
* Knowledge graph population
* Hybrid search
* Dashboard metrics
* All three agents
* Compliance checks
* Frontend production build

Seeded data includes **26 documents, 8 equipment items, and 48 maintenance events**.
