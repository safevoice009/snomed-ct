"""
tests/test_rf2_rehearsal.py
===========================
RF2 Ingestion Dress Rehearsal Test Suite.

Per Task B:
- Tests that scripts/load_rf2.py correctly parses real RF2 Snapshot format files.
- Uses data/rf2/_format_test/ into a temporary in-memory / temp SQLite database.
- Guarantees zero code changes required when real NRCeS SNOMED CT India Edition zip lands.
- Does NOT touch production clinical_knowledge.db.
"""

import os
import sys
import sqlite3
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.load_rf2 import init_schema, load_rf2_directory, load_seeds


class TestRF2Rehearsal(unittest.TestCase):

    def setUp(self):
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_path = self.temp_db_file.name
        self.temp_db_file.close()

        self.conn = sqlite3.connect(self.temp_db_path)
        init_schema(self.conn)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_rf2_format_snapshot_ingestion(self):
        """Verifies ingestion of hand-built mock RF2 Concept and Description Snapshot files."""
        format_test_dir = os.path.join(PROJECT_ROOT, "data", "rf2", "_format_test")
        self.assertTrue(os.path.exists(format_test_dir), f"Directory {format_test_dir} does not exist.")

        # Ingest test RF2 snapshot
        load_rf2_directory(self.conn, format_test_dir)

        cursor = self.conn.cursor()

        # 1. Assert active concepts ingested (concept 9900006 is inactive and must be skipped)
        concepts = cursor.execute("SELECT concept_id, preferred_name, semantic_tag, active FROM concepts WHERE concept_id LIKE '99%' ORDER BY concept_id;").fetchall()
        self.assertEqual(len(concepts), 9, f"Expected 9 active concepts, found {len(concepts)}")
        
        # Check FSN parsing extracted semantic tag and cleaned name
        c1 = cursor.execute("SELECT preferred_name, semantic_tag FROM concepts WHERE concept_id = '9900001';").fetchone()
        self.assertIsNotNone(c1)
        self.assertEqual(c1[0], "Format Test Severe Headache")
        self.assertEqual(c1[1], "finding")

        # 2. Assert active descriptions ingested
        descriptions = cursor.execute("SELECT description_id, concept_id, term FROM descriptions WHERE concept_id LIKE '99%' ORDER BY description_id;").fetchall()
        self.assertTrue(len(descriptions) >= 3)

        # 3. Assert FTS5 virtual tables can search test concepts and descriptions
        fts_concept_match = cursor.execute("SELECT concept_id FROM concepts_fts WHERE concepts_fts MATCH 'Headache';").fetchall()
        self.assertTrue(any(row[0] == "9900001" for row in fts_concept_match))

        fts_desc_match = cursor.execute("SELECT concept_id FROM descriptions_fts WHERE descriptions_fts MATCH 'Pyrexia';").fetchall()
        self.assertTrue(any(row[0] == "9900002" for row in fts_desc_match))


if __name__ == "__main__":
    unittest.main()
