"""
tests/test_terminology_full.py
==============================
Verifies the SQLite FTS5 SNOMED CT terminology pipeline.
Per MASTER_DIRECTIVE.md Task 1.2:
- Resolves real clinical concepts (symptoms, disorders, active substances).
- Resolves Indian pharmaceutical brands to generic molecules and SNOMED codes.
- Resolves vernacular/Hinglish synonyms via descriptions_fts.
- Returns uncoded without guessing on unknown terms.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from terminology_resolver import TerminologyResolver


class TestFullTerminologyResolver(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.resolver = TerminologyResolver("clinical_knowledge.db")

    def test_snomed_concept_resolution(self):
        """Verify resolution of core clinical disorders and findings."""
        # 1. Headache
        res_headache = self.resolver.resolve_term("Headache")
        self.assertIsNotNone(res_headache)
        self.assertEqual(res_headache["concept_id"], "25064002")

        # 2. Type 2 diabetes mellitus
        res_t2dm = self.resolver.resolve_term("Type 2 diabetes mellitus")
        self.assertIsNotNone(res_t2dm)
        self.assertEqual(res_t2dm["concept_id"], "44054006")

        # 3. Essential hypertension
        res_htn = self.resolver.resolve_term("Essential hypertension")
        self.assertIsNotNone(res_htn)
        self.assertEqual(res_htn["concept_id"], "38341003")

    def test_indian_brand_resolution(self):
        """Verify Indian pharmaceutical brand mapping to active generic substance."""
        # 1. Dolo 650 -> Paracetamol
        res_dolo = self.resolver.resolve_term("Dolo 650")
        self.assertIsNotNone(res_dolo)
        self.assertEqual(res_dolo["concept_id"], "387517004")
        self.assertEqual(res_dolo["generic_name"], "Paracetamol")

        # 2. Pantocid 40 -> Pantoprazole
        res_panto = self.resolver.resolve_term("Pantocid 40")
        self.assertIsNotNone(res_panto)
        self.assertEqual(res_panto["concept_id"], "387584000")
        self.assertEqual(res_panto["generic_name"], "Pantoprazole")

        # 3. Augmentin 625 -> Amoxicillin and clavulanic acid
        res_aug = self.resolver.resolve_term("Augmentin 625")
        self.assertIsNotNone(res_aug)
        self.assertEqual(res_aug["concept_id"], "372687004")

    def test_vernacular_hinglish_synonym_resolution(self):
        """Verify that descriptions_fts resolves vernacular terms to correct SNOMED concepts."""
        # 'sar dard' -> Headache (25064002)
        res_sar = self.resolver.resolve_term("sar dard")
        self.assertIsNotNone(res_sar)
        self.assertEqual(res_sar["concept_id"], "25064002")

        # 'saas phoolna' or 'soboe' -> Dyspnea on exertion (267036007)
        res_soboe = self.resolver.resolve_term("saas phoolna")
        self.assertIsNotNone(res_soboe)
        self.assertEqual(res_soboe["concept_id"], "267036007")

    def test_uncoded_handling_no_hallucination(self):
        """Verify that unknown nonsense terms return None without hallucinating codes and log to logs/unresolved_terms.jsonl."""
        test_term = f"NonexistentUnicornDisease{os.getpid()}"
        res_unknown = self.resolver.resolve_term(test_term)
        self.assertIsNone(res_unknown)

        # Assert logged to unresolved_terms.jsonl per Task D
        log_path = os.path.join(PROJECT_ROOT, "logs", "unresolved_terms.jsonl")
        self.assertTrue(os.path.exists(log_path), "logs/unresolved_terms.jsonl was not created.")
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(test_term, content)

    def test_no_duplicate_snomed_codes_across_different_generics(self):
        """CRITICAL DATA INTEGRITY GUARD (Law #1/#2): Fail if any snomed_id maps to >1 distinct generic_name."""
        import sqlite3
        import json
        from collections import defaultdict

        # 1. Check SQLite brands table
        db_path = os.path.join(PROJECT_ROOT, "clinical_knowledge.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            rows = conn.execute("SELECT snomed_id, generic_name FROM brands WHERE snomed_id IS NOT NULL AND snomed_id != '';").fetchall()
            conn.close()

            code_to_generics = defaultdict(set)
            for sid, gen in rows:
                code_to_generics[sid].add(gen.strip().lower())

            for sid, generics in code_to_generics.items():
                self.assertLessEqual(
                    len(generics), 1,
                    f"DATA INTEGRITY FAILURE: SNOMED code {sid} is mapped to multiple distinct generics: {generics}"
                )

        # 2. Check PMBJP formulary JSON
        pmbjp_path = os.path.join(PROJECT_ROOT, "data", "formulary", "pmbjp_generic_formulary.json")
        if os.path.exists(pmbjp_path):
            with open(pmbjp_path, "r", encoding="utf-8") as f:
                pmbjp_data = json.load(f)
            json_code_to_generics = defaultdict(set)
            for item in pmbjp_data:
                sid = item.get("snomed_id")
                if sid:
                    json_code_to_generics[sid].add(item["generic_name"].strip().lower())

            for sid, generics in json_code_to_generics.items():
                self.assertLessEqual(
                    len(generics), 1,
                    f"DATA INTEGRITY FAILURE in PMBJP formulary: SNOMED code {sid} is mapped to multiple distinct generics: {generics}"
                )


if __name__ == "__main__":
    unittest.main()
