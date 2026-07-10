import re
import os
import json
import logging
from typing import Dict, Any, List, Optional
import litellm
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nlp_parser")

# Attempt medspacy import
try:
    import spacy
    import medspacy
    from medspacy.target_matcher import TargetRule
    MEDSPACY_AVAILABLE = True
except ImportError:
    MEDSPACY_AVAILABLE = False
    logger.warning("medspacy or spacy not installed. Using high-performance regex clinical rule engine.")

# Pydantic schemas for structured LLM output
class MedicationEntity(BaseModel):
    brand_name: str = Field(description="The brand name recorded in the note, e.g. Dolo 650")
    generic_guess: str = Field(description="The generic active compound name, e.g. Paracetamol")
    dose: str = Field(default="", description="The dosage strength, e.g. 650mg, 40mg")
    frequency: str = Field(default="", description="The frequency, e.g. twice daily (BD), once daily (OD)")

class ClinicalEntities(BaseModel):
    symptoms: List[str] = Field(default_factory=list, description="A list of standard English symptoms/findings translated from text")
    diagnoses: List[str] = Field(default_factory=list, description="A list of standard English diagnoses/disease conditions")
    medications: List[MedicationEntity] = Field(default_factory=list, description="A list of medications prescribed")


class ClinicalCache:
    """Simple runtime in-memory cache to save on LLM API costs."""
    
    def __init__(self, max_size: int = 1000):
        self._cache = {}
        self.max_size = max_size
        
    def get(self, text: str) -> Optional[Dict[str, Any]]:
        clean_text = text.strip().lower()
        return self._cache.get(clean_text)
        
    def set(self, text: str, data: Dict[str, Any]):
        clean_text = text.strip().lower()
        if len(self._cache) >= self.max_size:
            self._cache.clear()
        self._cache[clean_text] = data


