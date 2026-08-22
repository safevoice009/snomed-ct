import os
import json
import base64
import logging
from typing import Dict, Any, List, Optional
import httpx
import io

logger = logging.getLogger("vision_parser")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

class VisionOCRParser:
    """High-speed Multimodal Clinical Vision Engine for Handwritten & Printed Prescriptions."""
    
    def __init__(self):
        self.model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        
    def _optimize_image(self, image_bytes: bytes) -> tuple[bytes, str]:
        """Compresses image to max 1280px for sub-second vision inference."""
        if not HAS_PIL:
            return image_bytes, "image/jpeg"
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Max width/height 1280
            max_size = 1280
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=82, optimize=True)
            return out.getvalue(), "image/jpeg"
        except Exception as e:
            logger.warning(f"Image optimization fallback: {e}")
            return image_bytes, "image/jpeg"

    async def parse_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """Parses prescription image into structured clinical entities, OCR text, and bounding boxes."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY is missing for Vision OCR.")
            return {
                "raw_text": "",
                "clinic_name": "OPD Clinic",
                "doctor_name": "Consultant Physician",
                "symptoms": [],
                "diagnoses": [],
                "medications": [],
                "bounding_boxes": []
            }
            
        opt_bytes, opt_mime = self._optimize_image(image_bytes)
        b64_data = base64.b64encode(opt_bytes).decode("utf-8")
        
        system_instruction = (
            "You are an expert Clinical OCR and Document AI engine specialized in reading handwritten and printed Indian prescriptions.\n"
            "Extract the doctor's handwriting, clinic details, patient info, complaints, diagnoses, and medication lines.\n"
            "Return a pure JSON object with exactly these keys:\n"
            "1. 'raw_text': verbatim transcription of the prescription document.\n"
            "2. 'clinic_name': clinic/hospital name if visible.\n"
            "3. 'doctor_name': doctor name with degree if visible.\n"
            "4. 'symptoms': list of symptoms/findings translated to standard English (e.g. 'Headache', 'Nausea', 'Loss of appetite', 'Cough', 'Fever').\n"
            "5. 'diagnoses': list of disease conditions (e.g. 'Gastritis', 'Migraine', 'Hypertension', 'Acid peptic disease').\n"
            "6. 'medications': list of objects with 'brand_name', 'generic_guess', 'dose', 'frequency' (e.g. 'Tab Pantocid 40', 'Pantoprazole', '40mg', 'once daily').\n"
            "7. 'bounding_boxes': list of detected visual regions with 'box_2d': [ymin, xmin, ymax, xmax] (0-1000 scale) and 'label' ('CLINIC_ENTITY', 'PATIENT_DEMOGRAPHICS', 'DIAGNOSIS', 'MEDICATION_ARRAY') and 'confidence' (0.95-0.99)."
        )
        
        prompt = f"{system_instruction}\n\nPerform full clinical OCR and Named Entity Extraction on this prescription image."
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"
        
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
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(url, headers={"Content-Type": "application/json"}, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(content)
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
                    logger.error(f"Vision API error ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"Vision OCR processing exception: {e}")
            
        return {
            "raw_text": "",
            "clinic_name": "OPD Clinic",
            "doctor_name": "Consultant Physician",
            "symptoms": [],
            "diagnoses": [],
            "medications": [],
            "bounding_boxes": []
        }
