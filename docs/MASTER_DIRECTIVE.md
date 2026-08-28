# MASTER DIRECTIVE — SICCE Rebuild & Scale Plan

**Version:** 1.0 · **Date:** 2026-08-23 · **Authority:** Founder-authored. This file governs all work on this repository.

> ## READ THIS FIRST (for any AI agent or human contributor)
>
> This directive **supersedes** `AGENT_RULES.md`, `implementation_plan.md`, `eagles_eye_view.md`, and any chat history claims about project status.
>
> - `AGENT_RULES.md` currently FORBIDS importing real SNOMED CT data and mandates staying on `mock_snomed_db.json`. That constraint produced a hollow demo (26 concepts) and is **reversed by this document**.
> - Your first task before executing anything: read `AGENT_RULES.md`, compare it against this file, produce a one-page conflict report for the founder, and **wait for explicit founder approval** on the conflicts. Do not silently follow either file where they disagree.
> - Between every phase there is a hard **STOP GATE**: you finish the phase, run its verification commands, present evidence to the founder, and wait. Never roll phases together.

---

## 0. Mission

SICCE = SNOMED-India Clinical Coding Engine.
Turn messy Indian clinical input (text, prescription photos, voice) into validated, coded, ABDM-compliant FHIR R4 bundles and NHCX-ready claim payloads — **with measured accuracy, honest failure modes, and zero fabricated output**.

Business goal: become the compliance/coding infrastructure ("compliance-in-a-box") for small Indian EMR/HIS vendors and TPA-side claim digitization. NOT another doctor-facing scribe.

---

## 1. Verified Current State (audit of 2026-08-23)

Every item below was verified by direct inspection. Reference these exact locations when fixing.

| # | Finding | Location | Severity |
|---|---------|----------|----------|
| A1 | **Fabricated clinical data returned on OCR failure** — endpoint silently invents "Headache / Fever / Paracetamol 650mg" with fake confidences 0.95–0.99 and fake bounding boxes instead of returning an error | `main.py:347-367` | CRITICAL |
| A2 | **Knowledge base is a toy** — SQLite DB contains 26 concepts and 39 brands (verified via SQL count). Entire product value depends on this | `clinical_knowledge.db`, seed source `build_clinical_db.py` | CRITICAL |
| A3 | **ABHA gateway is 100% mock** — OTP is always accepted (`123456`), every verified user becomes hardcoded `"Mr. Rahul Verma"`, no network calls exist | `abha_gateway.py` (entire file) | HIGH |
| A4 | Unsalted single-pass SHA-256 password hashing | `auth_service.py:54-56` | HIGH |
| A5 | CORS wildcard `allow_origins=["*"]` combined with `allow_credentials=True` | `main.py:75-81` | HIGH |
| A6 | WhatsApp webhook has NO authentication — anyone can POST and burn LLM credits | `main.py:581-613` | HIGH |
| A7 | Billing endpoints are hardcoded fiction — balance always returns 4980/5000 credits, default key `test-dev-key` baked into signature | `main.py:650-660` | MEDIUM |
| A8 | NHCX pre-adjudicator runs on 5 hardcoded rule rows presented as an engine | `nhcx_adjudicator.py:14-50` | MEDIUM |
| A9 | Test suite: 24 pass / **3 fail** (billing credit count mismatch, dosage format `'BD' != 'twice daily'`, postman-collection endpoint 404). Docs claiming "all tests passing" are false | `tests/test_pipeline.py` | HIGH |
| A10 | Deployment sprawl: Vercel serverless (`vercel.json`, `api/index.py`), Render (`render.yaml`, `Dockerfile`), on-prem compose files — plus a documented 437 MB bundle-size fight caused by forcing ML deps into serverless | repo root | MEDIUM |
| A11 | Stale/false documentation — `eagles_eye_view.md` status dashboard does not match reality (claims Supabase missing schema, 5 tests, etc.) | `eagles_eye_view.md` | LOW |
| A12 | PHI sanitizer strips identifiers but sanitized text still goes to Google Gemini cloud while docs imply DPDP erasure guarantees | `nlp_parser.py:58-80`, `main.py:490-504` | MEDIUM |

**Rule:** never re-state old claims ("production ready", "all tests pass") without re-running verification in the same session.

