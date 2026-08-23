import os
import sys
import unittest
import asyncio
from fastapi.testclient import TestClient

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main import app
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

        # 'amavata' AYUSH concept
        ayush_res = self.parser.rules.parse_locally("Pt has h/o Amavata")
        self.assertIn("Amavata", ayush_res["symptoms"])

    def test_medication_dosage_extraction(self):
        """Verify that brand names, dosages, and frequencies are correctly extracted."""
        res = self.parser.rules.parse_locally("Dolo 650 BD and Pantocid 40 OD")
        meds = res["medications"]
        self.assertEqual(len(meds), 2)
        
        dolo = next((m for m in meds if "Dolo" in m["brand_name"]), None)
        self.assertIsNotNone(dolo)
        self.assertEqual(dolo["generic_guess"], "Paracetamol")
        self.assertEqual(dolo["dose"], "650mg")
        self.assertEqual(dolo["frequency"], "twice daily")

        panto = next((m for m in meds if "Pantocid" in m["brand_name"]), None)
        self.assertIsNotNone(panto)
        self.assertEqual(panto["generic_guess"], "Pantoprazole")
        self.assertEqual(panto["dose"], "40mg")
        self.assertEqual(panto["frequency"], "once daily")

    def test_terminology_resolution_local(self):
        """Verify that extracted concepts are mapped to correct SNOMED IDs in local fallback."""
        raw_extraction = {
            "symptoms": ["Diarrhoea", "Headache", "Amavata"],
            "diagnoses": ["Acid peptic disease"],
            "medications": [
                {"brand_name": "Dolo 650", "generic_guess": "Paracetamol", "dose": "650mg", "frequency": "twice daily"}
            ]
        }
        resolved = self.resolver.resolve_extraction(raw_extraction)
        
        # Check symptoms
        self.assertEqual(resolved["symptoms"][0]["concept_id"], "62315008")  # Diarrhoea
        self.assertEqual(resolved["symptoms"][1]["concept_id"], "25064002")  # Headache
        self.assertEqual(resolved["symptoms"][2]["concept_id"], "1221000189104")  # Amavata (AYUSH)
        self.assertTrue(resolved["symptoms"][2].get("ayush_extension"))
        
        # Check diagnoses
        self.assertEqual(resolved["diagnoses"][0]["concept_id"], "367389006")  # Acid peptic disease
        
        # Check medications
        self.assertEqual(resolved["medications"][0]["concept_id"], "322262002")  # Paracetamol

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
        
        # Ensure timestamp is valid ISO format
        self.assertTrue("T" in bundle["timestamp"])

    def test_health_check_endpoint(self):
        """Verify health check endpoint returns 200 status and service flags."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("services", data)
        
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
        self.assertEqual(bundle["type"], "document")

    def test_better_auth_flow(self):
        """Verify user registration, sign-in, and session retrieval."""
        import uuid
        test_email = f"test_doctor_{uuid.uuid4().hex[:6]}@clinic.in"
        test_password = "SecurePassword123!"

        # 1. Sign Up
        signup_res = self.client.post("/api/auth/sign-up", json={
            "name": "Dr. Test Specialist",
            "email": test_email,
            "password": test_password,
            "role": "doctor"
        })
        self.assertEqual(signup_res.status_code, 200)
        data = signup_res.json()
        self.assertIn("user", data)
        self.assertIn("session", data)
        token = data["session"]["token"]

        # 2. Get Session with Bearer Token
        sess_res = self.client.get("/api/auth/get-session", headers={
            "Authorization": f"Bearer {token}"
        })
        self.assertEqual(sess_res.status_code, 200)
        sess_data = sess_res.json()
        self.assertEqual(sess_data["user"]["email"], test_email)

        # 3. Sign In
        signin_res = self.client.post("/api/auth/sign-in", json={
            "email": test_email,
            "password": test_password
        })
        self.assertEqual(signin_res.status_code, 200)
        self.assertIn("session", signin_res.json())

    def test_dynamic_api_key_generation(self):
        """Verify creating a dynamic API Key and using it against /api/v1/parse."""
        import uuid
        test_email = f"clinic_admin_{uuid.uuid4().hex[:6]}@hospital.in"
        
        # 1. Register Clinic
        reg_res = self.client.post("/api/auth/sign-up", json={
            "name": "Apollo OPD Clinic",
            "email": test_email,
            "password": "Password456!",
            "role": "clinic_admin"
        })
        token = reg_res.json()["session"]["token"]

        # 2. Create Dynamic API Key
        key_res = self.client.post("/api/v1/api-keys", headers={
            "Authorization": f"Bearer {token}"
        }, json={"name": "Apollo EHR Production Key"})
        self.assertEqual(key_res.status_code, 200)
        new_key = key_res.json()["key_value"]
        self.assertTrue(new_key.startswith("sicce_"))

        # 3. List API Keys
        list_res = self.client.get("/api/v1/api-keys", headers={
            "Authorization": f"Bearer {token}"
        })
        self.assertEqual(list_res.status_code, 200)
        keys = list_res.json()["keys"]
        self.assertTrue(any(k["key_value"] == new_key for k in keys))

        # 4. Use Dynamic API Key on /api/v1/parse
        parse_res = self.client.post(
            "/api/v1/parse",
            headers={"X-API-KEY": new_key},
            json={"text": "Pt c/o loose motion x 3 days, AP+, Dolo 650 BD"}
        )
        self.assertEqual(parse_res.status_code, 200)
        self.assertEqual(parse_res.json()["resourceType"], "Bundle")

    def test_dpdp_phi_sanitizer(self):
        """Verify PHI Sanitizer scrubs Indian phone numbers, ABHA IDs, Aadhaar numbers, and names."""
        from nlp_parser import PHISanitizer
        
        sample_sensitive_note = (
            "Patient Mr. Rajesh Sharma, Phone: +91 9876543210, ABHA: 91-1234-5678-9012, "
            "Aadhaar: 1234 5678 9012, Email: rajesh@example.com c/o loose motion x 3 days, AP+, Dolo 650 BD"
        )
        sanitized = PHISanitizer.sanitize(sample_sensitive_note)
        
        # Verify direct identifiers are scrubbed
        self.assertNotIn("9876543210", sanitized)
        self.assertNotIn("91-1234-5678-9012", sanitized)
        self.assertNotIn("rajesh@example.com", sanitized)
        self.assertIn("[REDACTED_PHONE]", sanitized)
        self.assertIn("[REDACTED_ABHA]", sanitized)
        self.assertIn("[REDACTED_EMAIL]", sanitized)
        
        # Verify clinical terms are preserved
        self.assertIn("loose motion", sanitized)
        self.assertIn("Dolo 650", sanitized)

    def test_non_samd_metadata_and_dpdp_purge(self):
        """Verify Non-SaMD safety tags in FHIR bundle and test DPDP Section 12 Purge API."""
        import uuid
        test_email = f"compliance_doctor_{uuid.uuid4().hex[:6]}@clinic.in"
        
        # 1. Register and get token
        reg_res = self.client.post("/api/auth/sign-up", json={
            "name": "Dr. Compliance Audit",
            "email": test_email,
            "password": "Password789!",
            "role": "doctor"
        })
        token = reg_res.json()["session"]["token"]

        # 2. Test DPDP Cryptographic Purge API
        purge_res = self.client.post(
            "/api/v1/compliance/purge-records",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirmation": "PURGE_AUDIT_LOGS"}
        )
        self.assertEqual(purge_res.status_code, 200)
        purge_data = purge_res.json()
        self.assertEqual(purge_data["status"], "purged")
        self.assertTrue(purge_data["deletion_receipt"].startswith("DPDP-PURGE-"))

        # 3. Verify Non-SaMD tags in generated FHIR bundle
        parse_res = self.client.post(
            "/api/v1/parse",
            headers={"X-API-KEY": "test-dev-key"},
            json={"text": "Pt c/o loose motion x 3 days"}
        )
    def test_ddi_interaction_alert(self):
        """Verify that drug-drug interaction engine flags Norfloxacin + Pantocid chelation alert."""
        from nlp_parser import DDIEngine
        sample_meds = [
            {"brand_name": "Tab Norflox TZ", "generic_guess": "Norfloxacin + Tinidazole"},
            {"brand_name": "Tab Pantocid", "generic_guess": "Pantoprazole"}
        ]
        alerts = DDIEngine.check_interactions(sample_meds)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["severity"], "moderate")
        self.assertIn("Chelation", alerts[0]["title"])

    def test_vernacular_translation(self):
        """Verify that frequency instructions are translated into 5 Indian languages."""
        from nlp_parser import VernacularTranslator
        sample_meds = [
            {"brand_name": "Tab Dolo 650", "dose": "650mg", "frequency": "twice daily (BD)"}
        ]
        schedules = VernacularTranslator.generate_schedules(sample_meds)
        self.assertEqual(len(schedules), 1)
        trans = schedules[0]["translations"]
        self.assertIn("hi", trans)
        self.assertIn("mr", trans)
        self.assertIn("ta", trans)
        self.assertIn("te", trans)
        self.assertIn("bn", trans)
        self.assertIn("दिन में 2 बार", trans["hi"])

    def test_postman_collection_endpoint(self):
        """Verify that the Postman collection endpoint returns valid v2.1 JSON schema."""
        res = self.client.get("/api/v1/postman-collection")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["info"]["name"], "SICCE Clinical OCR & ABDM FHIR Gateway")
        self.assertEqual(len(data["item"]), 3)

    def test_billing_packages_and_balance(self):
        """Verify that billing packages and balance endpoints return valid structures."""
        # 1. Packages
        res_pack = self.client.get("/api/v1/billing/packages")
        self.assertEqual(res_pack.status_code, 200)
        pack_data = res_pack.json()
        self.assertEqual(pack_data["currency"], "INR")
        self.assertEqual(len(pack_data["packages"]), 3)
        self.assertEqual(pack_data["packages"][0]["id"], "pack_starter")

        # 2. Balance
        res_bal = self.client.get(
            "/api/v1/billing/balance",
            headers={"X-API-KEY": "test-dev-key"}
        )
        self.assertEqual(res_bal.status_code, 200)
        bal_data = res_bal.json()
        self.assertEqual(bal_data["credits_total"], 5000)
        self.assertEqual(bal_data["credits_remaining"], 4980)


if __name__ == "__main__":
    unittest.main()


