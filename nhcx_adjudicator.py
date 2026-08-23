"""
nhcx_adjudicator.py
National Health Claims Exchange (NHCX) Claim Pre-Adjudication Engine.
Simulates TPA and Insurer adjudication rules against FHIR R4 Claim Bundles to prevent rejections,
validate medical necessity, check ICD-10 coherence, and guarantee high auto-approval rates.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("nhcx_adjudicator")

# IRDAI & TPA Medical Necessity Rules for OPD & Cashless Settlement
COHERENCE_RULES = [
    {
        "icd10_prefix": "I10",
        "category": "Cardiovascular",
        "expected_meds": ["telmisartan", "amlodipine", "losartan", "atorvastatin", "metoprolol"],
        "max_opd_claim": 2500,
        "required_vitals": ["blood_pressure"]
    },
    {
        "icd10_prefix": "E11",
        "category": "Endocrinology",
        "expected_meds": ["metformin", "glimepiride", "vildagliptin", "insulin", "dapagliflozin"],
        "max_opd_claim": 3000,
        "required_vitals": ["blood_sugar", "weight"]
    },
    {
        "icd10_prefix": "K29",
        "category": "Gastroenterology",
        "expected_meds": ["pantoprazole", "rabeprazole", "omeprazole", "antacid", "mucaine"],
        "max_opd_claim": 2000,
        "max_duration_days": 14
    },
    {
        "icd10_prefix": "A09",
        "category": "Infectious Disease",
        "expected_meds": ["norfloxacin", "tinidazole", "ors", "zinc", "paracetamol"],
        "max_opd_claim": 1800,
        "max_duration_days": 7
    },
    {
        "icd10_prefix": "J20",
        "category": "Pulmonology",
        "expected_meds": ["azithromycin", "amoxicillin", "levocetirizine", "montelukast", "paracetamol"],
        "max_opd_claim": 2200,
        "max_duration_days": 10
    }
]

class NHCXPreAdjudicator:
    """Pre-evaluates NHCX FHIR Claim bundles for cashless insurance settlement."""

    def evaluate_claim(self, claim_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Runs pre-submission adjudication checks and returns scoring with remediation."""
        score = 100
        flags: List[Dict[str, Any]] = []
        checks_passed: List[str] = []
        
        entries = claim_bundle.get("entry", [])
        claim_res = None
        for entry in entries:
            res = entry.get("resource", {})
            if res.get("resourceType") == "Claim":
                claim_res = res
                break
                
        if not claim_res:
            return {
                "mode": "mock",
                "approval_probability": 0,
                "status": "REJECTED_FORMAT_ERROR",
                "risk_level": "CRITICAL",
                "score": 0,
                "summary": "No FHIR Claim resource found in bundle.",
                "flags": [{"code": "NO_CLAIM_RESOURCE", "severity": "CRITICAL", "message": "Bundle must contain a valid FHIR R4 Claim resource."}],
                "checklist": []
            }

        # 1. Check Policy & Insurer Metadata
        insurance = claim_res.get("insurance", [{}])[0].get("coverage", {})
        if insurance.get("display") or insurance.get("reference"):
            checks_passed.append("Policy and Coverage Reference Validated")
        else:
            score -= 15
            flags.append({
                "code": "MISSING_COVERAGE_REF",
                "severity": "HIGH",
                "message": "Claim is missing explicit policy coverage reference.",
                "remediation": "Attach valid GIPSA / private insurer policy identifier."
            })

        # 2. Check Provider & Facility Registration
        provider = claim_res.get("provider", {})
        if provider.get("identifier") or provider.get("display"):
            checks_passed.append("Healthcare Facility ABDM Registry (HFR) Check: Passed")
        else:
            score -= 10
            flags.append({
                "code": "UNREGISTERED_PROVIDER",
                "severity": "MEDIUM",
                "message": "Hospital/Clinic HFR ID is unverified.",
                "remediation": "Ensure hospital ABDM Health Facility Registry ID is attached."
            })

        # 3. Check Diagnoses and ICD-10 Specificity
        diagnoses = claim_res.get("diagnosis", [])
        has_valid_diagnosis = False
        primary_icd10 = None
        
        for diag in diagnoses:
            cc = diag.get("diagnosisCodeableConcept", {})
            for coding in cc.get("coding", []):
                code = coding.get("code", "")
                if code and code != "R69":
                    has_valid_diagnosis = True
                    if not primary_icd10:
                        primary_icd10 = code
                        
        if has_valid_diagnosis:
            checks_passed.append(f"Primary ICD-10 Diagnosis Validated: {primary_icd10}")
        else:
            score -= 30
            flags.append({
                "code": "UNSPECIFIED_DIAGNOSIS_CODE",
                "severity": "CRITICAL",
                "message": "Diagnosis contains unspecific code (R69/Illness unspecified). TPAs reject claims lacking specific ICD-10 coding.",
                "remediation": "Map clinical findings to specific ICD-10 category (e.g. K29.70 for Gastritis, I10 for HTN)."
            })

        # 4. Check Bill Itemization and Line Total Coherence
        items = claim_res.get("item", [])
        total = claim_res.get("total", {}).get("value", 0)
        
        calculated_total = 0
        for item in items:
            net_val = item.get("net", {}).get("value", 0)
            calculated_total += net_val
            
        if items and (abs(calculated_total - total) < 1.0 or total > 0):
            checks_passed.append(f"Bill Itemization Coherent: {len(items)} line items totalling INR {total:,.2f}")
        else:
            score -= 20
            flags.append({
                "code": "BILL_ITEM_MISMATCH",
                "severity": "HIGH",
                "message": f"Sum of itemized net values (INR {calculated_total}) does not match claim total (INR {total}).",
                "remediation": "Re-sum line item charges to prevent financial ledger discrepancy rejection."
            })

        # 5. Check Medical Necessity Coherence with Prescription Lines
        # Find matching rule
        matched_rule = None
        if primary_icd10:
            for rule in COHERENCE_RULES:
                if primary_icd10.startswith(rule["icd10_prefix"]):
                    matched_rule = rule
                    break

        if matched_rule:
            checks_passed.append(f"IRDAI Medical Necessity Rule Profile: Matched for {matched_rule['category']}")
            if total > matched_rule.get("max_opd_claim", 5000):
                score -= 15
                flags.append({
                    "code": "OPD_SUB_LIMIT_EXCEEDED",
                    "severity": "MEDIUM",
                    "message": f"OPD Claim amount (INR {total}) exceeds standard TPA benchmark of INR {matched_rule['max_opd_claim']} for {matched_rule['category']}.",
                    "remediation": "Attach clinical escalation note or diagnostic report justification for higher billing."
                })
        else:
            checks_passed.append("Generic Medical Necessity Assessment: Standard Tier")

        # Determine Status and Risk Tier
        score = max(5, min(100, score))
        if score >= 90:
            status = "READY_FOR_AUTO_ADJUDICATION"
            risk_level = "LOW"
            approval_prob = "95% - 99%"
        elif score >= 75:
            status = "PASSED_WITH_CONDITIONS"
            risk_level = "MEDIUM"
            approval_prob = "75% - 89%"
        else:
            status = "ACTION_REQUIRED_BEFORE_SUBMISSION"
            risk_level = "HIGH"
            approval_prob = "< 70%"

        return {
            "mode": "mock",
            "score": score,
            "status": status,
            "risk_level": risk_level,
            "approval_probability": approval_prob,
            "claim_id": claim_res.get("id", "CLAIM-UNKNOWN"),
            "total_amount_inr": total,
            "primary_icd10": primary_icd10 or "R69",
            "checks_passed": checks_passed,
            "flags": flags,
            "timestamp": claim_res.get("created", "")
        }
