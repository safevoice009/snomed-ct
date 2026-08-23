# OpenSpec Change Proposal: Phase 1 — SICCE Real Architecture Rebuild

## Context
Per `MASTER_DIRECTIVE.md`, the SICCE codebase is transitioning from a 20% prototype / 80% demo state to a production-grade, secure, verifiable B2B clinical middleware. This requires eliminating all simulated placeholders, ingesting real SNOMED CT RF2 data into SQLite FTS5, hardening security with Argon2id and locked CORS/webhooks, building a clinical evaluation benchmark, unifying deployment around Docker, and instituting green CI with truth-in-documentation.

## Goals
1. Replace toy 26-concept dictionary with a robust RF2 ingestion pipeline (`scripts/load_rf2.py`) building SQLite FTS5 concept and description indexes.
2. Ensure 100% honesty across all endpoints: zero fabricated data fallbacks and explicit `"mode": "mock"` tags on simulated subsystems.
3. Harden authentication using Argon2id with automatic backward-compatible migration from legacy SHA-256.
4. Lock down CORS to configured origins and authenticate the WhatsApp webhook endpoint.
5. Create an evaluation harness (`eval/run_eval.py` + `eval/notes.jsonl`) calculating precision, recall, and F1.
6. Retire Vercel serverless artifacts to `attic/` and standardize on unified Docker container.
7. Setup GitHub Actions CI workflow enforcing 100% passing tests.
8. Establish truth-in-documentation in `docs/status.md` and update repository summaries.