class RuleParser:
    """Clinical parser mapping standard Indian abbreviations and concepts locally."""
    
    ABBREVIATIONS = {
        r"\bc/o\b": "complaining of",
        r"\bh/o\b": "history of",
        r"\bsoboe\b": "dyspnea on exertion",
        r"\bpedal edema\s*\+": "edema of foot",
        r"\bpedal edema\b": "edema of foot",
        r"\bap\s*\+": "abdominal pain",
        r"\bap positive\b": "abdominal pain",
        r"\bapd\b": "acid peptic disease",
        r"\bb/l age\b": "bilateral acute gastroenteritis",
        r"\bloose motion(s)?\b": "diarrhoea",
        r"\bsar dard\b": "headache",
        r"\bpet kharab\b": "diarrhoea",
        r"\bulti\b": "vomiting"
    }
    
    DOSAGES = {
        r"\bbd\b": "twice daily",
        r"\bod\b": "once daily",
        r"\btds\b": "three times daily",
        r"\bhs\b": "at bedtime",
        r"\bqid\b": "four times daily"
    }

    def __init__(self):
        self.medspacy_nlp = None
        if MEDSPACY_AVAILABLE:
            try:
                # Load default medspacy model
                self.medspacy_nlp = medspacy.load()
                target_matcher = self.medspacy_nlp.get_pipe("medspacy_target_matcher")
                rules = [
                    TargetRule("loose motion", category="SYMPTOM"),
                    TargetRule("loose motions", category="SYMPTOM"),
                    TargetRule("sar dard", category="SYMPTOM"),
                    TargetRule("pet kharab", category="SYMPTOM"),
                    TargetRule("ulti", category="SYMPTOM"),
                    TargetRule("soboe", category="SYMPTOM"),
                    TargetRule("pedal edema", category="SYMPTOM"),
                    TargetRule("ap+", category="SYMPTOM"),
                    TargetRule("apd", category="DIAGNOSIS"),
                    TargetRule("amavata", category="SYMPTOM"),
                    TargetRule("vata vyadhi", category="SYMPTOM"),
                ]
                target_matcher.add(rules)
                logger.info("medspacy clinical pipeline loaded successfully.")
            except Exception as e:
                logger.warning(f"Failed to load medspacy pipeline: {e}. Falling back to regex parser.")
                self.medspacy_nlp = None

    def clean_text(self, text: str) -> str:
        """Applies case-insensitive abbreviation expanding."""
        cleaned = text.lower()
        for pattern, replacement in self.ABBREVIATIONS.items():
            cleaned = re.sub(pattern, replacement, cleaned)
        return cleaned

    def extract_dosage_frequency(self, text: str) -> Dict[str, str]:
        """Scans text for dosage frequencies like BD, OD."""
        extracted = {}
        for pattern, desc in self.DOSAGES.items():
            if re.search(pattern, text, re.IGNORECASE):
                extracted[pattern.replace(r"\b", "")] = desc
        return extracted

    def parse_locally(self, text: str) -> Dict[str, Any]:
        """Performs localized extraction of standard abbreviations and entities to save on LLM costs."""
        text_lower = text.lower()
        extracted = {
            "symptoms": [],
            "diagnoses": [],
            "medications": []
        }
        
        # Use medspacy if available, otherwise run regex rules
        if self.medspacy_nlp:
            try:
                doc = self.medspacy_nlp(text)
                for ent in doc.ents:
                    if ent.label_ == "SYMPTOM":
                        # Map to normalized preferred terms
                        term = ent.text.lower()
                        if "loose motion" in term or "pet kharab" in term:
                            extracted["symptoms"].append("Diarrhoea")
                        elif "sar dard" in term:
                            extracted["symptoms"].append("Headache")
                        elif "soboe" in term:
                            extracted["symptoms"].append("Dyspnea on exertion")
                        elif "pedal edema" in term:
                            extracted["symptoms"].append("Edema of foot")
                        elif "ap+" in term:
                            extracted["symptoms"].append("Abdominal pain")
                        elif "amavata" in term:
                            extracted["symptoms"].append("Amavata")
                        elif "vata vyadhi" in term:
                            extracted["symptoms"].append("Vata vyadhi")
                        else:
                            extracted["symptoms"].append(ent.text.capitalize())
                    elif ent.label_ == "DIAGNOSIS":
                        if "apd" in ent.text.lower():
                            extracted["diagnoses"].append("Acid peptic disease")
                        else:
                            extracted["diagnoses"].append(ent.text.capitalize())
            except Exception as e:
                logger.error(f"medspacy parsing runtime exception: {e}. Falling back to regex parser.")
                self._run_regex_fallback(text_lower, extracted)
        else:
            self._run_regex_fallback(text_lower, extracted)

        # Parse local medications
        if "dolo" in text_lower:
            freq = "twice daily" if "bd" in text_lower else ("once daily" if "od" in text_lower else "")
            extracted["medications"].append({
                "brand_name": "Dolo 650",
                "generic_guess": "Paracetamol",
                "dose": "650mg",
                "frequency": freq
            })
        if "pantocid" in text_lower:
            freq = "once daily" if "od" in text_lower else ""
            extracted["medications"].append({
                "brand_name": "Pantocid 40",
                "generic_guess": "Pantoprazole",
                "dose": "40mg",
                "frequency": freq
            })
        if "lasix" in text_lower:
            freq = "twice daily" if "bd" in text_lower else ""
            extracted["medications"].append({
                "brand_name": "Lasix 40mg",
                "generic_guess": "Furosemide",
                "dose": "40mg",
                "frequency": freq
            })
            
        return extracted

    def _run_regex_fallback(self, text_lower: str, extracted: Dict[str, Any]):
        if "loose motion" in text_lower or "pet kharab" in text_lower:
            extracted["symptoms"].append("Diarrhoea")
        if "sar dard" in text_lower:
            extracted["symptoms"].append("Headache")
        if "soboe" in text_lower:
            extracted["symptoms"].append("Dyspnea on exertion")
        if "pedal edema" in text_lower:
            extracted["symptoms"].append("Edema of foot")
        if "ap+" in text_lower or "ap positive" in text_lower or "abdominal pain" in text_lower:
            extracted["symptoms"].append("Abdominal pain")
        if "ulti" in text_lower:
            extracted["symptoms"].append("Vomiting")
        if "amavata" in text_lower:
            extracted["symptoms"].append("Amavata")
        if "vata vyadhi" in text_lower:
            extracted["symptoms"].append("Vata vyadhi")
        if "apd" in text_lower:
            extracted["diagnoses"].append("Acid peptic disease")


