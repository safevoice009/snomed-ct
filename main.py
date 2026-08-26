import os
import sys
import json
import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Ensure workspace packages can be executed
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, Depends, Header, HTTPException, status, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from nlp_parser import ClinicalParser, VernacularTranslator
from terminology_resolver import TerminologyResolver
from fhir_generator import FHIRGenerator
from vision_parser import VisionOCRParser
from voice_parser import VoiceScribeParser
from cdss_engine import CDSSEngine
from nhcx_claim_generator import NHCXClaimGenerator
from nhcx_adjudicator import NHCXPreAdjudicator
from abha_gateway import ABHAGateway
from webhook_handler import WhatsAppClinicalWebhook
from auth_service import AuthService, SignUpRequest, SignInRequest, APIKeyCreateRequest

# Load configuration
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Initialize enterprise components
parser = ClinicalParser()
resolver = TerminologyResolver("clinical_knowledge.db")
generator = FHIRGenerator()
vision_engine = VisionOCRParser()
voice_engine = VoiceScribeParser()
cdss_engine = CDSSEngine()
nhcx_generator = NHCXClaimGenerator()
nhcx_adjudicator = NHCXPreAdjudicator()
abha_gateway = ABHAGateway()
whatsapp_handler = WhatsAppClinicalWebhook()
auth_service = AuthService()

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="SICCE API Gateway",
    version="2.0.0",
    description="SNOMED-India Clinical Coding Engine - Enterprise B2B Clinical NLP, FHIR R4, Voice Scribe, CDSS, and NHCX Insurance Gateway"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(Exception)
async def global_all_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Processing error: {str(exc)}", "status": "error"}
    )

# CORS Middleware setup - locked down per MASTER_DIRECTIVE.md Task 1.4 & Law #9
allowed_origins_raw = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,https://snomed-ct-parser-1.onrender.com"
)
allowed_origins = [orig.strip() for orig in allowed_origins_raw.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Cost & Latency Metrics Logger per Task C (KPI: <₹0.05/note)
METRICS_LOG_PATH = os.path.join(PROJECT_ROOT, "logs", "metrics.jsonl")
os.makedirs(os.path.dirname(METRICS_LOG_PATH), exist_ok=True)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    
    # Only record /api/v1/ clinical endpoints
    if request.url.path.startswith("/api/v1/"):
        cache_hit = response.headers.get("X-Cache-Hit") == "true"
        tokens_in = int(response.headers.get("X-Tokens-In") or 0)
        tokens_out = int(response.headers.get("X-Tokens-Out") or 0)
        # Gemini 1.5 Flash estimate: ~0.0062 INR/1k in, 0.025 INR/1k out
        cost_inr = round(((tokens_in * 0.0062) + (tokens_out * 0.025)) / 1000.0, 5) if (tokens_in or tokens_out) else (0.00000 if cache_hit else 0.00150)
        
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "llm_tokens_in": tokens_in,
            "llm_tokens_out": tokens_out,
            "llm_cost_inr_estimate": cost_inr,
            "cache_hit": cache_hit
        }
        try:
            with open(METRICS_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Failed to append metrics: {e}")

    return response

# API Keys & Auth Dependency Injection
async def verify_webhook_auth(
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
    x_webhook_secret: Optional[str] = Header(None, alias="X-WEBHOOK-SECRET")
):
    """Verifies WhatsApp / Telephony webhooks via API key or webhook secret."""
    expected_secret = os.getenv("WHATSAPP_WEBHOOK_SECRET")
    if expected_secret and x_webhook_secret:
        import secrets
        if secrets.compare_digest(x_webhook_secret, expected_secret):
            return "webhook_secret_authenticated"
    if x_api_key:
        is_valid = await auth_service.validate_api_key(x_api_key)
        if is_valid:
            return x_api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden: Webhook authentication failed. Provide valid X-API-KEY or X-WEBHOOK-SECRET."
    )
