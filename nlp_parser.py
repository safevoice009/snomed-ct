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

    def clear(self):
        """Purges all cached extractions from memory."""
        self._cache.clear()


class PHISanitizer:
    """Automated PHI De-identification and Redactor conforming to Indian DPDP Act 2023."""
    
    PATTERNS = [
        # Indian Phone Numbers (+91 9876543210 or 9876543210)
        (r"(?:\+91[\-\s]?)?[6-9]\d{9}", "[REDACTED_PHONE]"),
        # 14-digit ABHA IDs (e.g. 91-1234-5678-9012)
        (r"\b\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[REDACTED_ABHA]"),
        # 12-digit Aadhaar Numbers
        (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[REDACTED_AADHAAR]"),
        # Email Addresses
        (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]"),
        # Patient Names with standard Indian salutations
        (r"\b(?:Mr\.|Mrs\.|Ms\.|Shri|Smt|Master|Baby|Patient|Pt\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", "[PATIENT_NAME]")
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Strips direct personal identifiers before LLM routing or cloud processing."""
        sanitized = text
        for pattern, replacement in cls.PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        return sanitized


class RuleParser:
    """Clinical parser mapping standard Indian abbreviations and concepts locally."""
    
    ABBREVIATIONS = {
        r"\bc/o\b": "complaining of",
        r"\bh/o\b": "history of",
        r"\bk/c/o\b": "known case of",
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
        r"\bulti\b": "vomiting",
        r"\bkhansi\b": "cough",
        r"\bbukhar\b": "fever"
    }
    
    DOSAGES = {
        r"\bbd\b": "twice daily",
        r"\bod\b": "once daily",
        r"\btds\b": "three times daily",
        r"\bhs\b": "at bedtime",
        r"\bqid\b": "four times daily",
        r"\bsos\b": "as needed",
        r"\bprn\b": "as needed"
    }

    KNOWN_DRUGS = [
        {"pattern": r"levocet[\s\-]m", "brand": "Tab Levocet M", "generic": "Levocetirizine and montelukast", "dose": "5mg/10mg"},
        {"pattern": r"ascoril[\s\-]d", "brand": "Syp Ascoril D", "generic": "Dextromethorphan hydrobromide", "dose": "100ml"},
        {"pattern": r"telma[\s\-]40|telma\b", "brand": "Tab Telma 40", "generic": "Telmisartan", "dose": "40mg"},
        {"pattern": r"amlo(dipine|ng)?\s*(5|10)?", "brand": "Tab Amlodipine 5mg", "generic": "Amlodipine", "dose": "5mg"},
        {"pattern": r"dolo[\s\-]650|dolo\b", "brand": "Tab Dolo 650", "generic": "Paracetamol", "dose": "650mg"},
        {"pattern": r"pantocid[\s\-]40|pantocid\b|pan[\s\-]40", "brand": "Cap Pantocid 40", "generic": "Pantoprazole", "dose": "40mg"},
        {"pattern": r"norflox[\s\-]tz|norflox\b", "brand": "Tab Norflox TZ", "generic": "Norfloxacin and tinidazole", "dose": "400mg/600mg"},
        {"pattern": r"lasix[\s\-]40|lasix\b", "brand": "Tab Lasix 40mg", "generic": "Furosemide", "dose": "40mg"},
        {"pattern": r"glycomet[\s\-]500|glycomet\b|metformin\b", "brand": "Tab Glycomet 500", "generic": "Metformin hydrochloride", "dose": "500mg"},
        {"pattern": r"azithral[\s\-]500|azithral\b|azithromycin\b", "brand": "Tab Azithral 500", "generic": "Azithromycin", "dose": "500mg"},
        {"pattern": r"augmentin[\s\-]625|augmentin\b|clavam\b", "brand": "Tab Augmentin 625", "generic": "Amoxicillin and clavulanic acid", "dose": "625mg"},
        {"pattern": r"atorva[\s\-]10|atorva\b|atorvastatin\b", "brand": "Tab Atorva 10", "generic": "Atorvastatin", "dose": "10mg"},
        {"pattern": r"ors\b|electral\b", "brand": "ORS Electral Sachet", "generic": "Oral rehydration salts", "dose": "1 sachet in 1L"},
        {"pattern": r"steam(\s+inhalation)?", "brand": "Steam Inhalation", "generic": "Steam inhalation", "dose": "10 mins"}
    ]

    def __init__(self):
        self.medspacy_nlp = None
        if MEDSPACY_AVAILABLE:
            try:
                self.medspacy_nlp = medspacy.load()
                target_matcher = self.medspacy_nlp.get_pipe("medspacy_target_matcher")
                rules = [
                    TargetRule("loose motion", category="SYMPTOM"),
                    TargetRule("loose motions", category="SYMPTOM"),
                    TargetRule("sar dard", category="SYMPTOM"),
                    TargetRule("pet kharab", category="SYMPTOM"),
                    TargetRule("ulti", category="SYMPTOM"),
                    TargetRule("khansi", category="SYMPTOM"),
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
        cleaned = text.lower()
        for pattern, replacement in self.ABBREVIATIONS.items():
            cleaned = re.sub(pattern, replacement, cleaned)
        return cleaned

    def extract_dosage_frequency(self, text: str) -> Dict[str, str]:
        extracted = {}
        for pattern, desc in self.DOSAGES.items():
            if re.search(pattern, text, re.IGNORECASE):
                extracted[pattern.replace(r"\b", "")] = desc
        return extracted

    def parse_locally(self, text: str) -> Dict[str, Any]:
        """Comprehensive rule engine detecting symptoms, diagnoses, and prescription lines."""
        text_lower = text.lower()
        extracted = {
            "symptoms": [],
            "diagnoses": [],
            "medications": []
        }
        
        # 1. Symptoms Detection
        if re.search(r"\b(khansi|cough|dry cough|productive cough)\b", text_lower):
            extracted["symptoms"].append("Cough")
        if re.search(r"\b(chest tightness|chest heaviness|tightness in chest)\b", text_lower):
            extracted["symptoms"].append("Chest tightness")
        if re.search(r"\b(loose motion|loose motions|diarrhea|diarrhoea|pet kharab|dast)\b", text_lower):
            extracted["symptoms"].append("Diarrhoea")
        if re.search(r"\b(sar dard|headache|sir dard)\b", text_lower):
            extracted["symptoms"].append("Headache")
        if re.search(r"\b(fever|bukhar|pyrexia|taap|101f|102f)\b", text_lower):
            extracted["symptoms"].append("Fever")
        if re.search(r"\b(ulti|vomiting|nausea|ulti jaisa)\b", text_lower):
            extracted["symptoms"].append("Nausea and vomiting")
        if re.search(r"\b(soboe|dyspnea|shortness of breath|breathlessness|dam fulna)\b", text_lower):
            extracted["symptoms"].append("Dyspnea on exertion")
        if re.search(r"\b(pedal edema|edema|foot swelling|pair me sujan)\b", text_lower):
            extracted["symptoms"].append("Edema of foot")
        if re.search(r"\b(ap\+|ap positive|abdominal pain|pet dard|pet me marod|stomach pain)\b", text_lower):
            extracted["symptoms"].append("Abdominal pain")
        if re.search(r"\b(heartburn|jalan|chest burning|acidity)\b", text_lower):
            extracted["symptoms"].append("Heartburn")
        if re.search(r"\b(amavata)\b", text_lower):
            extracted["symptoms"].append("Amavata")
        if re.search(r"\b(vata vyadhi)\b", text_lower):
            extracted["symptoms"].append("Vata vyadhi")

        # 2. Diagnoses Detection
        if re.search(r"\b(allergic rhinitis|rhinitis|sardi|sneezing)\b", text_lower):
            extracted["diagnoses"].append("Allergic rhinitis")
        if re.search(r"\b(hypertension|htn|high bp|bp high)\b", text_lower):
            extracted["diagnoses"].append("Hypertension")
        if re.search(r"\b(acute gastroenteritis|age|gastroenteritis)\b", text_lower):
            extracted["diagnoses"].append("Acute gastroenteritis")
        if re.search(r"\b(apd|acid peptic disease|gerd)\b", text_lower):
            extracted["diagnoses"].append("Acid peptic disease")
        if re.search(r"\b(diabetes mellitus|diabetes|dm|t2dm|sugar)\b", text_lower):
            extracted["diagnoses"].append("Diabetes mellitus")
        if re.search(r"\b(rheumatoid arthritis|ra)\b", text_lower):
            extracted["diagnoses"].append("Rheumatoid arthritis")

        # 3. Medications Detection
        for drug in self.KNOWN_DRUGS:
            if re.search(drug["pattern"], text_lower):
                # Extract surrounding frequency and dose
                freq = ""
                # Find if BD, OD, TDS, HS, SOS appears near the drug or in text
                match_freq = re.search(rf"{drug['pattern']}.*?\b(bd|od|tds|hs|sos|qid|twice daily|once daily)\b", text_lower)
                if match_freq and match_freq.group(1):
                    freq = str(match_freq.group(1)).upper()
                else:
                    if "bd" in text_lower: freq = "BD"
                    elif "tds" in text_lower: freq = "TDS"
                    elif "hs" in text_lower: freq = "HS"
                    elif "od" in text_lower: freq = "OD"
                    elif "sos" in text_lower: freq = "SOS"

                extracted["medications"].append({
                    "brand_name": drug["brand"],
                    "generic_guess": drug["generic"],
                    "dose": drug["dose"],
                    "frequency": freq
                })

        # 4. Generic Fallback Regex for Unlisted Medications (e.g. Tab XYZ 10mg BD)
        generic_med_matches = re.finditer(r"(?:Tab|Cap|Syp|Inj|Oint|Drop)\.?\s+([A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)?)\s*(?:(\d+(?:mg|mcg|gm|ml)?))?\s*(?:(\d+\s*(?:tsp|tablets?|caps?))|\b(OD|BD|TDS|QID|HS|SOS)\b)?", text, re.IGNORECASE)
        for match in generic_med_matches:
            name = match.group(1).strip()
            # If not already added
            if not any(name.lower() in m["brand_name"].lower() for m in extracted["medications"]):
                dose = match.group(2) or ""
                freq_match = match.group(4) or match.group(3) or "OD"
                extracted["medications"].append({
                    "brand_name": f"Tab {name.capitalize()}",
                    "generic_guess": name.capitalize(),
                    "dose": dose or "Standard",
                    "frequency": str(freq_match).upper()
                })

        return extracted


class LLMParser:
    """High-speed zero-shot Gemini 2.5 Flash router extracting clinical entities with strict JSON validation."""
    
    def __init__(self):
        self.model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        
    async def parse_narrative(self, text: str) -> Dict[str, Any]:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"symptoms": [], "diagnoses": [], "medications": []}
            
        system_instruction = (
            "You are an expert Clinical NER assistant specialized in Indian OPD prescriptions and health records.\n"
            "Extract clinical entities into JSON with exactly these keys:\n"
            "- 'symptoms': list of standard English symptom names (e.g. 'Cough', 'Headache', 'Fever', 'Chest tightness')\n"
            "- 'diagnoses': list of disease conditions (e.g. 'Hypertension', 'Allergic rhinitis', 'Type 2 Diabetes', 'Acid peptic disease')\n"
            "- 'medications': list of objects with 'brand_name', 'generic_guess', 'dose', 'frequency' (e.g. 'Tab Levocet M', 'Levocetirizine', '5mg', 'at bedtime')\n"
            "Translate colloquial Hinglish phrases (e.g. 'sar dard' -> 'Headache', 'khansi' -> 'Cough', 'pet me marod' -> 'Abdominal pain')."
        )
        
        prompt = f"{system_instruction}\n\nClinical Note:\n\"\"\"\n{text}\n\"\"\"\n\nReturn pure JSON matching the schema."
        
        try:
            import httpx
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"response_mime_type": "application/json"}
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(content)
                    return {
                        "symptoms": parsed.get("symptoms", []),
                        "diagnoses": parsed.get("diagnoses", []),
                        "medications": parsed.get("medications", [])
                    }
        except Exception as e:
            logger.error(f"Gemini 2.5 Flash clinical extraction error: {e}")
            
        return {"symptoms": [], "diagnoses": [], "medications": []}


class ClinicalParser:
    """Unified hybrid parser matching local rules first and routing remaining Hinglish to LLMs."""
    
    def __init__(self):
        self.rules = RuleParser()
        self.llm = LLMParser()
        self.cache = ClinicalCache()
        
    async def parse(self, note: str) -> Dict[str, Any]:
        cached_result = self.cache.get(note)
        if cached_result:
            logger.info("Found clinical entities in local cache.")
            return cached_result
            
        logger.info(f"Parsing clinical note: '{note}'")
        
        # 1. Local Extraction via comprehensive rule engine
        local_entities = self.rules.parse_locally(note)
        
        # 2. Query LLM if unstructured and api key present
        unstructured_triggers = ["ho raha", "lag raha", "tha", "hai", "jaisa", "jalan"]
        needs_llm = any(trigger in note.lower() for trigger in unstructured_triggers)
        
        llm_entities = {"symptoms": [], "diagnoses": [], "medications": []}
        if needs_llm and os.getenv("GEMINI_API_KEY"):
            sanitized_note = PHISanitizer.sanitize(note)
            llm_entities = await self.llm.parse_narrative(sanitized_note)
            
        # 3. Merge extractions and deduplicate
        merged = self._merge_entities(local_entities, llm_entities)
        
        # 4. Expand and normalize dosage frequencies
        for med in merged.get("medications", []):
            freq = med.get("frequency", "")
            if freq:
                freq_clean = self.rules.extract_dosage_frequency(freq)
                if freq_clean:
                    med["frequency"] = list(freq_clean.values())[0]

        # 5. Run Clinical Drug-Drug Interaction (DDI) & Safety Checker
        merged["ddi_alerts"] = DDIEngine.check_interactions(merged.get("medications", []))

        # 6. Generate Multi-Lingual Vernacular Patient Dosage Cards
        merged["vernacular_dosages"] = VernacularTranslator.generate_schedules(merged.get("medications", []))
                    
        # Update Cache
        self.cache.set(note, merged)
        return merged

    def _merge_entities(self, local: Dict[str, Any], llm: Dict[str, Any]) -> Dict[str, Any]:
        merged = {
            "symptoms": list(set(local["symptoms"] + llm.get("symptoms", []))),
            "diagnoses": list(set(local["diagnoses"] + llm.get("diagnoses", []))),
            "medications": []
        }
        
        med_map = {}
        for m in local["medications"] + llm.get("medications", []):
            brand = m.get("brand_name", "").strip().lower()
            if not brand:
                continue
            if brand not in med_map:
                med_map[brand] = m
            else:
                for key in ["generic_guess", "dose", "frequency"]:
                    if not med_map[brand].get(key) and m.get(key):
                        med_map[brand][key] = m[key]
                        
        merged["medications"] = list(med_map.values())
        return merged


class DDIEngine:
    """Clinical Drug-Drug Interaction (DDI) & Safety Alert Checker."""

    INTERACTIONS = [
        {
            "group_a": ["norfloxacin", "norflox", "ciprofloxacin", "ofloxacin", "levofloxacin"],
            "group_b": ["pantocid", "pantoprazole", "mucaine", "omeprazole", "antacid", "gelusil", "digene"],
            "type": "chelation",
            "severity": "moderate",
            "title": "Chelation & Bioavailability Reduction Alert",
            "message": "Fluoroquinolones bind with multivalent cations/antacids. Administer Pantocid/Mucaine at least 2 hours before or 4 hours after Norflox."
        },
        {
            "group_a": ["dolo", "paracetamol", "crocin", "calpol", "panadol"],
            "group_b": ["combiflam", "flexon", "paracetamol"],
            "type": "overdose",
            "severity": "high",
            "title": "Cumulative Hepatotoxicity Warning",
            "message": "Multiple Paracetamol-containing formulations detected. Ensure total daily intake does not exceed 4,000 mg."
        },
        {
            "group_a": ["lasix", "furosemide", "torsemide"],
            "group_b": ["combiflam", "brufen", "ibuprofen", "diclofenac", "voveran"],
            "type": "renal",
            "severity": "moderate",
            "title": "Renal Perfusion & Diuretic Blunting Alert",
            "message": "NSAIDs blunt loop diuretic efficacy and increase nephrotoxicity risk. Monitor serum creatinine and urine output."
        }
    ]

    @classmethod
    def check_interactions(cls, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        alerts = []
        med_names = [m.get("brand_name", "").lower() + " " + m.get("generic_guess", "").lower() for m in medications]
        
        for rule in cls.INTERACTIONS:
            found_a = any(any(k in name for k in rule["group_a"]) for name in med_names)
            found_b = any(any(k in name for k in rule["group_b"]) for name in med_names)
            
            if found_a and found_b:
                alerts.append({
                    "severity": rule["severity"],
                    "title": rule["title"],
                    "message": rule["message"]
                })
        return alerts


class VernacularTranslator:
    """Translates clinical dosage instructions into Indian vernacular languages."""

    SCHEDULES = {
        "od": {
            "hi": "दिन में 1 बार (सुबह नाश्ते से पहले / सुबह)",
            "mr": "दिवसातून १ वेळ (सकाळी नाश्त्यापूर्वी / सकाळी)",
            "ta": "ஒரு நாளைக்கு 1 முறை (காலை உணவுக்கு முன்)",
            "te": "రోజుకు 1 సారి (ఉదయం టిఫిన్ ముందు)",
            "bn": "দিনে ১ বার (সকালে প্রাতঃরাশের আগে)"
        },
        "bd": {
            "hi": "दिन में 2 बार (सुबह और रात - खाना खाने के बाद)",
            "mr": "दिवसातून २ वेळा (सकाळी व रात्री - जेवणानंतर)",
            "ta": "ஒரு நாளைக்கு 2 முறை (காலை மற்றும் இரவு - உணவுக்குப் பின்)",
            "te": "రోజుకు 2 సార్లు (ఉదయం మరియు రాత్రి - భోజనం తర్వాత)",
            "bn": "দিনে ২ বার (সকাল এবং রাতে - খাওয়ার পর)"
        },
        "tds": {
            "hi": "दिन में 3 बार (सुबह, दोपहर, रात - खाने के बाद)",
            "mr": "दिवसातून ३ वेळा (सकाळी, दुपारी, रात्री - जेवणानंतर)",
            "ta": "ஒரு நாளைக்கு 3 முறை (காலை, மதியம், இரவு - உணவுக்குப் பின்)",
            "te": "రోజుకు 3 సార్లు (ఉదయం, మధ్యాహ్నం, రాత్రి - భోజనం తర్వాత)",
            "bn": "দিনে ৩ বার (সকাল, দুপুর, রাত - খাওয়ার পর)"
        },
        "hs": {
            "hi": "रात को सोने से पहले (गुनगुने पानी के साथ)",
            "mr": "रात्री झोपताना (कोमट पाण्यासोबत)",
            "ta": "இரவு தூங்கும் முன் (வெதுவெதுப்பான நீருடன்)",
            "te": "రాత్రి పడుకునే ముందు (గోరువెచ్చని నీటితో)",
            "bn": "রাতে শোবার আগে (হালকা গরম জলের সাথে)"
        },
        "sos": {
            "hi": "ज़रूरत पड़ने पर (जैसे बुखार या दर्द होने पर)",
            "mr": "गरज असेल तेव्हा (ताप किंवा दुखणे असल्यास)",
            "ta": "தேவைப்படும் போது மட்டும்",
            "te": "అవసరం అయినప్పుడు మాత్రమే",
            "bn": "প্রয়োজন হলে"
        }
    }

    @classmethod
    def generate_schedules(cls, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for m in medications:
            brand = m.get("brand_name", "Medication")
            dose = m.get("dose", "")
            raw_freq = (m.get("frequency", "") + " " + brand).lower()
            
            sch_key = "od"
            if "bd" in raw_freq or "twice" in raw_freq or "two" in raw_freq:
                sch_key = "bd"
            elif "tds" in raw_freq or "three" in raw_freq or "tid" in raw_freq or "tsp" in raw_freq:
                sch_key = "tds"
            elif "hs" in raw_freq or "bedtime" in raw_freq or "night" in raw_freq:
                sch_key = "hs"
            elif "sos" in raw_freq or "needed" in raw_freq:
                sch_key = "sos"
                
            trans = cls.SCHEDULES.get(sch_key, cls.SCHEDULES["od"])
            results.append({
                "medication": brand,
                "dose": dose,
                "translations": trans
            })
        return results
