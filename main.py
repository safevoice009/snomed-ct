import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any

# Ensure workspace packages can be executed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, Header, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from dotenv import load_dotenv

from nlp_parser import ClinicalParser
from terminology_resolver import TerminologyResolver
from fhir_generator import FHIRGenerator

# Load configuration
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Initialize components
parser = ClinicalParser()
resolver = TerminologyResolver("mock_snomed_db.json")
generator = FHIRGenerator()

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="SICCE API Gateway",
    version="1.0.0",
    description="SNOMED-India Clinical Coding Engine - Secure B2B Clinical NLP & FHIR Translation Service"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys Configuration
API_KEYS = set(os.getenv("API_KEYS", "test-dev-key").split(","))

def verify_api_key(x_api_key: str = Header(None, alias="X-API-KEY")):
    """Dependency injection to validate API key headers."""
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or missing X-API-KEY header"
        )
    return x_api_key

# Request payload validation
class ParseRequest(BaseModel):
    text: str

@app.post("/api/v1/parse")
@limiter.limit("60/minute")
async def parse_clinical_text(
    payload: ParseRequest, 
    request: Request, # required by slowapi
    api_key: str = Depends(verify_api_key)
):
    """Processes clinical text input and returns a validated FHIR R4 Bundle."""
    if not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input text cannot be empty"
        )
        
    try:
        # 1. Local/LLM NLP entity extraction
        raw_extraction = await parser.parse(payload.text)
        
        # 2. Terminology resolution (Synonyms/Fuzzy SNOMED CT lookup)
        resolved_profile = resolver.resolve_extraction(raw_extraction)
        
        # 3. ABDM FHIR bundle generation
        fhir_bundle = generator.create_op_consultation_bundle(resolved_profile)
        
        return fhir_bundle
    except Exception as e:
        logger.error(f"Error processing clinical parse request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal processing error: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Connectivity health check for backend services."""
    gemini_api_configured = bool(os.getenv("GEMINI_API_KEY"))
    supabase_db_configured = bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "gemini_api": "configured" if gemini_api_configured else "fallback_mode",
            "supabase_db": "configured" if supabase_db_configured else "local_mock_mode"
        }
    }


async def run_cli_tests():
    """Runs a dry CLI translation test case loop."""
    print("Running local CLI pipeline demonstration...")
    test_cases = [
        "Pt c/o loose motion x 3 days, AP+, Dolo 650 BD",
        "Sar dard ho raha hai and ulti jaisa lag raha hai. APD positive. Pantocid 40 OD.",
        "Pt has h/o Amavata. c/o SOBOE on walking. pedal edema + B/L. Rx Lasix 40mg BD."
    ]
    for case in test_cases:
        print("="*60)
        print(f"INPUT NOTE: \"{case}\"")
        print("="*60)
        
        raw_extraction = await parser.parse(case)
        print("\n[Step 1: NLP Entity Extraction]")
        print(json.dumps(raw_extraction, indent=2))
        
        resolved_profile = resolver.resolve_extraction(raw_extraction)
        print("\n[Step 2: SNOMED CT / LOINC Code Mapping]")
        print(json.dumps(resolved_profile, indent=2))
        
        fhir_bundle = generator.create_op_consultation_bundle(resolved_profile)
        print("\n[Step 3: Generated ABDM FHIR R4 OPConsultation Bundle]")
        print(json.dumps(fhir_bundle, indent=2))
        print("="*60 + "\n")


if __name__ == "__main__":
    if "--cli" in sys.argv or "--test" in sys.argv:
        asyncio.run(run_cli_tests())
    else:
        import uvicorn
        port = int(os.getenv("PORT", 8000))
        uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
