# SICCE Living Status & Verification Dashboard

**Last Verified Session**: August 24, 2026  
**Governing Authority**: [`MASTER_DIRECTIVE.md`](file:///c:/Users/unbou/snomedct/snomed%20ct/MASTER_DIRECTIVE.md)  
**Current Phase 1 Status**: 🟡 **~75% Complete — BLOCKED ON FOUNDER INPUTS (NOT READY FOR OUTREACH)**  
**Pytest Suite**: `40 passed, 0 failed (100% pass rate)`  

---

## 🛑 Blocked Founder Gates (Required Before Phase 2 Outreach)

| Required Founder Action | Status | Impact on System | Next Step for Founder |
| :--- | :--- | :--- | :--- |
| **1. Apply for Free NRCeS SNOMED CT License** | 🔴 **PENDING (HUMAN REQUIRED)** | `clinical_knowledge.db` contains **106 concepts / 327 descriptions / 99 brands** (OPD RefSet v1 + PMBJP public generic formulary). Real gigabyte RF2 snapshot files do not exist yet in `data/rf2/`. `/health` warns `degraded_unseeded_terminology`. | Register at [nrces.in](https://www.nrces.in), download official India Edition Snapshot `.zip`, and place in `data/rf2/`. Then run `python scripts/load_rf2.py`. |
| **2. Supply 200+ Real De-identified Clinical Notes** | 🔴 **PENDING (HUMAN REQUIRED)** | `eval/notes.jsonl` currently has synthetic developer cases. System accuracy cannot be certified on synthetic data. | Export 200–300 de-identified OPD prescription notes and format into `eval/notes.jsonl`. |
| **3. ABDM Sandbox Registration** | 🔴 **PENDING (HUMAN REQUIRED)** | Sandbox API credentials required for live M1/M2 testing at `sandbox.abdm.gov.in`. | Follow [`docs/ABDM_SANDBOX_REGISTRATION.md`](file:///c:/Users/unbou/snomedct/snomed%20ct/docs/ABDM_SANDBOX_REGISTRATION.md) to register and acquire client keys. |

---

## 📊 Detailed Subsystem Audit & Truth Table

| Subsystem | Audit Status | Code Reality | Notes / Next Actions |
| :--- | :--- | :--- | :--- |
| **Data Integrity & Zero Code Collisions (F1/F3)** | 🟢 **ENFORCED** | All unverified brand codes set to `NULL` (`coded=false`). Permanent guard test asserts NO SNOMED ID maps to >1 distinct generic. | Verified by `test_no_duplicate_snomed_codes_across_different_generics`. |
| **RF2 Programmatic Backfill (F4)** | 🟡 **PROGRAMMATIC DESIGN** | When official NRCeS RF2 zip arrives, brand codes will be matched programmatically against RF2 substance descriptions — zero model hallucination. | Documented in `scripts/load_rf2.py`. |
| **Local Container Build (F5)** | 🟡 **PENDING DOCKER DAEMON** | `Dockerfile` and `docs/DEPLOY_CHECKLIST.md` ready; local container build pending Docker Desktop running on host. | Start Docker Desktop to test `docker build -t sicce .`. |
| **Fake OCR Fallbacks (A1)** | 🟢 **FIXED** | Deleted silent fallback in `main.py:345-350` and `vision_parser.py:129`. Returns `HTTP 502: Clinical OCR Extraction Failed`. | Verified with test suite. Zero fabricated entities. |
| **Terminology Database (A2)** | 🟡 **OPD REFSET SEEDED** | Seeded with 106 concepts, 327 descriptions, and 99 brands. Full 350k terminology pending NRCeS snapshot. | Blocked on founder NRCeS download. |
| **Mock Gateway Labeling (A3/A7/A8)** | 🟢 **FIXED** | `"mode": "mock"` explicitly returned by `abha_gateway.py`, `nhcx_adjudicator.py`, and `/api/v1/billing/balance`. | Verified by `tests/test_security.py`. |
| **Auth Security (A4)** | 🟢 **FIXED** | Argon2id (`argon2.PasswordHasher`) implemented in `auth_service.py` with seamless legacy migration. | Verified by `tests/test_security.py`. |
| **CORS Lockdown (A5)** | 🟢 **FIXED** | Replaced wildcard `*` with explicit `ALLOWED_ORIGINS` whitelist. | Verified. |
| **WhatsApp Webhook Auth (A6)** | 🟢 **FIXED** | Protected with `verify_webhook_auth` dependency in `main.py`. Returns `HTTP 403` on unauthenticated calls. | Verified by `tests/test_security.py`. |
| **Cost & Latency Telemetry (Task C)** | 🟢 **ACTIVE** | `logs/metrics.jsonl` logs per-request metrics (<₹0.05/note KPI); `GET /api/v1/metrics/summary` returns p50/p95 latency and hit rates. | Verified. |
| **Unresolved Terms Logging (Task D)** | 🟢 **ACTIVE** | `logs/unresolved_terms.jsonl` captures every unmapped term with timestamp to feed open-source dictionary. | Verified by `tests/test_terminology_full.py`. |
| **Accuracy Benchmark Gate** | 🟡 **PENDING FOUNDER DATA** | Synthetic-only benchmark (circular test against 10 synthetic notes); real-note evaluation pending 200+ founder notes per MASTER_DIRECTIVE Task 1.5. NOT certification-grade. | Must evaluate on real clinical dataset. |

---

## 🛠️ Runnable Verification Commands

```powershell
# 1. Check Knowledge Base Row Counts
uv run python scripts/load_rf2.py --check

# 2. Run Clinical Extraction Evaluation Benchmark (Honest Synthetic Notice)
uv run python eval/run_eval.py

# 3. Run Complete Pytest Suite (40 tests)
uv run pytest -q tests/
```
