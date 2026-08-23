# OpenSpec Tasks: Phase 1 — SICCE Real Architecture Rebuild

- [x] 1. Terminology Pipeline & Real Data Loader (`scripts/load_rf2.py`) <!-- id: 1 -->
  - [x] 1.1 Create RF2 directory structure (`data/rf2/`) and `VERSION.txt` documentation <!-- id: 1.1 -->
  - [x] 1.2 Build `scripts/load_rf2.py` with SQLite FTS5 schema (`concepts`, `concepts_fts`, `descriptions`, `descriptions_fts`, `brands`) <!-- id: 1.2 -->
  - [x] 1.3 Seed rich clinical terminology dataset (500+ Indian brands, full essential OPD SNOMED refset) <!-- id: 1.3 -->
  - [x] 1.4 Update `terminology_resolver.py` search hierarchy and uncoded logging <!-- id: 1.4 -->
  - [x] 1.5 Add `tests/test_terminology_full.py` verifying multi-concept search and brand resolution <!-- id: 1.5 -->

- [x] 2. Security Hardening & Mock Labeling <!-- id: 2 -->
  - [x] 2.1 Replace SHA-256 with Argon2id in `auth_service.py` with transparent legacy migration <!-- id: 2.1 -->
  - [x] 2.2 Lock down CORS to `ALLOWED_ORIGINS` in `main.py` <!-- id: 2.2 -->
  - [x] 2.3 Authenticate `/api/v1/webhook/whatsapp` endpoint with webhook secret / API key <!-- id: 2.3 -->
  - [x] 2.4 Label all mock endpoints (`abha_gateway.py`, `nhcx_adjudicator.py`, billing balance) with `"mode": "mock"` <!-- id: 2.4 -->
  - [x] 2.5 Add `tests/test_security.py` covering auth hashing, CORS origin checks, and webhook protection <!-- id: 2.5 -->

- [x] 3. Clinical Evaluation Harness (`eval/run_eval.py`) <!-- id: 3 -->
  - [x] 3.1 Create `eval/notes.jsonl` with gold standard annotated clinical cases <!-- id: 3.1 -->
  - [x] 3.2 Build `eval/run_eval.py` computing Precision, Recall, and F1 per clinical entity <!-- id: 3.2 -->
  - [x] 3.3 Create test runner script `scripts/run_eval.ps1` <!-- id: 3.3 -->

- [x] 4. Single Deployment, CI & Documentation <!-- id: 4 -->
  - [x] 4.1 Move Vercel serverless artifacts (`vercel.json`, `api/index.py`) to `attic/` <!-- id: 4.1 -->
  - [x] 4.2 Streamline `Dockerfile` and update `/health` with terminology concept threshold check <!-- id: 4.2 -->
  - [x] 4.3 Create GitHub Actions workflow `.github/workflows/ci.yml` <!-- id: 4.3 -->
  - [x] 4.4 Create `docs/status.md` and update `eagles_eye_view.md` with verified session proof <!-- id: 4.4 -->
  - [x] 4.5 Run full verification suite and push to GitHub <!-- id: 4.5 -->

