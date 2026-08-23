import os
import json
import base64
import logging
from typing import Dict, Any, List, Optional
import io
import requests

logger = logging.getLogger("vision_parser")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

class VisionOCRParser:
    """High-speed Resilient Multimodal Clinical Vision Engine."""
    
    def __init__(self):
        self.model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        
    def _optimize_image(self, image_bytes: bytes) -> tuple[bytes, str]:
        """Compresses image to max 960px JPEG for lightning fast cloud inference."""
        if not HAS_PIL:
            return image_bytes, "image/jpeg"
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            max_size = 960
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=75, optimize=True)
            return out.getvalue(), "image/jpeg"
        except Exception as e:
            logger.warning(f"Image optimization fallback: {e}")
            return image_bytes, "image/jpeg"

    async def parse_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """Parses prescription image into structured clinical entities, OCR text, and bounding boxes."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY is missing for Vision OCR.")
            return self._fallback_response()
            
        opt_bytes, opt_mime = self._optimize_image(image_bytes)
        b64_data = base64.b64encode(opt_bytes).decode("utf-8")
        
        models_to_try = [
            os.getenv("LLM_MODEL", "gemini-2.5-flash"),
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-1.5-flash"
        ]
        
        system_instruction = (
            "You are an expert Clinical OCR and Document AI engine specialized in reading handwritten and printed Indian prescriptions.\n"
            "Extract the doctor's handwriting, clinic details, patient info, complaints, diagnoses, and medication lines with utmost fidelity.\n"
            "Return a pure JSON object with exactly these keys:\n"
            "1. 'raw_text': verbatim transcription of the entire prescription document including doctor's notes and Rx lines.\n"
            "2. 'clinic_name': clinic or hospital name (e.g. 'Apollo Clinic, Pune', 'Max Hospital').\n"
            "3. 'doctor_name': doctor name with qualification (e.g. 'Dr. Rajesh Sharma, MD').\n"
            "4. 'symptoms': list of chief complaints/symptoms (e.g. ['Severe headache', 'Nausea', 'Acidic taste', 'Loss of appetite', 'Fever', 'Cough']).\n"
            "5. 'diagnoses': list of diagnoses (e.g. ['Acid Peptic Disease (Gastritis)', 'Migraine secondary to acidity', 'Hypertension']).\n"
            "6. 'medications': list of objects with:\n"
            "   - 'brand_name': prescribed brand or formulation (e.g. 'Tab Pantocid 40', 'Tab Dolo 650', 'Syp Mucaine')\n"
            "   - 'generic_guess': active salt/molecule (e.g. 'Pantoprazole', 'Paracetamol', 'Oxetacaine')\n"
            "   - 'dose': dosage strength (e.g. '40mg', '650mg', '2 tsp')\n"
            "   - 'frequency': schedule instruction (e.g. 'OD Before Food', 'BD After Food', 'TDS After Food')\n"
            "7. 'bounding_boxes': list of visual bounding boxes [ymin, xmin, ymax, xmax] (0-1000 scale) with 'label' ('CLINIC_ENTITY', 'PATIENT_DEMOGRAPHICS', 'DIAGNOSIS', 'MEDICATION_ARRAY') and 'confidence' (0.95-0.99)."
        )
        
        prompt = f"{system_instruction}\n\nPerform complete Document OCR and Clinical Entity Extraction on this image."
        
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": opt_mime,
                                    "data": b64_data
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.1
                }
            }
            
            try:
                import asyncio
                def _post():
                    return requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=28)
                    
                res = await asyncio.to_thread(_post)
                
                if res.status_code == 200:
                    data = res.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(content)
                    logger.info(f"Vision OCR successfully extracted text using model: {model}")
                    return {
                        "raw_text": parsed.get("raw_text", ""),
                        "clinic_name": parsed.get("clinic_name", "OPD Clinic"),
                        "doctor_name": parsed.get("doctor_name", "Consultant Physician"),
                        "symptoms": parsed.get("symptoms", []),
                        "diagnoses": parsed.get("diagnoses", []),
                        "medications": parsed.get("medications", []),
                        "bounding_boxes": parsed.get("bounding_boxes", [])
                    }
                else:
                    logger.warning(f"Vision model {model} returned status {res.status_code}: {res.text[:200]}")
            except Exception as e:
                logger.warning(f"Vision OCR model {model} attempt failed: {e}")
                
        return self._fallback_response()

    def _fallback_response(self, error_msg: str = "OCR Extraction Failed") -> Dict[str, Any]:
        return {
            "raw_text": "",
            "clinic_name": "",
            "doctor_name": "",
            "symptoms": [],
            "diagnoses": [],
            "medications": [],
            "bounding_boxes": [],
            "error": error_msg
        }
