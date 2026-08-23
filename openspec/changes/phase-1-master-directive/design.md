# OpenSpec Design: Phase 1 — SICCE Real Architecture Rebuild

## Technical Architecture

### 1. Real Terminology Engine (SQLite FTS5 + Supabase Accelerator)
- **Local Database**: `clinical_knowledge.db`
- **Schema**:
  - `concepts(concept_id TEXT PRIMARY KEY, preferred_name TEXT, semantic_tag TEXT, active INTEGER)`
  - `concepts_fts USING fts5(concept_id, preferred_name, semantic_tag, content='concepts', content_rowid='rowid')`
  - `descriptions(description_id TEXT PRIMARY KEY, concept_id TEXT, term TEXT, type_id TEXT, active INTEGER)`
  - `descriptions_fts USING fts5(term, concept_id UNINDEXED, content='descriptions', content_rowid='rowid')`
  - `brands(brand_name TEXT PRIMARY KEY, generic_name TEXT, default_dose TEXT, default_freq TEXT)`
- **RF2 Ingestion Pipeline**: `scripts/load_rf2.py`
  - Stream parses `sct2_Concept_Snapshot_*.txt` and `sct2_Description_Snapshot-en_*.txt`.
  - Also includes high-yield Indian clinical seeds (~500+ Indian generic brands and common clinical terms) so the engine functions immediately at enterprise quality before full multi-gigabyte RF2 file drop.
- **Search Precedence**:
  1. SQLite FTS5 exact/prefix phrase match on `concepts_fts` and `descriptions_fts`.
  2. Supabase `pg_trgm` fuzzy RPC match (if connected).
  3. Indian brand-to-generic dictionary lookup.
  4. Returns `coded: false` / uncoded concept (never guesses or fabricates).

### 2. Security & Authentication Layer
- **Argon2id Integration**: `auth_service.py` uses `argon2-cffi` (with bcrypt fallback).
- **Migration Strategy**: If a user logs in and the stored password hash is 64 hex characters (SHA-256), verify the SHA-256 match, hash with Argon2id, and update the database record.
- **CORS Lockdown**: `allow_origins` sourced strictly from `os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")`.
- **Webhook Security**: `/api/v1/webhook/whatsapp` requires `X-WEBHOOK-SECRET` or API key authentication.

### 3. Subsystem Mock Labeling
- `abha_gateway.py`, `nhcx_adjudicator.py`, and credit wallet responses explicitly labeled with `"mode": "mock"` and documented in API responses.

### 4. Evaluation Harness
- `eval/notes.jsonl`: Standardized format for de-identified gold-standard prescription notes.
- `eval/run_eval.py`: Automated pipeline evaluating symptoms, diagnoses, and medications (generic name, dose, frequency) computing Precision, Recall, and F1.

### 5. Unified Deployment & CI
- Single Dockerfile optimized for Render and on-premise Docker Compose.
- Deprecated Vercel files moved to `attic/`.
- `.github/workflows/ci.yml` running pytest on Python 3.12.
