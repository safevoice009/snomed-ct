import json
import os
import logging
from typing import Dict, Any, List, Optional
import difflib

# Add Supabase integration
try:
    from supabase import create_client, Client
    SUPABASE_INSTALLED = True
except ImportError:
    SUPABASE_INSTALLED = False

logger = logging.getLogger("terminology_resolver")

class TerminologyResolver:
    """Resolves raw text terms to standard SNOMED CT/LOINC codes using local or Supabase backends."""
    
    def __init__(self, db_path: str = "mock_snomed_db.json"):
        self.db_path = db_path
        self.concepts = []
        
        # Initialize Supabase client if credentials are in the environment
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_client = None
        
        if SUPABASE_INSTALLED and self.supabase_url and self.supabase_key:
            try:
                self.supabase_client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Supabase client initialized successfully for fuzzy matching.")
            except Exception as e:
                logger.error(f"Error initializing Supabase client: {e}")
                
        if not self.supabase_client:
            logger.info("Supabase credentials missing or Client failed to init. Running in local fallback mode.")
            self.load_database()

    def load_database(self):
        """Loads mock concepts from JSON file."""
        if not os.path.exists(self.db_path):
            # Check relative to current file's directory
            file_dir = os.path.dirname(os.path.abspath(__file__))
            candidate = os.path.join(file_dir, os.path.basename(self.db_path))
            if os.path.exists(candidate):
                self.db_path = candidate
            else:
                # Check parent directory (useful if invoked from api/ or tests/)
                parent_candidate = os.path.join(os.path.dirname(file_dir), os.path.basename(self.db_path))
                if os.path.exists(parent_candidate):
                    self.db_path = parent_candidate
                else:
                    logger.error(f"Mock database not found at {self.db_path}. Initializing empty database.")
                    self.concepts = []
                    return
                
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.concepts = data.get("concepts", [])
                logger.info(f"Loaded {len(self.concepts)} mock terminology concepts from {self.db_path}.")
        except Exception as e:
            logger.error(f"Error loading mock database: {e}")
            self.concepts = []

    def resolve_term(self, term: str) -> Optional[Dict[str, Any]]:
        """Matches a search term against concept names and synonyms, supporting fuzzy lookups.
        
        Tries Supabase fuzzy matching first, and falls back to local seed calculations if unconfigured.
        """
        if not term:
            return None
            
        term_clean = term.strip().lower()
        
        # 1. Supabase Postgres trigram fuzzy match
        if self.supabase_client:
            try:
                response = self.supabase_client.rpc(
                    "fuzzy_match_concept", 
                    {"search_term": term_clean}
                ).execute()
                
                if response.data and len(response.data) > 0:
                    best_match = response.data[0]
                    similarity = best_match.get("similarity", 0.0)
                    # We accept matches with a similarity score > 0.4 or valid exact matches
                    if similarity > 0.4 or best_match.get("concept_id"):
                        logger.info(f"Supabase resolved '{term}' -> '{best_match['preferred_name']}' (similarity: {similarity:.2f})")
                        return best_match
            except Exception as e:
                logger.error(f"Supabase RPC resolution failed: {e}. Falling back to local search.")
                if not self.concepts:
                    self.load_database()

        # 2. Local Fallback: Exact Match (Preferred Name or Synonyms)
        for concept in self.concepts:
            if concept["preferred_name"].lower() == term_clean:
                return concept
            for synonym in concept.get("synonyms", []):
                if synonym.lower() == term_clean:
                    return concept
                    
        # 3. Local Fallback: Substring Match
        for concept in self.concepts:
            if term_clean in concept["preferred_name"].lower():
                return concept
            for synonym in concept.get("synonyms", []):
                if term_clean in synonym.lower():
                    return concept
                    
        # 4. Local Fallback: Fuzzy Match (Trigram-like SequenceMatcher)
        best_ratio = 0.0
        best_match = None
        for concept in self.concepts:
            candidates = [concept["preferred_name"].lower()] + [s.lower() for s in concept.get("synonyms", [])]
            for cand in candidates:
                ratio = difflib.SequenceMatcher(None, term_clean, cand).ratio()
                if ratio > best_ratio and ratio > 0.6:  # Similarity threshold
                    best_ratio = ratio
                    best_match = concept
                    
        if best_match:
            logger.info(f"Fuzzy resolved '{term}' -> '{best_match['preferred_name']}' (confidence: {best_ratio:.2f})")
            return best_match

        logger.warning(f"Could not resolve terminology for term: '{term}'")
        return None

    def resolve_extraction(self, extraction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Resolves all extracted clinical entities to structured terminology profiles."""
        resolved = {
            "symptoms": [],
            "diagnoses": [],
            "medications": []
        }
        
        # Resolve symptoms
        for symptom in extraction_results.get("symptoms", []):
            match = self.resolve_term(symptom)
            if match:
                resolved["symptoms"].append(self._format_concept(match, symptom))
            else:
                resolved["symptoms"].append(self._format_uncoded(symptom, "finding"))
                
        # Resolve diagnoses
        for diagnosis in extraction_results.get("diagnoses", []):
            match = self.resolve_term(diagnosis)
            if match:
                resolved["diagnoses"].append(self._format_concept(match, diagnosis))
            else:
                resolved["diagnoses"].append(self._format_uncoded(diagnosis, "disorder"))
                
        # Resolve medications
        for med in extraction_results.get("medications", []):
            brand_name = med.get("brand_name", "")
            generic_guess = med.get("generic_guess", "")
            
            match = self.resolve_term(brand_name) or self.resolve_term(generic_guess)
            
            if match:
                resolved_med = self._format_concept(match, brand_name or generic_guess)
                resolved_med["dose"] = med.get("dose", "")
                resolved_med["frequency"] = med.get("frequency", "")
                resolved["medications"].append(resolved_med)
            else:
                resolved["medications"].append({
                    "concept_id": None,
                    "display": brand_name or generic_guess,
                    "semantic_tag": "substance",
                    "dose": med.get("dose", ""),
                    "frequency": med.get("frequency", ""),
                    "coded": False
                })
                
        return resolved

    def _format_concept(self, concept: Dict[str, Any], query_term: str) -> Dict[str, Any]:
        """Formats concept metadata into a standard terminology payload."""
        data = {
            "concept_id": concept["concept_id"],
            "display": concept["preferred_name"],
            "original_query": query_term,
            "semantic_tag": concept.get("semantic_tag", "finding"),
            "coded": True
        }
        
        # Add special Indian AYUSH tags if present
        if concept.get("ayush_extension"):
            data["ayush_extension"] = True
            
        if concept.get("cross_allopathy_mapping"):
            data["cross_allopathy_mapping"] = concept["cross_allopathy_mapping"]
            
        return data

    def _format_uncoded(self, term: str, default_tag: str) -> Dict[str, Any]:
        return {
            "concept_id": None,
            "display": term,
            "original_query": term,
            "semantic_tag": default_tag,
            "coded": False
        }
