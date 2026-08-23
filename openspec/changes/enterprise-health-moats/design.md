# OpenSpec Design: Enterprise Health Moats Suite (SICCE Phase 2)

## Architectural Design

### 1. NHCX Pre-Adjudication Claim Engine (`nhcx_adjudicator.py`)
- Evaluates FHIR and NHCX claim resources against IRDAI/TPA validation rules:
  - **Code Coherence**: Verifies that procedure/medication lines match primary diagnosis ICD-10/SNOMED CT codes.
  - **Medical Necessity Check**: Checks duration limits (e.g. antibiotic or PPI durations exceeding clinical standards without diagnostic attachment).
  - **Claim Integrity Score**: Returns an approval probability score (0-100%), itemized warning checklist, and suggested code corrections before submitting to NHCX.

### 2. ABDM M1/M2 ABHA Gateway (`abha_gateway.py`)
- Provides endpoints for ABHA operations:
  - `POST /api/v1/abdm/abha/generate-otp`: Sends OTP to Aadhaar/mobile.
  - `POST /api/v1/abdm/abha/verify-otp`: Validates OTP and returns ABHA Address (`@abdm`), ABHA Number (`14-digit`), and KYC profile.
  - `POST /api/v1/abdm/link-care-context`: Associates encounter bundles to patient ABHA records.

### 3. WhatsApp & Telephony Ingestion Gateway (`webhook_handler.py`)
- `POST /api/v1/webhook/whatsapp`:
  - Accepts incoming Twilio/Meta WhatsApp webhook payloads.
  - Ingests image/audio attachments, executes OCR/Voice scribe pipeline.
  - Formats clinical output and auto-replies to doctor/patient with vernacular dosage card and summary link.

### 4. Air-Gapped DPDP Enterprise Appliance (`appliance_config.py` / `Dockerfile.onprem`)
- Standalone packaging with offline SQLite FTS5 fallback, local vector index, and tokenized DPDP data purge handlers for zero-cloud intranet deployment.
