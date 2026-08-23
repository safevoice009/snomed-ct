"""
nhcx_claim_generator.py
National Health Claims Exchange (NHCX) & ABDM Compliant Insurance Claim Formatter.
Converts structured clinical consultations into standard FHIR R4 Claim bundles with ICD-10-CM coding.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("nhcx_claim_generator")

# Standard Clinical Diagnosis to ICD-10-CM Mapping Catalog
ICD10_DIAGNOSIS_CATALOG = {
    "hypertension": {"code": "I10", "display": "Essential (primary) hypertension"},
    "essential hypertension": {"code": "I10", "display": "Essential (primary) hypertension"},
    "diabetes mellitus": {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications"},
    "type 2 diabetes": {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications"},
    "t2dm": {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications"},
    "acute gastroenteritis": {"code": "A09", "display": "Infectious gastroenteritis and colitis, unspecified"},
    "gastroenteritis": {"code": "A09", "display": "Infectious gastroenteritis and colitis, unspecified"},
    "acute bronchitis": {"code": "J20.9", "display": "Acute bronchitis, unspecified"},
    "bronchitis": {"code": "J20.9", "display": "Acute bronchitis, unspecified"},
    "allergic rhinitis": {"code": "J30.9", "display": "Allergic rhinitis, unspecified"},
    "asthma": {"code": "J45.909", "display": "Unspecified asthma, uncomplicated"},
    "pneumonia": {"code": "J18.9", "display": "Pneumonia, unspecified organism"},
    "sinusitis": {"code": "J01.90", "display": "Acute sinusitis, unspecified"},
    "dengue fever": {"code": "A90", "display": "Dengue fever [classical dengue]"},
    "dengue": {"code": "A90", "display": "Dengue fever [classical dengue]"},
    "malaria": {"code": "B54", "display": "Unspecified malaria"},
    "typhoid fever": {"code": "A01.00", "display": "Typhoid fever, unspecified"},
    "typhoid": {"code": "A01.00", "display": "Typhoid fever, unspecified"},
    "covid-19": {"code": "U07.1", "display": "COVID-19"},
    "anemia": {"code": "D64.9", "display": "Anemia, unspecified"},
    "hypothyroidism": {"code": "E03.9", "display": "Hypothyroidism, unspecified"},
    "gerd": {"code": "K21.9", "display": "Gastro-esophageal reflux disease without esophagitis"},
    "gastritis": {"code": "K29.70", "display": "Gastritis, unspecified, without bleeding"}
}

class NHCXClaimGenerator:
    """Generates ABDM/NHCX compliant FHIR R4 Claim Bundles."""

    def resolve_icd10(self, diagnosis_name: str) -> Dict[str, str]:
        """Resolves diagnostic phrase to standard ICD-10-CM code."""
        clean = diagnosis_name.strip().lower()
        if clean in ICD10_DIAGNOSIS_CATALOG:
            return ICD10_DIAGNOSIS_CATALOG[clean]
        for key, val in ICD10_DIAGNOSIS_CATALOG.items():
            if key in clean or clean in key:
                return val
        # Default unclassified clinical diagnosis
        return {"code": "R69", "display": f"Illness, unspecified ({diagnosis_name})"}

    def generate_claim_bundle(
        self,
        consultation_bundle: Dict[str, Any],
        patient_info: Optional[Dict[str, Any]] = None,
        policy_info: Optional[Dict[str, Any]] = None,
        bill_items: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Wraps consultation and generates a standard NHCX FHIR Claim resource bundle."""
        patient_info = patient_info or {}
        policy_info = policy_info or {
            "insurer_id": "GIPSA-001",
            "insurer_name": "National Insurance Co. Ltd.",
            "policy_number": "POL-2026-987654",
            "sum_insured": 500000
        }
        bill_items = bill_items or [
            {"service": "OPD Consultation & Clinical Coding", "unit_price": 500, "quantity": 1},
            {"service": "Pharmacy Dispensation (Prescribed Medications)", "unit_price": 450, "quantity": 1}
        ]

        claim_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Extract diagnoses from bundle
        diagnoses_list = []
        diag_sequence = 1
        for entry in consultation_bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Condition":
                codings = resource.get("code", {}).get("coding") or []
                code_obj = codings[0] if codings else {}
                display_text = code_obj.get("display") or resource.get("code", {}).get("text", "Condition")
                snomed_code = code_obj.get("code", "Unknown")
                
                icd = self.resolve_icd10(display_text)
                diagnoses_list.append({
                    "sequence": diag_sequence,
                    "diagnosisCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                                "code": icd["code"],
                                "display": icd["display"]
                            },
                            {
                                "system": "http://snomed.info/sct",
                                "code": snomed_code,
                                "display": display_text
                            }
                        ],
                        "text": display_text
                    }
                })
                diag_sequence += 1

        if not diagnoses_list:
            diagnoses_list.append({
                "sequence": 1,
                "diagnosisCodeableConcept": {
                    "coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "R69", "display": "Illness, unspecified"}],
                    "text": "General Medical Consultation"
                }
            })

        # Calculate Total
        total_amount = sum(item["unit_price"] * item["quantity"] for item in bill_items)
        
        # Itemized lines
        claim_items = []
        for idx, item in enumerate(bill_items, start=1):
            claim_items.append({
                "sequence": idx,
                "productOrService": {
                    "coding": [
                        {
                            "system": "https://nrces.in/ndhm/fhir/r4/CodeSystem/ndhm-billing-codes",
                            "code": f"BILL-00{idx}",
                            "display": item["service"]
                        }
                    ],
                    "text": item["service"]
                },
                "unitPrice": {
                    "value": float(item["unit_price"]),
                    "currency": "INR"
                },
                "quantity": {
                    "value": item["quantity"]
                },
                "net": {
                    "value": float(item["unit_price"] * item["quantity"]),
                    "currency": "INR"
                }
            })

        # Construct FHIR Claim Resource
        claim_resource = {
            "resourceType": "Claim",
            "id": claim_id,
            "meta": {
                "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Claim"]
            },
            "identifier": [
                {
                    "system": "https://nhcx.gov.in/claim-identifiers",
                    "value": f"CLAIM-IND-{claim_id[:8].upper()}"
                }
            ],
            "status": "active",
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                        "code": "professional",
                        "display": "Professional / OPD Consultation"
                    }
                ]
            },
            "use": "claim",
            "patient": {
                "reference": "Patient/demo-patient",
                "display": patient_info.get("name", "Patient Vikram Mehta")
            },
            "created": timestamp,
            "insurer": {
                "identifier": {"value": policy_info["insurer_id"]},
                "display": policy_info["insurer_name"]
            },
            "provider": {
                "reference": "Practitioner/doctor-01",
                "display": "Dr. S. Sharma, MBBS, MD (ABDM Registered)"
            },
            "priority": {
                "coding": [{"code": "normal", "display": "Standard Cashless Processing"}]
            },
            "insurance": [
                {
                    "sequence": 1,
                    "focal": True,
                    "coverage": {
                        "display": f"Policy #{policy_info['policy_number']} - Sum Insured: ₹{policy_info['sum_insured']:,}"
                    }
                }
            ],
            "diagnosis": diagnoses_list,
            "item": claim_items,
            "total": {
                "value": float(total_amount),
                "currency": "INR"
            }
        }

        # Return full NHCX Bundle
        return {
            "resourceType": "Bundle",
            "id": f"nhcx-bundle-{claim_id}",
            "meta": {
                "versionId": "1",
                "lastUpdated": timestamp,
                "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/DocumentBundle"]
            },
            "type": "collection",
            "timestamp": timestamp,
            "entry": [
                {"fullUrl": f"urn:uuid:{claim_id}", "resource": claim_resource},
                *consultation_bundle.get("entry", [])
            ]
        }