---

## 2. THE LAWS — Non-Negotiable Rules (DO NOT violate)

These override convenience, deadlines, and demo pressure.

### NEVER do these
1. **NEVER fabricate clinical data.** If parsing/OCR/resolution fails, return an explicit error (`4xx/5xx` JSON with `status: "error"`). Inventing symptoms/drugs is disqualifying in medicine. (Kills A1 permanently.)
2. **NEVER present a mock as a shipped feature.** Every mock must return a response field `"mode": "mock"` and the README/API doc must label it MOCK until real integration exists. (A3, A7, A8.)
3. **NEVER add new features** (voice GA, WhatsApp GA, consumer app, billing dashboard, new UI panels) until Phase 1 Definition-of-Done is signed off by the founder.
4. **NEVER claim "production ready"/"working"/"deployed" without live proof attached** (command output, HTTP status, URL hit in the same session).
5. **NEVER commit while any test fails.** Fix or explicitly mark-and-report failing tests to the founder first.
6. **NEVER send raw un-sanitized PHI to external LLM APIs.** The sanitizer must run upstream of every LLM call.
7. **NEVER introduce a second deployment platform.** One target: Docker container on Render. On-prem = same image via compose.
8. **NEVER store passwords with plain SHA-256 / MD5.** Use argon2id (or bcrypt if argon2 unavailable).
9. **NEVER leave an unauthenticated mutating or compute-expensive endpoint** (LLM calls, file uploads).
10. **NEVER edit `AGENT_RULES.md` or history docs silently.** Founder decides their fate after your conflict report.

### ALWAYS do these
1. Error-first design: define the failure response before the success path.
2. Every task ends with: tests green + a runnable verification command + honest output pasted to the founder.
3. Small commits, imperative messages, one logical change each.
4. Keep `mock_snomed_db.json` ONLY as offline emergency fallback; it must never be the primary path again.
5. Ask the founder when a decision changes cost, architecture, or public claims.

---

## 3. PHASE 1 — Make It Real (Weeks 1–10)

Goal: replace the hollow core with real data, honest errors, security basics, measurable accuracy, one deployment, green CI.

### Task 1.1 — Obtain SNOMED CT India license & RF2 data
- **Steps:**
  1. Apply at NRCeS (nrces.in) for the free SNOMED CT India license (affiliate/licensee registration). Founder does the identity/org steps; agent prepares answers.
  2. Download the current **India Edition RF2 release** (Snapshot zip: `SnomedCT_InternationalRF2_PRODUCTION_*.zip` + India extension module).
  3. Store under `data/rf2/` (git-ignored; add `data/` to `.gitignore`). Record version/date in `data/rf2/VERSION.txt`.
- **Acceptance:** RF2 snapshot files exist locally; `VERSION.txt` states edition + release date.
- **STOP GATE:** license terms confirmed by founder before redistribution decisions later.

### Task 1.2 — Build the real terminology pipeline (kills A2)
- **Architecture decision (binding):**
  - Primary local/offline store: **SQLite FTS5** (already implemented in `terminology_resolver.py`) loaded with the FULL RF2-derived tables. SQLite handles millions of rows in a single file at zero cost — no Supabase 500 MB limit issue.
  - Cloud accelerator: keep Supabase `pg_trgm` fuzzy RPC, seeded with a **curated refset** (~15–25k most common Indian OPD concepts + brands + Hinglish synonyms), not the full ontology.
- **Steps:**
  1. Write `scripts/load_rf2.py`: parse RF2 Snapshot files (`sct2_Concept_Snapshot`, `sct2_Description_Snapshot-en`, India extension) → build tables `concepts(concept_id, preferred_name, semantic_tag, active)` + `concepts_fts` (+ existing `brands` untouched). Include only active concepts; map semantic tags from the metadata refset.
  2. Run loader; verify row counts (expect hundreds of thousands of concepts, >1M descriptions).
  3. Update `terminology_resolver.py` search order: SQLite full DB → Supabase refset fuzzy → difflib fallback → **return uncoded** (never guess silently). Log unresolved terms to `logs/unresolved_terms.jsonl` (feeds dictionary work later).
  4. Add resolver unit test asserting resolution of 20 real SNOMED codes sampled from RF2 (not from the mock file).
