import unittest
import os
import sys
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, verify_api_key
from nlp_parser import ClinicalParser
from terminology_resolver import TerminologyResolver
from fhir_generator import FHIRGenerator


class TestSICCEPipeline(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.parser = ClinicalParser()
        cls.resolver = TerminologyResolver("mock_snomed_db.json")
        cls.generator = FHIRGenerator()
        cls.client = TestClient(app)
        
    def test_local_abbreviation_parsing(self):
        """Verify that local clinical rules resolve standard abbreviations to full names."""
        # 'loose motion' should map to 'Diarrhoea' locally
        loop_res = self.parser.rules.parse_locally("Pt c/o loose motion x 3 days")
        self.assertIn("Diarrhoea", loop_res["symptoms"])
        
        # 'sar dard' should map to 'Headache' locally
        head_res = self.parser.rules.parse_locally("sar dard ho raha hai")
        self.assertIn("Headache", head_res["symptoms"])

        # 'soboe' should map to 'Dyspnea on exertion' locally
        soboe_res = self.parser.rules.parse_locally("c/o SOBOE on walking")
        self.assertIn("Dyspnea on exertion", soboe_res["symptoms"])

    def test_terminology_resolution_local(self):
        """Verify that extracted concepts are mapped to correct SNOMED IDs in local fallback."""
        raw_extraction = {
            "symptoms": ["Diarrhoea", "Headache"],
            "diagnoses": ["Acid peptic disease"],
            "medications": [
                {"brand_name": "Dolo 650", "generic_guess": "Paracetamol", "dose": "650mg", "frequency": "twice daily"}
            ]
        }
        resolved = self.resolver.resolve_extraction(raw_extraction)
        
        # Check symptoms
        self.assertEqual(resolved["symptoms"][0]["concept_id"], "62315008") # Diarrhoea
        self.assertEqual(resolved["symptoms"][1]["concept_id"], "25064002") # Headache
        
        # Check diagnoses
        self.assertEqual(resolved["diagnoses"][0]["concept_id"], "367389006") # Acid peptic disease
        
        # Check medications
        self.assertEqual(resolved["medications"][0]["concept_id"], "322262002") # Paracetamol

    def test_fhir_bundle_generation(self):
        """Verify that valid FHIR OPConsultation Bundle is generated and passes validation."""
        resolved_profile = {
            "symptoms": [
                {"concept_id": "62315008", "display": "Diarrhoea (finding)", "original_query": "loose motion", "semantic_tag": "finding", "coded": True}
            ],
            "diagnoses": [
                {"concept_id": "367389006", "display": "Acid peptic disease (disorder)", "original_query": "APD", "semantic_tag": "disorder", "coded": True}
            ],
            "medications": [
                {"concept_id": "322262002", "display": "Paracetamol (substance)", "original_query": "Dolo 650", "semantic_tag": "substance", "dose": "650mg", "frequency": "twice daily", "coded": True}
            ]
        }
        bundle = self.generator.create_op_consultation_bundle(resolved_profile)
        
        # Check standard FHIR document bundle tags
        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["type"], "document")
        self.assertTrue(len(bundle["entry"]) > 0)
        
        # Composition must be the first entry
        self.assertEqual(bundle["entry"][0]["resource"]["resourceType"], "Composition")
        
    def test_health_check_endpoint(self):
        """Verify health check endpoint returns 200 status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        
    def test_api_auth_validation(self):
        """Verify API key verification rejects invalid keys and accepts valid ones."""
        # 1. Invalid API Key
        response_invalid = self.client.post(
            "/api/v1/parse",
            headers={"X-API-KEY": "invalid-key"},
            json={"text": "Pt c/o loose motion"}
        )
        self.assertEqual(response_invalid.status_code, 403)
        
        # 2. Valid API Key
        response_valid = self.client.post(
            "/api/v1/parse",
            headers={"X-API-KEY": "test-dev-key"},
            json={"text": "Pt c/o loose motion"}
        )
        self.assertEqual(response_valid.status_code, 200)
        bundle = response_valid.json()
        self.assertEqual(bundle["resourceType"], "Bundle")


if __name__ == "__main__":
    unittest.main()