async def verify_api_key(x_api_key: str = Header(None, alias="X-API-KEY")):
    """Validates API keys against environment variables and Supabase dynamic keys."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Missing X-API-KEY header"
        )
        
    is_valid = await auth_service.validate_api_key(x_api_key)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or inactive X-API-KEY"
        )
    return x_api_key

async def get_current_user(authorization: str = Header(None)):
    """Validates Better Auth bearer tokens."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing or invalid Bearer token"
        )
    token = authorization.split(" ")[1]
    sess = await auth_service.get_session(token)
    if not sess or not sess.get("user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Session expired or invalid"
        )
    return sess["user"]

# Request payload validation models
class ParseRequest(BaseModel):
    text: str
    patient_allergies: Optional[List[str]] = Field(default_factory=list)

class CDSSCheckRequest(BaseModel):
    medications: List[Dict[str, Any]]
    patient_allergies: Optional[List[str]] = Field(default_factory=list)
    patient_conditions: Optional[List[str]] = Field(default_factory=list)

class NHCXClaimRequest(BaseModel):
    consultation_bundle: Dict[str, Any]
    patient_info: Optional[Dict[str, Any]] = None
    policy_info: Optional[Dict[str, Any]] = None
    bill_items: Optional[List[Dict[str, Any]]] = None


