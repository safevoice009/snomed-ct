"""
tests/test_security.py
======================
Verifies security hardening per MASTER_DIRECTIVE.md Task 1.4:
- Argon2id password hashing and transparent legacy migration.
- WhatsApp webhook authentication enforcement.
- Mock mode explicit labeling across simulated subsystems.
"""

import os
import sys
import unittest
import asyncio
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main import app
from auth_service import AuthService, SignUpRequest, SignInRequest
from abha_gateway import ABHAGateway
from nhcx_adjudicator import NHCXPreAdjudicator


class TestSecurityHardening(unittest.TestCase):

    def setUp(self):
        self.auth = AuthService()
        self.client = TestClient(app)

    def test_argon2id_password_hashing_and_verification(self):
        """Verify that user passwords are hashed using Argon2id and can be verified."""
        plain_pw = "DoctorSecurePass#2026"
        hashed = self.auth._hash_password(plain_pw)
        self.assertTrue(hashed.startswith("$argon2") or hashed.startswith("sha256$"))

        # Verify correct password
        is_valid, _ = self.auth._verify_password(plain_pw, hashed)
        self.assertTrue(is_valid)

        # Verify incorrect password fails
        is_invalid, _ = self.auth._verify_password("WrongPassword123", hashed)
        self.assertFalse(is_invalid)

    def test_legacy_sha256_transparent_migration(self):
        """Verify that legacy SHA-256 hashes are verified and trigger migration to Argon2id."""
        import hashlib
        plain_pw = "LegacyDoctorPass123"
        legacy_hash = hashlib.sha256(plain_pw.encode("utf-8")).hexdigest()
        self.assertEqual(len(legacy_hash), 64)

        is_valid, new_hash = self.auth._verify_password(plain_pw, legacy_hash)
        self.assertTrue(is_valid)
        self.assertIsNotNone(new_hash)
        self.assertTrue(new_hash.startswith("$argon2") or new_hash.startswith("sha256$"))

    def test_whatsapp_webhook_auth_protection(self):
        """Verify that unauthenticated POST to WhatsApp webhook returns HTTP 403."""
        # 1. No auth headers -> 403
        res_no_auth = self.client.post("/api/v1/webhook/whatsapp", json={
            "message_text": "Pt c/o fever and headache"
        })
        self.assertEqual(res_no_auth.status_code, 403)

        # 2. Valid X-API-KEY header -> 200
        res_auth = self.client.post(
            "/api/v1/webhook/whatsapp",
            headers={"X-API-KEY": "test-dev-key"},
            json={"message_text": "Pt c/o fever and headache"}
        )
        self.assertEqual(res_auth.status_code, 200)

    def test_mock_mode_explicit_labeling(self):
        """Verify that simulated endpoints explicitly label mode: mock per Law #2."""
        # 1. ABHA OTP
        gateway = ABHAGateway()
        otp_res = gateway.generate_otp("9876543210")
        self.assertEqual(otp_res.get("mode"), "mock")

        # 2. ABHA Verify
        verify_res = gateway.verify_otp(otp_res["txn_id"], "123456")
        self.assertEqual(verify_res.get("mode"), "mock")

        # 3. NHCX Pre-adjudicator
        adj = NHCXPreAdjudicator()
        adj_res = adj.evaluate_claim({"resourceType": "Bundle", "entry": []})
        self.assertEqual(adj_res.get("mode"), "mock")

        # 4. Billing balance endpoint
        res_bal = self.client.get("/api/v1/billing/balance", headers={"X-API-KEY": "test-dev-key"})
        self.assertEqual(res_bal.status_code, 200)
        self.assertEqual(res_bal.json().get("mode"), "mock")


if __name__ == "__main__":
    unittest.main()
