import json
import os
import sqlite3
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
    """Resolves raw text terms to standard SNOMED CT/LOINC codes using SQLite FTS5, Supabase, or JSON fallback."""
    
    def __init__(self, db_path: str = "clinical_knowledge.db", json_fallback_path: str = "mock_snomed_db.json"):
        self.db_path = self._resolve_path(db_path)
        self.json_fallback_path = self._resolve_path(json_fallback_path)
        self.concepts = []
        self.sqlite_conn = None
        
        # 1. Try SQLite FTS5 database first
        if self.db_path and os.path.exists(self.db_path):
            try:
                self.sqlite_conn = sqlite3.connect(self.db_path, check_same_thread=False)
                # Enable foreign keys and test connection
                cur = self.sqlite_conn.cursor()
                cur.execute("SELECT count(*) FROM concepts")
                cnt_c = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM brands")
                cnt_b = cur.fetchone()[0]
                logger.info(f"SQLite FTS5 Terminology Resolver initialized successfully with {cnt_c} concepts & {cnt_b} pharma brands.")
            except Exception as e:
                logger.error(f"Error initializing SQLite database: {e}")
                self.sqlite_conn = None

        # 2. Initialize Supabase client if configured in environment
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_client = None
        
        if SUPABASE_INSTALLED and self.supabase_url and self.supabase_key:
            try:
                self.supabase_client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Supabase client initialized successfully for cloud fuzzy matching.")
            except Exception as e:
                logger.error(f"Error initializing Supabase client: {e}")

        # 3. Load JSON fallback if SQLite is not available
        if not self.sqlite_conn and not self.supabase_client:
            logger.info("Running in local JSON fallback mode.")
            self.load_json_database()

    def _resolve_path(self, path: str) -> Optional[str]:
        if not path:
            return None
        if os.path.isabs(path) and os.path.exists(path):
            return path
        file_dir = os.path.dirname(os.path.abspath(__file__))
        candidate = os.path.join(file_dir, os.path.basename(path))
        if os.path.exists(candidate):
            return candidate
        parent_candidate = os.path.join(os.path.dirname(file_dir), os.path.basename(path))
        if os.path.exists(parent_candidate):
            return parent_candidate
        return os.path.join(file_dir, os.path.basename(path))

    def load_json_database(self):
        """Loads mock concepts from JSON file."""
        if not self.json_fallback_path or not os.path.exists(self.json_fallback_path):
            logger.error(f"JSON fallback not found at {self.json_fallback_path}.")
            self.concepts = []
            return
                
        try:
            with open(self.json_fallback_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.concepts = data.get("concepts", [])
                logger.info(f"Loaded {len(self.concepts)} mock terminology concepts from {self.json_fallback_path}.")
        except Exception as e:
            logger.error(f"Error loading JSON fallback: {e}")
            self.concepts = []

    def _log_unresolved_term(self, term: str):
        """Logs unresolved clinical terms to logs/unresolved_terms.jsonl for lexicon curation."""
        try:
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "unresolved_terms.jsonl")
            with open(log_file, "a", encoding="utf-8") as f:
                import datetime
                payload = {
                    "term": term,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                f.write(json.dumps(payload) + "\n")
        except Exception:
            pass

    def _search_sqlite(self, term_clean: str) -> Optional[Dict[str, Any]]:
        """Queries SQLite FTS5 tables for pharma brands, descriptions, and SNOMED concepts."""
        if not self.sqlite_conn:
            return None
        try:
            cur = self.sqlite_conn.cursor()
            
            # A. Search brands table (Exact match on brand or generic)
            cur.execute("""
                SELECT brand_name, generic_name, category, snomed_id
                FROM brands
                WHERE lower(brand_name) = ? OR lower(generic_name) = ?
            """, (term_clean, term_clean))
            row = cur.fetchone()
            if row:
                has_snomed = bool(row[3] and str(row[3]).strip())
                return {
                    "concept_id": row[3] if has_snomed else None,
                    "preferred_name": f"{row[0]} ({row[1]})",
                    "generic_name": row[1],
                    "semantic_tag": "substance",
                    "category": row[2],
                    "coded": has_snomed
                }

            # B. Search concepts table (Exact match on preferred name)
            cur.execute("""
                SELECT concept_id, preferred_name, semantic_tag
                FROM concepts
                WHERE lower(preferred_name) = ?
            """, (term_clean,))
            row = cur.fetchone()
            if row:
                return {
                    "concept_id": row[0],
                    "preferred_name": row[1],
                    "semantic_tag": row[2],
                    "coded": True
                }

            # C. FTS5 Search on brands
            fts_query = f'"{term_clean}"' if " " in term_clean else f"{term_clean}*"
            cur.execute("""
                SELECT b.brand_name, b.generic_name, b.category, b.snomed_id
                FROM brands_fts f
                JOIN brands b ON f.rowid = b.rowid
                WHERE brands_fts MATCH ?
                LIMIT 1
            """, (fts_query,))
            row = cur.fetchone()
            if row:
                has_snomed = bool(row[3] and str(row[3]).strip())
                return {
                    "concept_id": row[3] if has_snomed else None,
                    "preferred_name": f"{row[0]} ({row[1]})",
                    "generic_name": row[1],
                    "semantic_tag": "substance",
                    "category": row[2],
                    "coded": has_snomed
                }

            # D. FTS5 Search on concepts
            cur.execute("""
                SELECT c.concept_id, c.preferred_name, c.semantic_tag
                FROM concepts_fts f
                JOIN concepts c ON f.rowid = c.rowid
                WHERE concepts_fts MATCH ?
                LIMIT 1
            """, (fts_query,))
            row = cur.fetchone()
            if row:
                return {
                    "concept_id": row[0],
                    "preferred_name": row[1],
                    "semantic_tag": row[2],
                    "coded": True
                }

            # E. FTS5 Search on descriptions / synonyms
            cur.execute("""
                SELECT c.concept_id, c.preferred_name, c.semantic_tag
                FROM descriptions_fts df
                JOIN descriptions d ON df.rowid = d.rowid
                JOIN concepts c ON d.concept_id = c.concept_id
                WHERE descriptions_fts MATCH ?
                LIMIT 1
            """, (fts_query,))
            row = cur.fetchone()
            if row:
                return {
                    "concept_id": row[0],
                    "preferred_name": row[1],
                    "semantic_tag": row[2],
                    "coded": True
                }
                
        except Exception as e:
            logger.debug(f"SQLite FTS5 query error: {e}")
            
        return None

    def resolve_term(self, term: str) -> Optional[Dict[str, Any]]:
        """Matches a search term against concept names, brand names, and synonyms."""
        if not term:
            return None
            
        term_clean = term.strip().lower()

        # 1. SQLite FTS5 Fast Search (<1ms)
        sqlite_match = self._search_sqlite(term_clean)
        if sqlite_match:
            return sqlite_match
        
        # 2. Supabase Postgres Trigram Fuzzy Match
        if self.supabase_client:
            try:
                response = self.supabase_client.rpc(
                    "fuzzy_match_concept", 
                    {"search_term": term_clean}
                ).execute()
                
                if response.data and len(response.data) > 0:
                    best_match = response.data[0]
                    similarity = best_match.get("similarity", 0.0)
                    if similarity > 0.4 or best_match.get("concept_id"):
                        logger.info(f"Supabase resolved '{term}' -> '{best_match['preferred_name']}' (similarity: {similarity:.2f})")
                        return best_match
            except Exception as e:
                logger.error(f"Supabase RPC resolution failed: {e}")

        # 3. Local JSON Fallback: Exact & Substring Match
        if not self.concepts and self.json_fallback_path:
            self.load_json_database()

        for concept in self.concepts:
            if concept.get("preferred_name", "").lower() == term_clean:
                return concept
            for synonym in concept.get("synonyms", []):
                if synonym.lower() == term_clean or term_clean in synonym.lower():
                    return concept
                    
        # 4. Fuzzy Sequence Matcher
        best_ratio = 0.0
        best_match = None
        for concept in self.concepts:
            candidates = [concept.get("preferred_name", "").lower()] + [s.lower() for s in concept.get("synonyms", [])]
            for cand in candidates:
                ratio = difflib.SequenceMatcher(None, term_clean, cand).ratio()
                if ratio > best_ratio and ratio > 0.6:
                    best_ratio = ratio
                    best_match = concept
                    
        if best_match:
            logger.info(f"Fuzzy resolved '{term}' -> '{best_match['preferred_name']}' (confidence: {best_ratio:.2f})")
            return best_match

        # Log unresolved term for lexicon curation (never guess silently)
        self._log_unresolved_term(term)
        logger.warning(f"Could not resolve terminology for term: '{term}' - logged to unresolved_terms.jsonl")
        return None

    def resolve_extraction(self, extraction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Resolves all extracted clinical entities to structured terminology profiles."""
        resolved = {
            "symptoms": [],
            "diagnoses": [],
            "medications": []
        }
        
        seen_symptoms = set()
        for symptom in extraction_results.get("symptoms", []):
            match = self.resolve_term(symptom)
            item = self._format_concept(match, symptom) if match else self._format_uncoded(symptom, "finding")
            key = (item.get("concept_id"), (item.get("display") or item.get("original_query", "")).lower())
            if key not in seen_symptoms:
                seen_symptoms.add(key)
                resolved["symptoms"].append(item)
                
        seen_diagnoses = set()
        for diagnosis in extraction_results.get("diagnoses", []):
            match = self.resolve_term(diagnosis)
            item = self._format_concept(match, diagnosis) if match else self._format_uncoded(diagnosis, "disorder")
            key = (item.get("concept_id"), (item.get("display") or item.get("original_query", "")).lower())
            if key not in seen_diagnoses:
                seen_diagnoses.add(key)
                resolved["diagnoses"].append(item)
                
        seen_meds = set()
        for med in extraction_results.get("medications", []):
            brand_name = med.get("brand_name", "")
            generic_guess = med.get("generic_guess", "")
            match = self.resolve_term(brand_name) or self.resolve_term(generic_guess)
            
            if match:
                resolved_med = self._format_concept(match, brand_name or generic_guess)
                resolved_med["brand_name"] = brand_name or generic_guess
                resolved_med["generic_name"] = match.get("generic_name") or match.get("preferred_name")
                resolved_med["dose"] = med.get("dose", "")
                resolved_med["frequency"] = med.get("frequency", "")
                if "category" in match:
                    resolved_med["category"] = match["category"]
            else:
                resolved_med = {
                    "concept_id": None,
                    "display": brand_name or generic_guess,
                    "brand_name": brand_name or generic_guess,
                    "generic_name": brand_name or generic_guess,
                    "semantic_tag": "substance",
                    "dose": med.get("dose", ""),
                    "frequency": med.get("frequency", ""),
                    "coded": False
                }
                
            med_key = (resolved_med.get("concept_id"), (resolved_med.get("display") or brand_name).lower())
            if med_key not in seen_meds:
                seen_meds.add(med_key)
                resolved["medications"].append(resolved_med)
                
        return resolved

    def _format_concept(self, concept: Dict[str, Any], query_term: str) -> Dict[str, Any]:
        """Formats concept metadata into a standard terminology payload."""
        cid = concept.get("concept_id")
        has_code = bool(cid and str(cid).strip())
        data = {
            "concept_id": cid if has_code else None,
            "display": concept.get("preferred_name") or query_term,
            "original_query": query_term,
            "semantic_tag": concept.get("semantic_tag", "substance" if concept.get("generic_name") else "finding"),
            "coded": has_code
        }
        
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

    def _log_unresolved_term(self, term: str, context: Optional[str] = "unresolved_clinical_query"):
        """Logs unresolved term to logs/unresolved_terms.jsonl to feed future open-source lexicon."""
        try:
            from datetime import datetime, timezone
            file_dir = os.path.dirname(os.path.abspath(__file__))
            log_dir = os.path.join(file_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "unresolved_terms.jsonl")

            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "term": term,
                "context": context
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.warning(f"Failed to log unresolved term: {e}")
