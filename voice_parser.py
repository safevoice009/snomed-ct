"""
voice_parser.py
Ambient Clinical Voice Scribe Engine for SICCE.
Accepts audio dictations (English, Hindi, Hinglish), transcribes verbatim speech,
and extracts structured clinical entities (Symptoms, Diagnoses, Medications, Vitals).
"""

import os
import json
import base64
import logging
import asyncio
from typing import Dict, Any, List, Optional
import requests
from nlp_parser import PHISanitizer

logger = logging.getLogger("voice_parser")

class VoiceScribeParser:
    """Multimodal Clinical Voice Scribe for Indian Healthcare."""
    
    def __init__(self):
        self.model = os.getenv("LLM_MODEL", "gemini-2.5-flash")

    async def parse_audio(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> Dict[str, Any]:
        """Transcribes clinician audio dictation and extracts structured clinical entities."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY is missing for Voice Scribe.")
            return self._fallback_response("API Key missing")

        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        
        system_instruction = (
            "You are an expert Ambient Clinical Scribe AI specialized in Indian medical practice and multilingual clinical dictation.\n"
            "You understand clinical terminology spoken in Indian English, Hindi, and Hinglish shorthand (e.g. 'c/o khansi x 3 days', 'fever 102F', 'pet dard', 'BP 130/80', 'Tab Augmentin 625 BD', 'Pan-D OD', 'Dolo TDS').\n\n"
            "Analyze the doctor's audio dictation and return a strictly valid JSON object with exactly these keys:\n"
            "1. 'raw_transcript': Complete verbatim de-identified transcript of what the doctor said.\n"
            "2. 'symptoms': Array of patient complaints and clinical findings translated to standard English (e.g. ['Fever', 'Cough', 'Abdominal pain', 'Headache']).\n"
            "3. 'diagnoses': Array of clinical impressions or established diagnoses (e.g. ['Acute Gastroenteritis', 'Hypertension', 'Upper Respiratory Tract Infection']).\n"
            "4. 'medications': Array of medication objects, each with:\n"
            "   - 'brand_name': Commercial drug name (e.g. 'Augmentin 625', 'Pan-D', 'Telma 40', 'Dolo 650')\n"
            "   - 'generic_guess': Active molecule name (e.g. 'Amoxicillin and clavulanic acid', 'Pantoprazole + Domperidone')\n"
            "   - 'dose': Dosage strength/form (e.g. '625mg', '40mg', '1 tablet')\n"
            "   - 'frequency': Standard schedule (e.g. 'twice daily (BD)', 'once daily (OD)', 'three times daily (TDS)', 'at bedtime (HS)')\n"
            "5. 'vitals': Object with detected vitals (e.g. {'blood_pressure': '130/80 mmHg', 'pulse': '78/min', 'temperature': '101 F', 'spo2': '98%'}).\n"
            "6. 'allergies': Array of documented patient allergies (e.g. ['Penicillin', 'Sulfa']).\n"
            "7. 'advice': Array of dietary, lifestyle, or follow-up instructions."
        )

        prompt = f"{system_instruction}\n\nPerform full clinical audio transcription and structured extraction."
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"

        # Clean mime_type
        if ";" in mime_type:
            mime_type = mime_type.split(";")[0].strip()
        if not mime_type or mime_type == "application/octet-stream":
            mime_type = "audio/webm"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_audio
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
            def _post():
                return requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=25)
                
            res = await asyncio.to_thread(_post)
            if res.status_code == 200:
                data = res.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(content)
                # Sanitize raw transcript
                if "raw_transcript" in parsed:
                    parsed["raw_transcript"] = PHISanitizer.sanitize(parsed["raw_transcript"])
                return parsed
            else:
                logger.error(f"Gemini Audio API error ({res.status_code}): {res.text}")
                return self._fallback_response(f"Gemini API status: {res.status_code}")
        except Exception as e:
            logger.error(f"Voice scribe exception: {e}")
            return self._fallback_response(str(e))

    def _fallback_response(self, error_msg: str = "") -> Dict[str, Any]:
        return {
            "raw_transcript": "[Audio processing fallback - please verify microphone audio]",
            "symptoms": ["Clinical dictation recorded"],
            "diagnoses": [],
            "medications": [],
            "vitals": {},
            "allergies": [],
            "advice": [],
            "error": error_msg
        }