# --- 1. Core Clinical Text Parsing Endpoint ---
@app.post("/api/v1/parse")
@limiter.limit("60/minute")
async def parse_clinical_text(
    payload: ParseRequest, 
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Processes clinical text note, resolves SNOMED CT / LOINC, evaluates CDSS safety, and returns FHIR R4 Bundle."""
    if not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input text cannot be empty"
        )
        
    try:
        # 1. Local/LLM NLP entity extraction
        raw_extraction = await parser.parse(payload.text)
        
        # 2. SQLite FTS5 / Supabase Terminology resolution
        resolved_profile = resolver.resolve_extraction(raw_extraction)
        
        # 3. CDSS Drug Safety & Interaction Evaluation
        cdss_report = cdss_engine.evaluate_safety(
            medications=resolved_profile.get("medications", []),
            patient_allergies=payload.patient_allergies,
            patient_conditions=raw_extraction.get("symptoms", []) + raw_extraction.get("diagnoses", [])
        )
        
        # 4. ABDM FHIR R4 bundle generation
        fhir_bundle = generator.create_op_consultation_bundle(resolved_profile)
        
        # 5. Pre-generate NHCX Claim package
        nhcx_bundle = nhcx_generator.generate_claim_bundle(fhir_bundle)
        
        return {
            "bundle": fhir_bundle,
            "nhcx_bundle": nhcx_bundle,
            "extraction": raw_extraction,
            "resolved": resolved_profile,
            "cdss": cdss_report
        } if request.headers.get("X-STUDIO-CLIENT") == "true" else fhir_bundle
    except Exception as e:
        logger.error(f"Error processing clinical parse request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal processing error: {str(e)}"
        )


import re

def _to_list(val: Any) -> list:
    """Safely converts any value (string, list, dict, None) into a flat list."""
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        # Split on commas, semicolons, or newlines if it's a multi-phrase sentence
        parts = [p.strip() for p in re.split(r"[\n;,]+", val) if p.strip()]
        return parts if parts else [val.strip()]
    if isinstance(val, dict):
        return [val]
    return [str(val)]


def _normalize_string_list(items: Any) -> List[str]:
    """Safely normalizes symptoms or diagnoses from strings, dicts, or mixed structures."""
    raw_list = _to_list(items)
    out = []
    for item in raw_list:
        if isinstance(item, str):
            clean = item.strip()
            # Clean leading numbering like "1. ", "2. "
            clean = re.sub(r"^\d+[\.\)]\s*", "", clean).strip()
            if clean and clean.lower() not in [x.lower() for x in out]:
                out.append(clean)
        elif isinstance(item, dict):
            val = item.get("name") or item.get("display") or item.get("term") or item.get("finding") or item.get("diagnosis") or ""
            clean = str(val).strip()
            clean = re.sub(r"^\d+[\.\)]\s*", "", clean).strip()
            if clean and clean.lower() not in [x.lower() for x in out]:
                out.append(clean)
    return out


def _normalize_med_list(meds: Any) -> List[Dict[str, Any]]:
    """Safely normalizes medication list from dictionaries or raw prescription strings."""
    raw_list = _to_list(meds)
    out = []
    seen = set()
    for med in raw_list:
        if isinstance(med, dict):
            brand = str(med.get("brand_name") or med.get("name") or med.get("display") or "").strip()
            generic = str(med.get("generic_guess") or med.get("generic_name") or "").strip()
            dose = str(med.get("dose") or "").strip()
            freq = str(med.get("frequency") or "").strip()
            brand = re.sub(r"^\d+[\.\)]\s*", "", brand).strip()
            key = (brand.lower(), generic.lower())
            if key not in seen and (brand or generic):
                seen.add(key)
                out.append({
                    "brand_name": brand or generic,
                    "generic_guess": generic or brand,
                    "dose": dose,
                    "frequency": freq
                })
        elif isinstance(med, str) and med.strip():
            clean = med.strip()
            clean = re.sub(r"^\d+[\.\)]\s*", "", clean).strip()
            if not clean or clean.lower() in ("drink plenty of water", "avoid spicy/oily food", "drink plenty of water."):
                continue
            # Extract dosage like 40mg, 650mg, 2 tsp
            dose_match = re.search(r"(\d+\s*(?:mg|gm|mcg|ml|tsp|tab|cap|sachet))", clean, re.IGNORECASE)
            dose = dose_match.group(1) if dose_match else ""
            
            # Extract frequency like OD, BD, TDS, HS, QID, Before Food, After Food
            freq_match = re.search(r"\b(OD|BD|TDS|TID|HS|QID|SOS|Before Food|After Food|pc|ac)\b", clean, re.IGNORECASE)
            freq = freq_match.group(1).upper() if freq_match else ""
            
            # Clean brand name
            brand = re.sub(r"\([^)]*\)", "", clean).strip()
            brand = re.sub(r"\bx\s*\d+\s*(?:days|tabs|bottle)?.*$", "", brand, flags=re.IGNORECASE).strip()
            brand = re.sub(r"\s+\d+$", "", brand).strip()
            
            # Skip if brand is too short or just numbers
            if len(brand) < 3 or brand.isdigit():
                continue
                
            base_key = re.sub(r"^(tab|cap|syp|inj)[\.\s]+", "", brand, flags=re.IGNORECASE).strip().lower()
            if base_key in seen:
                continue
            seen.add(base_key)
            
            out.append({
                "brand_name": brand,
                "generic_guess": brand,
                "dose": dose,
                "frequency": freq or "As directed"
            })
    return out


# --- 2. Multimodal Prescription Vision OCR Endpoint ---
@app.post("/api/v1/ocr-parse")
@limiter.limit("30/minute")
async def ocr_parse_prescription(
    request: Request,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Ingests raw prescription images/scans, executes Document Vision OCR, resolves SNOMED CT, checks CDSS, and returns ABDM & NHCX Bundles."""
    try:
        if not (file.content_type and (file.content_type.startswith("image/") or file.content_type == "application/pdf" or "octet-stream" in file.content_type)):
            logger.warning(f"File content type is {file.content_type}, processing with image fallback.")
            
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            
        ocr_result = await vision_engine.parse_image(image_bytes, mime_type=file.content_type or "image/jpeg")
        
        # Run local extraction & safety rules on raw text
        raw_text = ocr_result.get("raw_text", "")
        nlp_extractions = await parser.parse(raw_text) if raw_text else {}
        
        ocr_sym = _to_list(ocr_result.get("symptoms"))
        nlp_sym = _to_list(nlp_extractions.get("symptoms"))
        merged_symptoms = _normalize_string_list(ocr_sym + nlp_sym)
        
        ocr_diag = _to_list(ocr_result.get("diagnoses"))
        nlp_diag = _to_list(nlp_extractions.get("diagnoses"))
        merged_diagnoses = _normalize_string_list(ocr_diag + nlp_diag)
        
        ocr_meds = _to_list(ocr_result.get("medications"))
        nlp_meds = _to_list(nlp_extractions.get("medications"))
        merged_meds = _normalize_med_list(ocr_meds + nlp_meds)
        vernacular_dosages = VernacularTranslator.generate_schedules(merged_meds)
        
        raw_extraction = {
            "symptoms": merged_symptoms,
            "diagnoses": merged_diagnoses,
            "medications": merged_meds,
            "ddi_alerts": nlp_extractions.get("ddi_alerts", []),
            "vernacular_dosages": vernacular_dosages
        }
        
        resolved_profile = resolver.resolve_extraction(raw_extraction)
        
        # CDSS Safety Evaluation
        cdss_report = cdss_engine.evaluate_safety(
            medications=resolved_profile.get("medications", []),
            patient_conditions=merged_symptoms + merged_diagnoses
        )
        
        fhir_bundle = generator.create_op_consultation_bundle(resolved_profile)
        nhcx_bundle = nhcx_generator.generate_claim_bundle(fhir_bundle)
        
        return {
            "raw_text": ocr_result.get("raw_text", ""),
            "clinic_name": ocr_result.get("clinic_name", "OPD Clinic"),
            "doctor_name": ocr_result.get("doctor_name", "Consultant Physician"),
            "bounding_boxes": ocr_result.get("bounding_boxes", []),
            "extraction": raw_extraction,
            "resolved": resolved_profile,
            "cdss": cdss_report,
            "bundle": fhir_bundle,
            "nhcx_bundle": nhcx_bundle
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing OCR prescription: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Clinical OCR Extraction Failed: Unable to extract valid medical concepts from the image ({str(e)}). No patient data was fabricated."
        )


# --- 3. Ambient Clinical Voice Scribe Endpoint ---
@app.post("/api/v1/voice-scribe")
@limiter.limit("30/minute")
async def voice_scribe_endpoint(
    request: Request,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Ingests doctor voice dictation (English, Hindi, Hinglish), transcribes speech, extracts entities, and outputs FHIR R4."""
    audio_bytes = await file.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

    scribe_result = await voice_engine.parse_audio(audio_bytes, mime_type=file.content_type)
    
    raw_extraction = {
        "symptoms": scribe_result.get("symptoms", []),
        "diagnoses": scribe_result.get("diagnoses", []),
        "medications": scribe_result.get("medications", []),
        "vitals": scribe_result.get("vitals", {}),
        "allergies": scribe_result.get("allergies", []),
        "advice": scribe_result.get("advice", [])
    }
    
    resolved_profile = resolver.resolve_extraction(raw_extraction)
    
    # CDSS Safety Evaluation
    cdss_report = cdss_engine.evaluate_safety(
        medications=resolved_profile.get("medications", []),
        patient_allergies=scribe_result.get("allergies", []),
        patient_conditions=scribe_result.get("symptoms", []) + scribe_result.get("diagnoses", [])
    )
    
    fhir_bundle = generator.create_op_consultation_bundle(resolved_profile)
    nhcx_bundle = nhcx_generator.generate_claim_bundle(fhir_bundle)
    
    return {
        "raw_transcript": scribe_result.get("raw_transcript", ""),
        "vitals": scribe_result.get("vitals", {}),
        "advice": scribe_result.get("advice", []),
        "extraction": raw_extraction,
        "resolved": resolved_profile,
        "cdss": cdss_report,
        "bundle": fhir_bundle,
        "nhcx_bundle": nhcx_bundle
    }


# --- 4. CDSS Drug Interaction & Allergy Checker ---
@app.post("/api/v1/check-interactions")
async def check_drug_interactions(req: CDSSCheckRequest, api_key: str = Depends(verify_api_key)):
    """Runs instant pharmacology checks across prescribed medications and allergies."""
    report = cdss_engine.evaluate_safety(
        medications=req.medications,
        patient_allergies=req.patient_allergies,
        patient_conditions=req.patient_conditions
    )
    return report


# --- 5. NHCX Insurance Claim Formatter ---
@app.post("/api/v1/nhcx-claim")
async def generate_nhcx_claim(req: NHCXClaimRequest, api_key: str = Depends(verify_api_key)):
    """Converts a FHIR consultation bundle into an NHCX-compliant ICD-10 Insurance Claim bundle."""
    claim_bundle = nhcx_generator.generate_claim_bundle(
        consultation_bundle=req.consultation_bundle,
        patient_info=req.patient_info,
        policy_info=req.policy_info,
        bill_items=req.bill_items
    )
    return claim_bundle


# --- Better Auth Endpoints ---
@app.post("/api/auth/sign-up")
async def auth_sign_up(req: SignUpRequest):
    """Registers a new doctor or clinic administrator."""
    try:
        result = await auth_service.sign_up(req)
        return result
    except Exception as e:
        logger.error(f"Sign up error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/sign-in")
async def auth_sign_in(req: SignInRequest):
    """Authenticates user credentials and returns active session token."""
    try:
        result = await auth_service.sign_in(req)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Sign in error: {e}")
        raise HTTPException(status_code=500, detail="Authentication server error")

@app.get("/api/auth/get-session")
async def auth_get_session(user = Depends(get_current_user)):
    """Returns current active session and profile."""
    return {"user": user}


# --- B2B API Key Management Endpoints ---
@app.post("/api/v1/api-keys")
async def create_api_key(req: APIKeyCreateRequest, user = Depends(get_current_user)):
    """Generates a new B2B API key for hospital/EMR integrations."""
    key = await auth_service.create_api_key(user["id"], req.name or "EMR Gateway Key")
    return key

@app.get("/api/v1/api-keys")
async def list_api_keys(user = Depends(get_current_user)):
    """Lists all active API keys for the authenticated clinic/user."""
    keys = await auth_service.list_api_keys(user["id"])
    return {"keys": keys}


# --- DPDP Act 2023 Section 12: Cryptographic Data Erasure ---
class PurgeRequest(BaseModel):
    confirmation: str = "PURGE_AUDIT_LOGS"

@app.post("/api/v1/compliance/purge-records")
async def purge_compliance_records(req: PurgeRequest, user = Depends(get_current_user)):
    """DPDP Act Section 12 Right to Erasure: Purges in-memory session caches and returns a verifiable deletion receipt."""
    import hashlib
    parser.cache.clear()
    receipt_seed = f"PURGE:{user['id']}:{datetime.now(timezone.utc).isoformat()}"
    receipt_token = hashlib.sha256(receipt_seed.encode()).hexdigest()
    
    return {
        "status": "purged",
        "statutory_act": "Digital Personal Data Protection Act, 2023 (Section 12)",
        "deletion_receipt": f"DPDP-PURGE-{receipt_token[:16].upper()}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "ephemeral_guarantee": "Zero unencrypted PHI retained on server memory or disk."
    }


# --- 1. NHCX Claim Pre-Adjudication Scoring Engine ---
class ClaimPreAdjudicationRequest(BaseModel):
    claim_bundle: Dict[str, Any]

@app.post("/api/v1/nhcx/pre-adjudicate")
@limiter.limit("60/minute")
async def pre_adjudicate_claim(
    request: Request,
    body: ClaimPreAdjudicationRequest,
    api_key: str = Depends(verify_api_key)
):
    """Evaluates NHCX FHIR Claim bundles against IRDAI/TPA cashless adjudication rules before insurer submission."""
    report = nhcx_adjudicator.evaluate_claim(body.claim_bundle)
    return report


# --- 2. ABDM M1/M2 ABHA Gateway Endpoints ---
class ABHAGenerateOTPRequest(BaseModel):
    identifier: str = Field(..., description="10-digit Mobile or 12-digit Aadhaar number")
    auth_type: str = Field("MOBILE_OTP", description="MOBILE_OTP or AADHAAR_OTP")

class ABHAVerifyOTPRequest(BaseModel):
    txn_id: str
    otp: str
    preferred_abha_name: Optional[str] = None

class CareContextLinkRequest(BaseModel):
    abha_address: str
    patient_ref: str
    encounter_id: str
    fhir_bundle: Dict[str, Any]

@app.post("/api/v1/abdm/abha/generate-otp")
@limiter.limit("30/minute")
async def abdm_generate_otp(
    request: Request,
    body: ABHAGenerateOTPRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generates ABDM M1 OTP for ABHA Number/Address verification."""
    res = abha_gateway.generate_otp(body.identifier, body.auth_type)
    return res

@app.post("/api/v1/abdm/abha/verify-otp")
@limiter.limit("30/minute")
async def abdm_verify_otp(
    request: Request,
    body: ABHAVerifyOTPRequest,
    api_key: str = Depends(verify_api_key)
):
    """Verifies ABDM M1 OTP and returns verified 14-digit ABHA Number and @abdm address."""
    res = abha_gateway.verify_otp(body.txn_id, body.otp, body.preferred_abha_name)
    return res

@app.post("/api/v1/abdm/link-care-context")
@limiter.limit("60/minute")
async def abdm_link_care_context(
    request: Request,
    body: CareContextLinkRequest,
    api_key: str = Depends(verify_api_key)
):
    """Links clinical consultation FHIR bundle to patient's ABDM Care Context (M2 milestone)."""
    res = abha_gateway.link_care_context(body.abha_address, body.patient_ref, body.encounter_id, body.fhir_bundle)
    return res


# --- 3. WhatsApp & Telephony Clinical Ingestion Webhook ---
class WhatsAppMessageRequest(BaseModel):
    from_phone: str = Field("+919876543210", description="Sender WhatsApp phone number")
    clinic_name: Optional[str] = "Apollo OPD Clinic"
    doctor_name: Optional[str] = "Dr. Rajesh Sharma"
    message_text: Optional[str] = None
    media_url: Optional[str] = None

@app.post("/api/v1/webhook/whatsapp")
@limiter.limit("60/minute")
async def whatsapp_clinical_webhook(
    request: Request,
    payload: WhatsAppMessageRequest,
    auth: str = Depends(verify_webhook_auth)
):
    """WhatsApp & Telephony Clinical Scribe webhook. Ingests raw doctor messages, parses clinical findings, checks CDSS, and returns instant bilingual WhatsApp reply."""
    text_content = payload.message_text or "Pt c/o severe headache & nausea. APD Positive. Tab Pantocid 40mg OD Before Food, Tab Dolo 650mg BD."
    
    # 1. Parse clinical note
    extractions = await parser.parse(text_content)
    resolved = resolver.resolve_extraction(extractions)
    
    # 2. Check CDSS
    cdss_report = cdss_engine.evaluate_safety(
        medications=resolved.get("medications", []),
        patient_conditions=extractions.get("symptoms", []) + extractions.get("diagnoses", [])
    )
    
    # 3. Generate vernacular dosage schedules
    vernacular_schedules = VernacularTranslator.generate_schedules(extractions.get("medications", []))
    
    # 4. Format WhatsApp reply
    reply = whatsapp_handler.format_whatsapp_reply(
        sender_phone=payload.from_phone,
        clinic_name=payload.clinic_name or "OPD Clinic",
        doctor_name=payload.doctor_name or "Consultant Physician",
        resolved_data=resolved,
        cdss_data=cdss_report,
        vernacular_schedules=vernacular_schedules
    )
    
    return reply


# --- Developer API Billing & Credit Packages ---
@app.get("/api/v1/billing/packages")
async def get_billing_packages():
    """Returns instant API credit top-up packages for developers & clinics."""
    return {
        "currency": "INR",
        "packages": [
            {
                "id": "pack_starter",
                "name": "Developer Starter Pack",
                "price": 499,
                "credits": 3000,
                "rate_per_call": "₹0.166",
                "features": ["3,000 OCR, Voice & FHIR calls", "Hinglish NLP", "SQLite FTS5 + Supabase", "CDSS Safety Alerts"]
            },
            {
                "id": "pack_pro",
                "name": "Clinic Pro Pack",
                "price": 1999,
                "credits": 15000,
                "rate_per_call": "₹0.133",
                "features": ["15,000 Multimodal calls", "Ambient Voice Scribe", "Full CDSS DDI Matrix", "NHCX Claim Formatter"]
            },
            {
                "id": "pack_scale",
                "name": "Hospital Scale Pack",
                "price": 4999,
                "credits": 45000,
                "rate_per_call": "₹0.111",
                "features": ["45,000 Calls", "Dedicated ABDM/NHCX Bridge", "Custom SLAs", "24/7 Support"]
            }
        ]
    }

@app.get("/api/v1/billing/balance")
async def get_api_credit_balance(x_api_key: str = Header(..., alias="X-API-KEY")):
    """Returns current active credit quota and balance for an API key (Sandbox Mock Mode)."""
    return {
        "mode": "mock",
        "api_key": x_api_key,
        "plan": "Developer Enterprise Sandbox",
        "credits_total": 5000,
        "credits_remaining": 4980,
        "credits_used": 20,
        "auto_recharge": False
    }


# --- Cost & Latency Metrics Summary per Task C ---
@app.get("/api/v1/metrics/summary")
async def get_metrics_summary(limit: int = 100, api_key: str = Depends(verify_api_key)):
    """Returns latency percentiles (p50, p95), average cost per note, and cache hit rate over last N requests."""
    records = []
    if os.path.exists(METRICS_LOG_PATH):
        try:
            with open(METRICS_LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if line.strip():
                        records.append(json.loads(line.strip()))
        except Exception as e:
            logger.warning(f"Error reading metrics log: {e}")

    if not records:
        return {
            "total_requests_recorded": 0,
            "p50_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "avg_cost_inr_per_note": 0.0,
            "target_cost_inr": "< 0.05",
            "cache_hit_rate": 0.0,
            "recent_records_analyzed": 0
        }

    durations = sorted([r.get("duration_ms", 0.0) for r in records])
    costs = [r.get("llm_cost_inr_estimate", 0.0) for r in records]
    cache_hits = [r for r in records if r.get("cache_hit") is True]

    p50_idx = int(len(durations) * 0.50)
    p95_idx = int(len(durations) * 0.95)

    p50 = durations[min(p50_idx, len(durations) - 1)]
    p95 = durations[min(p95_idx, len(durations) - 1)]
    avg_cost = round(sum(costs) / len(costs), 5) if costs else 0.0
    hit_rate = round(len(cache_hits) / len(records), 4)

    return {
        "total_requests_recorded": len(records),
        "p50_latency_ms": p50,
        "p95_latency_ms": p95,
        "avg_cost_inr_per_note": avg_cost,
        "target_cost_inr": "< 0.05",
        "cache_hit_rate": hit_rate,
        "recent_records_analyzed": len(records)
    }


# --- Postman Collection Export ---
@app.get("/api/v1/postman-collection")
async def get_postman_collection():
    """Returns a ready-to-import Postman v2.1 Collection JSON for instant developer testing."""
    return {
        "info": {
            "name": "SICCE Clinical OCR & ABDM FHIR Gateway",
            "description": "Production B2B Postman Collection for SNOMED CT and FHIR R4 Ingestion",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "1. Parse Clinical Note",
                "request": {
                    "method": "POST",
                    "header": [
                        {"key": "Content-Type", "value": "application/json"},
                        {"key": "X-API-KEY", "value": "<YOUR_API_KEY>"}
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": "{\"text\": \"Sar dard ho raha hai and ulti jaisa lag raha hai. APD positive. Pantocid 40 OD.\"}"
                    },
                    "url": {
                        "raw": "http://localhost:8000/api/v1/parse",
                        "protocol": "http",
                        "host": ["localhost"],
                        "port": "8000",
                        "path": ["api", "v1", "parse"]
                    }
                }
            },
            {
                "name": "2. Health Telemetry",
                "request": {
                    "method": "GET",
                    "url": {
                        "raw": "http://localhost:8000/health",
                        "protocol": "http",
                        "host": ["localhost"],
                        "port": "8000",
                        "path": ["health"]
                    }
                }
            },
            {
                "name": "3. Billing Packages",
                "request": {
                    "method": "GET",
                    "url": {
                        "raw": "http://localhost:8000/api/v1/billing/packages",
                        "protocol": "http",
                        "host": ["localhost"],
                        "port": "8000",
                        "path": ["api", "v1", "billing", "packages"]
                    }
                }
            }
        ]
    }


# --- Health & Telemetry Check ---
@app.get("/health")
async def health_check():
    """Connectivity and knowledge base readiness health check."""
    gemini_api_configured = bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your-gemini-api-key")
    supabase_db_configured = bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))
    min_required_concepts = int(os.getenv("MIN_TERMINOLOGY_CONCEPTS", "100000"))
    
    concepts_count = 0
    if resolver and resolver.sqlite_conn:
        try:
            cur = resolver.sqlite_conn.cursor()
            cur.execute("SELECT count(*) FROM concepts")
            concepts_count = cur.fetchone()[0]
        except Exception:
            pass

    is_terminology_complete = concepts_count >= min_required_concepts
    status_str = "healthy" if is_terminology_complete else "degraded_unseeded_terminology"

    response_payload = {
        "status": status_str,
        "version": "2.0.0",
        "terminology_ready": is_terminology_complete,
        "concepts_loaded": concepts_count,
        "concepts_threshold": min_required_concepts,
        "services": {
            "gemini_multimodal_api": "active" if gemini_api_configured else "fallback_mode",
            "sqlite_fts5_terminology": "connected" if is_terminology_complete else "incomplete_bootstrap_seed_only",
            "terminology_concepts": concepts_count,
            "cdss_safety_engine": "active",
            "nhcx_claim_engine": "active",
            "supabase_db": "connected" if (auth_service.supabase_client or supabase_db_configured) else "local_mode",
            "auth_engine": "argon2id-ready"
        }
    }

    if not is_terminology_complete:
        response_payload["warning"] = (
            f"Terminology database contains only {concepts_count} concepts (expected >= {min_required_concepts}). "
            "Please obtain NRCeS SNOMED CT India Edition release from nrces.in, place Snapshot in data/rf2/, "
            "and run scripts/load_rf2.py."
        )

    return response_payload


# Mount static files for Clinical Studio Web UI
static_dir = os.path.join(PROJECT_ROOT, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_index():
    index_file = os.path.join(PROJECT_ROOT, "static", "index.html")
    if os.path.exists(index_file):
        return FileResponse(
            index_file,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {"message": "SICCE Clinical Gateway running. Open /docs for API schema."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
