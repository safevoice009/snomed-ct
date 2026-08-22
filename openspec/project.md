# Project Context: SICCE Enterprise Clinical Intelligence Platform

## Tech Stack
- **Backend**: Python 3.14, FastAPI, Uvicorn, LiteLLM, Supabase PostgreSQL with `pg_trgm` GIN Index, Pytest.
- **Frontend**: Vanilla JavaScript (ES6+), Vanilla CSS Enterprise System, 3D Scroll-World Scrub Engine, HTML5 Semantic Elements.
- **Standards & Regulations**: HL7 FHIR R4 (MoHFW NRCES Profile), SNOMED CT International, AYUSH NAMASTE, Indian DPDP Act 2023.

## Architectural Rules
1. **Statutory DPDP Act Zero Retention**: No patient PHI persisted to disk or databases; ephemeral in-memory processing only with cryptographic Section 12 purge audit receipts.
2. **Sub-50ms Terminology Lookups**: Always use Supabase `pg_trgm` GIN trigram indexing with local fallback dictionaries.
3. **Medical Device Disclaimer (Non-SaMD)**: Output administrative clinical data only; must not provide automated diagnostic treatment decisions without clinician oversight.