- **Verification:** `python scripts/load_rf2.py --check` prints counts; `pytest tests/test_terminology_full.py` passes.
- **Acceptance:** resolving e.g. "community acquired pneumonia", "type 2 diabetes mellitus", brand→generic across 500+ brands works from the real DB.

### Task 1.3 — Delete fabricated fallbacks (kills A1, honesty layer)
- **Steps:**
  1. Remove the entire fallback block at `main.py:347-367`. On OCR/pipeline exception: return `HTTP 502` JSON `{"status":"error","stage":"ocr","detail": "<safe message>"}`. Log full traceback server-side only.
  2. Audit ALL endpoints for similar invented-data patterns (grep for hardcoded confidence values like `0.9`, sample strings like `"Rahul Verma"`, `"Apollo"`) and remove/mock-label them.
  3. Mock-labeled mode: ABHA gateway, NHCX adjudicator, billing endpoints must include `"mode": "mock"` in every response until Tasks 3.x integrate reality (see Phase 3).
- **Verification:** upload a corrupt/garbage image to `/api/v1/ocr-parse` → receive error JSON, never clinical content. Document the curl command in `docs/verification.md`.
- **Acceptance:** zero code paths invent clinical entities.

### Task 1.4 — Security hardening (kills A4, A5, A6, part of A7)
- **Steps:**
  1. Replace SHA-256 hashing in `auth_service.py` with argon2id (`argon2-cffi`); migrate transparently: on sign-in, if stored hash looks like bare sha256, verify then re-hash-and-update. New signups always argon2id.
  2. CORS: restrict `allow_origins` to explicit origins from env var `ALLOWED_ORIGINS` (comma-separated). No wildcard+credentials combo.
  3. Protect `/api/v1/webhook/whatsapp` with the same `verify_api_key` dependency (or a dedicated webhook secret header `X-WEBHOOK-SECRET` compared via `secrets.compare_digest`).
  4. Remove default `"test-dev-key"` from function signatures; require explicit env-configured key; keep a test-only fixture inside tests, not prod code.
  5. Rate-limit `/api/auth/sign-in` (e.g., 10/min/IP) to blunt credential stuffing.
- **Verification:** `pytest tests/test_security.py` (new): wrong-origin blocked, webhook without secret → 403, sha256→argon2 migration works.
- **Acceptance:** none of the five issues reproduce.

