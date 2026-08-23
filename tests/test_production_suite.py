"""
test_production_suite.py
Comprehensive integration and unit test suite for SICCE Production Enhancements:
- SQLite FTS5 Indian Drug Brand & Terminology Resolution
- CDSS Drug-Drug Interaction & Allergy Checker
- Voice Scribe Multi-Modal Engine
- NHCX Insurance Claim Formatter
- FastAPI Gateway Endpoints
"""

import os
import sys
import unittest
import json
from fastapi.testclient import TestClient

# Ensure snomed ct directory is on path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main import app
from terminology_resolver import TerminologyResolver
from cdss_engine import CDSSEngine
from nhcx_claim_generator import NHCXClaimGenerator

class TestSICCEProductionSuite(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.resolver = TerminologyResolver("clinical_knowledge.db")
        cls.cdss = CDSSEngine()
        cls.nhcx = NHCXClaimGenerator()
        cls.api_key = os.getenv("API_KEY", "test-dev-key")

    # --- 1. Terminology & Indian Brand Resolution Tests ---
    def test_indian_brand_resolution(self):
        """Verifies top Indian pharmaceutical brands resolve to correct generic & SNOMED CT IDs."""
        test_cases = [
            ("Augmentin 625", "372687004", "Amoxicillin and clavulanic acid"),
            ("Pan-D", "715879001", "Pantoprazole and domperidone"),
            ("Telma 40", "387532007", "Telmisartan"),
            ("Dolo 650", "387517004", "Paracetamol"),
            ("Shelcal 500", "715879001", "Calcium and vitamin D3")
        ]
        for query, expected_snomed, expected_generic in test_cases:
            match = self.resolver.resolve_term(query)
            self.assertIsNotNone(match, f"Failed to resolve {query}")
            self.assertEqual(match.get("concept_id"), expected_snomed)
            self.assertIn(expected_generic.lower(), match.get("preferred_name", "").lower())

    def test_hindi_symptom_resolution(self):
        """Verifies colloquial Hindi/Hinglish symptoms resolve to standard clinical findings."""
        symptoms = [
            ("khansi", "49727002", "Cough"),
            ("sar dard", "25064002", "Headache"),
            ("pet kharab", "62315008", "Diarrhoea"),
            ("bukhar", "386661006", "Fever")
        ]
        for term, expected_id, expected_name in symptoms:
            match = self.resolver.resolve_term(term)
            self.assertIsNotNone(match, f"Failed to resolve {term}")
            self.assertEqual(match.get("concept_id"), expected_id)
            self.assertIn(expected_name.lower(), match.get("preferred_name", "").lower())

    # --- 2. CDSS Drug Interaction & Allergy Tests ---
    def test_cdss_critical_ddi_sildenafil_nitrate(self):
        """Verifies lethal PDE5 + Nitrate interaction is flagged as CRITICAL."""
        meds = [{"display": "Sildenafil 50mg"}, {"display": "Nitroglycerin 0.4mg"}]
        report = self.cdss.evaluate_safety(medications=meds)
        self.assertEqual(report["status"], "CRITICAL_ALERTS_DETECTED")
        self.assertTrue(any("Hypotension" in a["title"] for a in report["alerts"]))

    def test_cdss_critical_ddi_warfarin_nsaid(self):
        """Verifies Warfarin + Combiflam / NSAID bleeding risk is flagged."""
        meds = [{"display": "Warfarin 5mg"}, {"display": "Combiflam"}]
        report = self.cdss.evaluate_safety(medications=meds)
        self.assertEqual(report["status"], "CRITICAL_ALERTS_DETECTED")
        self.assertTrue(any("Bleeding" in a["title"] for a in report["alerts"]))

    def test_cdss_allergy_penicillin_cross_reactivity(self):
        """Verifies Penicillin allergy flags Augmentin (Amoxicillin/Clavulanate)."""
        meds = [{"display": "Augmentin 625 Duo", "generic_name": "Amoxicillin and clavulanic acid"}]
        report = self.cdss.evaluate_safety(medications=meds, patient_allergies=["penicillin"])
        self.assertEqual(report["status"], "CRITICAL_ALERTS_DETECTED")
        self.assertTrue(any(a["type"] == "ALLERGY_CONTRAINDICATION" for a in report["alerts"]))

    def test_cdss_duplicate_therapy(self):
        """Verifies duplicate PPI prescription triggers a warning."""
        meds = [{"display": "Pan 40"}, {"display": "Omez 20"}]
        report = self.cdss.evaluate_safety(medications=meds)
        self.assertEqual(report["status"], "WARNINGS_PRESENT")
        self.assertTrue(any(a["type"] == "DUPLICATE_THERAPY" for a in report["alerts"]))

    # --- 3. NHCX Claim Formatter Tests ---
    def test_nhcx_claim_bundle_generation(self):
        """Verifies generation of a compliant NHCX Claim bundle with ICD-10 codes."""
        # Simulated consultation bundle
        mock_consultation = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Condition",
                        "code": {
                            "coding": [{"system": "http://snomed.info/sct", "code": "38341003", "display": "Hypertension (disorder)"}]
                        }
                    }
                }
            ]
        }
        claim_bundle = self.nhcx.generate_claim_bundle(mock_consultation)
        self.assertEqual(claim_bundle["resourceType"], "Bundle")
        
        # Verify Claim Resource
        claim_entry = claim_bundle["entry"][0]["resource"]
        self.assertEqual(claim_entry["resourceType"], "Claim")
        self.assertEqual(claim_entry["use"], "claim")
        
        # Verify ICD-10 mapping for Hypertension (I10)
        diag = claim_entry["diagnosis"][0]["diagnosisCodeableConcept"]["coding"]
        icd_code = next(c["code"] for c in diag if "icd-10" in c["system"])
        self.assertEqual(icd_code, "I10")

    # --- 4. FastAPI Endpoint Integration Tests ---
    def test_endpoint_health(self):
        """Verifies /health endpoint status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["status"], ["healthy", "degraded_unseeded_terminology"])
        self.assertEqual(data["version"], "2.0.0")

    def test_endpoint_parse_with_cdss(self):
        """Verifies POST /api/v1/parse returns FHIR bundle and CDSS evaluation."""
        headers = {"X-API-KEY": self.api_key, "X-STUDIO-CLIENT": "true"}
        payload = {
            "text": "Pt c/o severe khansi x 3 days, known HTN. Rx: 1. Tab Levocet M 1 HS, 2. Tab Telma 40 1 OD morning, 3. Dolo 650 TDS.",
            "patient_allergies": []
        }
        response = self.client.post("/api/v1/parse", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("bundle", data)
        self.assertIn("cdss", data)
        self.assertIn("nhcx_bundle", data)
        self.assertEqual(data["cdss"]["status"], "CLEAR")

    def test_endpoint_check_interactions(self):
        """Verifies POST /api/v1/check-interactions."""
        headers = {"X-API-KEY": self.api_key}
        payload = {
            "medications": [{"display": "Sildenafil"}, {"display": "Nitroglycerin"}],
            "patient_allergies": []
        }
        response = self.client.post("/api/v1/check-interactions", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "CRITICAL_ALERTS_DETECTED")

    # --- 5. Enterprise Health Moat Tests (SICCE Phase 2) ---
    def test_nhcx_pre_adjudication_engine(self):
        """Verifies NHCX Claim Pre-Adjudication scoring and IRDAI necessity checks."""
        headers = {"X-API-KEY": self.api_key, "X-STUDIO-CLIENT": "true"}
        claim_bundle = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Claim",
                        "id": "CLM-TEST-001",
                        "insurance": [{"coverage": {"display": "National Insurance - POL-123"}}],
                        "provider": {"display": "Apollo Clinic"},
                        "diagnosis": [{"diagnosisCodeableConcept": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "I10", "display": "Essential hypertension"}]}}],
                        "item": [{"net": {"value": 500}}, {"net": {"value": 450}}],
                        "total": {"value": 950}
                    }
                }
            ]
        }
        response = self.client.post("/api/v1/nhcx/pre-adjudicate", json={"claim_bundle": claim_bundle}, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data["score"], 80)
        self.assertEqual(data["status"], "READY_FOR_AUTO_ADJUDICATION")

    def test_abdm_m1_m2_abha_gateway(self):
        """Verifies ABHA M1 OTP Generation & Verification and M2 Care Context Linkage."""
        headers = {"X-API-KEY": self.api_key}
        # 1. Generate OTP
        gen_res = self.client.post("/api/v1/abdm/abha/generate-otp", json={"identifier": "9876543210", "auth_type": "MOBILE_OTP"}, headers=headers)
        self.assertEqual(gen_res.status_code, 200)
        txn_id = gen_res.json()["txn_id"]
        
        # 2. Verify OTP
        ver_res = self.client.post("/api/v1/abdm/abha/verify-otp", json={"txn_id": txn_id, "otp": "123456", "preferred_abha_name": "rahul.verma"}, headers=headers)
        self.assertEqual(ver_res.status_code, 200)
        profile = ver_res.json()["profile"]
        self.assertTrue(profile["abha_number"].startswith("91-"))
        self.assertEqual(profile["abha_address"], "rahul.verma@abdm")

    def test_whatsapp_clinical_webhook(self):
        """Verifies WhatsApp clinical webhook message processing."""
        payload = {
            "from_phone": "+919876543210",
            "clinic_name": "Apollo Clinic",
            "doctor_name": "Dr. Rajesh Sharma",
            "message_text": "Pt c/o severe khansi & fever. Tab Pantocid 40 OD, Tab Dolo 650 BD."
        }
        response = self.client.post(
            "/api/v1/webhook/whatsapp",
            headers={"X-API-KEY": self.api_key},
            json=payload
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message_body", data)
        self.assertIn("SNOMED CT", data["message_body"])
        self.assertIn("PATIENT DOSAGE CARD", data["message_body"])

if __name__ == "__main__":
    unittest.main()
