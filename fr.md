# SICCE Industry-Grade Terminology & NLP API Gateway Implementation Plan

> **For Antigravity:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the SNOMED-India Clinical Coding Engine (SICCE) into an industry-grade, highly secure, and cloud-efficient B2B API service using standard open-source clinical NLP tools and FHIR Terminology Server integrations.

**Architecture:** We will implement a secure FastAPI serverless gateway that leverages a caching clinical text parser (LiteLLM with structured outputs), links extracted terms to a multi-backend Terminology Resolver (supporting local JSON fallback, Supabase pg_trgm fuzzy matching, and official HL7 FHIR Terminology Server/Snowstorm API endpoints), and validates the final payload against official ABDM FHIR R4 profile specifications.

**Tech Stack:** FastAPI, LiteLLM (structured parsing), Supabase PostgreSQL (trigram fuzzy matching), Snowstorm FHIR Terminology API, fhir.resources (HL7 FHIR validation), SlowAPI (rate-limiting), Python-dotenv.

---

## User Review Required

> [!IMPORTANT]
> **Open-Source Integrations for Career and Tech Leverage:**
> 1. **Multi-Backend Terminology Architecture:** We are structuring the `TerminologyResolver` to support three backends:
>    * *Mock Local JSON* (zero-dependency testing).
>    * *Supabase Postgres* (fuzzy text/trigram queries via `pg_trgm` to fit inside the 500MB free-tier limits).
>    * *FHIR Terminology Server* (queries standard Snowstorm endpoints via the official FHIR `/CodeSystem/$lookup` and `/ValueSet/$expand` APIs).
> 2. **Structured Outputs & LLM Safety:** LiteLLM is upgraded to use Pydantic models to guarantee JSON formatting.
> 3. **API-Key Auth and Rate-Limiting:** Necessary middleware is added to let you charge EMR partners per API call.

## Open Questions

> [!NOTE]
> 1. Do you have a preferred Snowstorm server URL (e.g., standard C-DAC test servers or SNOMED International's sandbox), or should we default to SNOMED's public sandbox for demonstration purposes?
> 2. What rate limits would you like to set for free vs. paid API keys? (Default is 60 requests/minute for standard keys).

---

## Proposed Changes

We will implement changes within `/home/sucharithpop/Downloads/snomed ct`.

### Task 1: Environment & Requirements Definition

**Files:**
* Modify: [requirements.txt](file:///home/sucharithpop/Downloads/snomed%20ct/requirements.txt)
* Create: `[NEW] .env.example`

**Steps:**
1. Add `slowapi`, `python-dotenv`, and `pydantic` to `requirements.txt`.
2. Create `.env.example` template declaring variables for `SUPABASE_URL`, `SUPABASE_KEY`, `GEMINI_API_KEY`, `TERMINOLOGY_SERVER_URL`, and `API_KEYS`.

---

### Task 2: Supabase DDL Schema and Seed

**Files:**
* Create: `[NEW] supabase_schema.sql`

**Steps:**
1. Write DDL setup script:
   - Enable `pg_trgm` extension.
   - Define `snomed_concepts` and `concept_synonyms` tables.
   - Build GIN trigram indexes on synonym text for rapid fuzzy search.
   - Create SQL insert statements using seed concepts in `mock_snomed_db.json`.

---

### Task 3: Terminology Resolver Multi-Backend Expansion

**Files:**
* Modify: [terminology_resolver.py](file:///home/sucharithpop/Downloads/snomed%20ct/terminology_resolver.py)

**Steps:**
1. Upgrade `TerminologyResolver` to auto-detect configuration:
   - If `TERMINOLOGY_SERVER_URL` is set, route queries via HTTP FHIR `$lookup` or `$expand` requests.
   - If `SUPABASE_URL` is set, run fuzzy postgres queries via psycopg2.
   - Otherwise, fall back to exact/fuzzy parsing of local `mock_snomed_db.json`.

---

### Task 4: Caching NLP Parser with Structured Output

**Files:**
* Modify: [nlp_parser.py](file:///home/sucharithpop/Downloads/snomed%20ct/nlp_parser.py)

**Steps:**
1. Define a Pydantic schema class `ParsedClinicalNote` to structure symptoms, diagnoses, and medications.
2. Implement a runtime memory cache `ClinicalCache` using standard python dictionaries to intercept identical note queries before calling LLM APIs.
3. Configure LiteLLM to enforce JSON output using the Pydantic schema definition.

---

### Task 5: ABDM FHIR Bundle Generator Compliance

**Files:**
* Modify: [fhir_generator.py](file:///home/sucharithpop/Downloads/snomed%20ct/fhir_generator.py)

**Steps:**
1. Ensure the bundle maps the standard Indian NRCeS profile metadata URLs:
   - Patient Profile: `https://nrces.in/ndhm/fhir/r4/StructureDefinition/Patient`
   - Practitioner Profile: `https://nrces.in/ndhm/fhir/r4/StructureDefinition/Practitioner`
   - Condition Profile: `https://nrces.in/ndhm/fhir/r4/StructureDefinition/Condition`
2. Validate using `fhir.resources.R4B.bundle.Bundle.validate(bundle)` when library is available.

---

### Task 6: Secure FastAPI Server App Gateway

**Files:**
* Modify: [main.py](file:///home/sucharithpop/Downloads/snomed%20ct/main.py)

**Steps:**
1. Convert `main.py` into a FastAPI application instance.
2. Implement custom middleware or dependency injection for API key header validation (`X-API-Key`).
3. Set up CORS configuration and API rate-limiting via `slowapi`.
4. Expose:
   - `POST /api/v1/parse` processing raw patient text.
   - `GET /health` responding with connectivity reports of the configured Terminology Server and LLM API.

---

### Task 7: Vercel Deployment Configuration

**Files:**
* Create: `[NEW] vercel.json`

**Steps:**
1. Define serverless handlers routing traffic from `/api/*` to `main.py`.

---

### Task 8: Verification Unit Tests

**Files:**
* Create: `[NEW] tests/test_pipeline.py`

**Steps:**
1. Write testing suites using `unittest`:
   - Mock LLM responses to test extraction logic deterministic fallback.
   - Test terminology resolver matching logic on local mock data.
   - Use `fastapi.testclient.TestClient` to verify HTTP status codes, rate limits, and authentication errors.

---

## Verification Plan

### Automated Tests
Run unit tests to verify integration correctness:
```bash
python3 -m unittest discover -s tests
```

### Manual Verification
1. Run application locally:
   ```bash
   uvicorn main:app --reload
   ```
2. Request `/health` to verify components setup:
   ```bash
   curl -i http://127.0.0.1:8000/health
   ```
3. Test parsing with invalid API key:
   ```bash
   curl -i -X POST http://127.0.0.1:8000/api/v1/parse \
     -H "X-API-KEY: invalid-key" \
     -H "Content-Type: application/json" \
     -d '{"text": "sar dard"}'
   ```
   *Expected:* HTTP 403 Forbidden.
4. Test parsing with valid API key:
   ```bash
   curl -i -X POST http://127.0.0.1:8000/api/v1/parse \
     -H "X-API-KEY: test-dev-key" \
     -H "Content-Type: application/json" \
     -d '{"text": "Pt c/o loose motion x 3 days, AP+, Dolo 650 BD"}'
   ```
   *Expected:* HTTP 200 OK with fully structured and validated ABDM FHIR JSON bundle.