### Task 1.5 — Evaluation harness (the credibility moat)
- **Steps:**
  1. Create `eval/notes.jsonl` schema: `{"id","text_raw","language_mix","entities":{"symptoms":[],"diagnoses":[],"medications":[{"brand_name","generic_name","dose","frequency"}]}}`.
  2. Founder supplies 200–300 de-identified REAL notes via clinic network (this is the founder's job — agent builds tooling only). Agent may bootstrap 30 synthetic notes clearly tagged `source:"synthetic"` for plumbing tests.
  3. Write `eval/run_eval.py`: runs the pipeline over the set, computes precision/recall/F1 per entity type (symptom/diagnosis/medication) incl. dose/frequency sub-metrics; outputs `eval/results/<date>.json` and a human-readable table.
  4. Add `make eval` / `scripts/run_eval.ps1`.
- **Targets (gate for Phase 2 outreach):** diagnosis F1 ≥ 0.90, medication F1 ≥ 0.92, symptom F1 ≥ 0.88 on the real set. If missed: iterate dictionary/rules — do NOT lower targets silently.
- **Acceptance:** results file exists with methodology notes (what counted as correct).

### Task 1.6 — One deployment (kills A10)
- **Steps:**
  1. Keep: `Dockerfile`, `docker-compose.yml` (dev), `render.yaml`, `Dockerfile.onprem` + `docker-compose.enterprise.yml` (same image, on-prem profile).
  2. Delete from deploy story: `vercel.json`, `api/index.py`, any docs referencing Vercel. Move them to `attic/` folder rather than deleting git history blindly.
  3. Ensure Docker image does NOT ship medspacy/spacy unless actually used at runtime; if unused (regex path active), drop them → smaller image, faster cold start. Verify which path `ClinicalParser` uses in production config and remove dead branch imports accordingly (keep code behind optional import).
  4. Render health check wired to `/health`; add `/health` check that fails loudly if terminology row count < 100k (catches empty-DB deploys).
- **Verification:** `docker build .` succeeds; `docker run` + `curl /health` shows `terminology_concepts >= 100000`; one Render deploy from clean checkout.
- **Acceptance:** exactly one supported cloud path.

### Task 1.7 — Green CI (kills A9)
- **Steps:**
  1. Fix the 3 failing tests: reconcile billing credit numbers between endpoint and test; decide canonical dosage representation (recommend: keep vernacular `"BD"` in extraction AND normalized `"twice daily"` field; update test to assert both); implement or remove the postman-collection endpoint (decide with founder; default: implement simple `/postman_collection.json` generator since docs reference it).
  2. Add GitHub Actions `.github/workflows/ci.yml`: on push/PR → install deps → `pytest -q`. Branch protection: CI green required.
- **Verification:** CI run URL green on the next push; local `pytest -q` reports 0 failures.
- **Acceptance:** no known-failing tests.

### Task 1.8 — Truth-in-docs pass (kills A11)
- Rewrite `eagles_eye_view.md` status dashboard to reflect verified reality with dates; add `docs/status.md` as the living status page updated at end of every task. Mark every mock subsystem explicitly as MOCK.
- **Acceptance:** every claim in docs traceable to a command output dated that day.

---

## 3.5 PHASE 1.5 — Parallel Track While Founder Gates Pending

Execute ONLY after Phase 1 is verified done and while awaiting: (a) NRCeS license, (b) real notes.
No outreach, no new features beyond these tasks, mocks stay labeled, tests green at end.

### Task 1.5A — Curated OPD RefSet v1 (interim credibility + future cloud refset)
- Founder supplies (voice notes/chat is fine) their top ~200–400 real-world OPD conditions, symptoms, and findings from clinical practice.
- Agent structures them into `data/refset/opd_refset_v1.json` schema:
  `{"preferred_name","semantic_tag","icd10_guess(optional)","hinglish_synonyms":[],"abbreviations":[]}` — every entry clinically plausible; NO invented concepts.
- Load into `clinical_knowledge.db` (tagged rows are fine to merge into `concepts`/synonym tables) AND export `scripts/export_supabase_refset.sql` for the future cloud refset.
- Acceptance: `/health` still reports degraded (count <100k guard unchanged); demo parse of 20 common OPD notes resolves ≥90% of entities.

### Task 1.5B — Public formulary expansion (real, legal brand→generic data)
- Ingest the **PMBJP / Jan Aushadhi public product list** (publicly published by Govt of India) plus any other legally public Indian formulary sources.
- Expand the `brands` table with real `(brand_name, generic_name, category)` rows. Every row must carry a real generic mapping — zero invented drugs.
- Re-run resolver tests + eval; commit counts as proof.

### Task 1.5C — Deployment dry-run (so launch takes minutes, not days)
- Run `docker build -t sicce .` locally; run container; verify `/health` + one text parse inside the container.
- Write `docs/DEPLOY_CHECKLIST.md`: env vars required, exact Render deploy steps, post-deploy verification commands.
- Acceptance: founder can take current build live in <10 minutes following only that doc.

### Task 1.5D — (Founder, parallel) ABDM Sandbox registration
- Register at sandbox.abdm.gov.in NOW — it does NOT require the NRCeS license. Use `docs/ABDM_SANDBOX_REGISTRATION.md`.

---

## 4. PHASE 2 — Wedge & First Revenue (Months 3–6)

Positioning: **"ABDM/NHCX compliance engine in a box"** for small EMR/HIS vendors (2–5 dev teams, thousands of them in India) and pilot with 1–2 TPAs for legacy claim digitization. Not sold to doctors directly.

- **Offer spec:** POST messy note/image → coded FHIR R4 + NHCX-shaped payload + CDSS flags. Pricing guardrails: ₹25k/mo pilot (fixed), ₹50k–1L/mo annual per vendor tier. Free dev sandbox: 100 calls/day with watermarked output. Never price against free (Snowstorm/NRCeS) — sell validated accuracy + certification-readiness.
- **Assets to build (agent):** 1-page technical pitch PDF, live demo link (read-only), accuracy report from Task 1.5, sandbox signup flow (manual is fine initially).
- **Founder actions (agent cannot do):** LinkedIn outreach to CTOs/founders of Indian HIS vendors; 3 signed LOIs/pilots is the gate.
- **STOP GATE:** do not begin Phase 3 spend/effort until ≥3 pilots are verbally committed.

## 5. PHASE 3 — Moats (Months 4–9)

1. **Open-source dictionary v1:** publish curated Hinglish/abbreviation → SNOMED mapping as Apache-2.0 repo (`sicce-hinglish-lexicon`) generated from `logs/unresolved_terms.jsonl` curation. Goal: become the canonical reference dataset; inbound leads + C-DAC/SNOMED International visibility.
2. **Real ABDM sandbox integration:** register at sandbox.abdm.gov.in; implement M1 (ABHA OTP) against real gateway behind feature flag `ABDM_MODE=sandbox|production|mock`; then M2 care-context linkage. Retire mock paths per Law #2 once certified.
3. **Data flywheel:** with written customer consent, resolved+unresolved term pairs feed weekly dictionary updates. Track `unresolved_rate` trend as a KPI (target <5% after month 6).
4. **On-prem packaging:** one-command enterprise compose profile; target hospital chains that refuse cloud PHI.

## 6. PHASE 4 — Scale Levers & KPIs (Months 9+)

First hire = **solutions engineer** (integrations + pilots), not another feature developer. Partner rev-share with embedding vendors. Raise only after 3+ paying pilots (or stay bootstrapped-profitable).

| KPI | 6-month target | Measured by |
|---|---|---|
| Diagnosis F1 / Medication F1 | ≥0.90 / ≥0.92 (published) | eval harness |
| Paying pilots | 3–5 | contracts |
| Cost per parsed note | <₹0.05 | cache-hit rate + token logs |
| Unresolved-term rate | <5% | resolver logs |
| ABDM status | Sandbox-certified M1(+M2) | NHA portal |

---

## 7. Explicitly Deferred / Forbidden Backlog (do not build now)

- Voice scribe general availability · WhatsApp bot GA · consumer patient app · billing/payments dashboards · pricing competition vs free tools · any new frontend framework migration · multi-tenant org features beyond API keys.
- These live here so agents stop "helpfully" building them.

---

## 8. Solo Founder Operating Manual (personal advice section)

1. **Time split:** early stage ≈ 40% building / 60% distribution (outreach, content, partnerships). Code you don't sell is a hobby. As a physician-founder your credibility IS the sales channel — use it in public writing weekly (clinical informatics, NHCX explainers).
2. **Weekly cadence:** Mon: pick ONE task from this doc. Tue–Thu: execute. Fri: verify + send status to yourself (or advisor) with evidence. Nothing carries silently.
3. **Scope discipline rule:** any idea not in this file goes to `DEFERRED` (Section 7) instead of the sprint. Revisit quarterly.
4. **Trust rule:** after the agent-history problems in this repo, adopt: *agent claims nothing; commands prove everything.* Every status update includes paste-able proof.
5. **Money:** keep burn ~zero (SQLite, free tiers) until pilots pay. First revenue beats first investor.
6. **Hiring:** solutions engineer before engineer #2; clinical safety reviewer (can be a peer doctor) before scaling to hospitals.
7. **When to raise:** after 3+ paid pilots with retention signal; raise on distribution metrics, not demos.
8. **Protect the asset:** your medical license and reputation. Never let marketing language outrun the system's verified capability (Law #4 exists for you as much as users).

---

## 9. DEFINITION OF DONE — whole directive

All true simultaneously:

- [ ] Real RF2-loaded terminology resolves ≥100k concepts (Task 1.2 check passes)
- [ ] Zero code paths fabricate clinical data (grep-audit clean, corrupt-input curl proves error path)
- [ ] All mocks labeled `mode:"mock"`
- [ ] argon2id auth, locked CORS, authenticated webhooks, no baked-in default keys
- [ ] Eval report published internally with F1 ≥ targets
- [ ] Single cloud deployment path; `/health` enforces non-empty terminology
- [ ] CI green; 0 known failing tests
- [ ] Docs match reality with dated evidence
- [ ] ≥3 signed pilots (founder-confirmed)

**End of directive. When in doubt: stop, verify, report honestly, ask the founder.**