class LLMParser:
    """LiteLLM endpoint router parsing unstructured clinical narratives in the cloud."""
    
    def __init__(self):
        self.model = os.getenv("LLM_MODEL", "gemini/gemini-1.5-flash")
        
    async def parse_narrative(self, text: str) -> Dict[str, Any]:
        """Extracts clinical entities using cloud-based AI with Pydantic JSON validation."""
        
        system_prompt = (
            "You are a Clinical Named Entity Recognition (NER) assistant specialized in Indian health records.\n"
            "The input notes are often written in a mix of English, clinical abbreviations, and Hinglish (Hindi words in English script).\n"
            "Your task is to parse the note and extract symptoms, diagnoses, and medications.\n"
            "If you find Hinglish terms, translate them to standard English clinical entities (e.g. 'sar dard' -> 'Headache', 'loose motion' -> 'Diarrhoea')."
        )
        
        user_prompt = f"Extract clinical entities from this note:\n\"\"\"\n{text}\n\"\"\""
        
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY environment variable is not set. Falling back to local simulation.")
                return {"symptoms": [], "diagnoses": [], "medications": []}
                
            # Request structured JSON format conforming to the Pydantic schema
            response = await litellm.acompletion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=ClinicalEntities,
                temperature=0.0
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"LiteLLM structured output error: {e}")
            return {"symptoms": [], "diagnoses": [], "medications": []}


class ClinicalParser:
    """Unified hybrid parser matching local rules first and routing remaining Hinglish to LLMs."""
    
    def __init__(self):
        self.rules = RuleParser()
        self.llm = LLMParser()
        self.cache = ClinicalCache()
        
    async def parse(self, note: str) -> Dict[str, Any]:
        # 1. Check cache first to avoid LLM & processing costs
        cached_result = self.cache.get(note)
        if cached_result:
            logger.info("Found clinical entities in local cache.")
            return cached_result
            
        logger.info(f"Parsing clinical note: '{note}'")
        
        # 2. Local Extraction via rules / medspacy
        local_entities = self.rules.parse_locally(note)
        
        # 3. Determine if LLM is required
        # If there are Hinglish verb structures (e.g., 'ho raha', 'lag raha', 'tha')
        # or unstructured text that rule engine missed, query LiteLLM.
        unstructured_triggers = ["ho raha", "lag raha", "tha", "hai", "jaisa", "jalan"]
        needs_llm = any(trigger in note.lower() for trigger in unstructured_triggers)
        
        llm_entities = {"symptoms": [], "diagnoses": [], "medications": []}
        if needs_llm:
            logger.info("Unstructured content detected. Routing to LiteLLM router.")
            llm_entities = await self.llm.parse_narrative(note)
            
        # 4. Merge extractions and deduplicate
        merged = self._merge_entities(local_entities, llm_entities)
        
        # 5. Expand and normalize dosage frequencies
        for med in merged.get("medications", []):
            freq = med.get("frequency", "")
            if freq:
                freq_clean = self.rules.extract_dosage_frequency(freq)
                if freq_clean:
                    med["frequency"] = list(freq_clean.values())[0]
                    
        # Update Cache
        self.cache.set(note, merged)
        return merged

    def _merge_entities(self, local: Dict[str, Any], llm: Dict[str, Any]) -> Dict[str, Any]:
        """Combines locally extracted concepts with LLM entities, eliminating duplicates."""
        merged = {
            "symptoms": list(set(local["symptoms"] + llm.get("symptoms", []))),
            "diagnoses": list(set(local["diagnoses"] + llm.get("diagnoses", []))),
            "medications": []
        }
        
        # Merge medications by brand name mapping
        med_map = {}
        for m in local["medications"] + llm.get("medications", []):
            brand = m.get("brand_name", "").strip().lower()
            if not brand:
                continue
            if brand not in med_map:
                med_map[brand] = m
            else:
                # Merge missing keys
                for key in ["generic_guess", "dose", "frequency"]:
                    if not med_map[brand].get(key) and m.get(key):
                        med_map[brand][key] = m[key]
                        
        merged["medications"] = list(med_map.values())
        return merged
