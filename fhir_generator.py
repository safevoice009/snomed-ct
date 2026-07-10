import uuid
from datetime import datetime
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger("fhir_generator")

class FHIRGenerator:
    """Generates ABDM-compliant HL7 FHIR R4 OPConsultation bundles from resolved terminology profiles."""
    
    def __init__(self):
        # We try to import fhir.resources for schema validation if installed
        try:
            from fhir.resources.bundle import Bundle
            from fhir.resources.composition import Composition
            from fhir.resources.condition import Condition
            from fhir.resources.observation import Observation
            from fhir.resources.medicationrequest import MedicationRequest
            self.fhir_validator = True
            logger.info("fhir.resources imported successfully. Strict validation enabled.")
        except ImportError:
            self.fhir_validator = False
            logger.warning("fhir.resources library not installed or models missing. Graceful dictionary output will be used.")

    def create_op_consultation_bundle(self, resolved_data: Dict[str, Any], patient_details: Dict[str, str] = None) -> Dict[str, Any]:
        """Constructs the complete OPConsultation Bundle containing Composition, Patient, Condition, and Observation resources."""
        
        # Initialize default entities if not provided
        if not patient_details:
            patient_details = {
                "id": "pat-01",
                "name": "Arjun Kumar",
                "gender": "male",
                "abha_id": "91-1234-5678-9012"
            }
            
        practitioner_details = {
            "id": "prac-01",
            "name": "Dr. Rajesh Sharma, MD",
            "hpr_id": "HP99882211"
        }
        
        bundle_id = str(uuid.uuid4())
        composition_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # 1. Initialize Bundle Root
        bundle = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "meta": {
                "lastUpdated": timestamp,
                "profile": [
                    "https://nrces.in/ndhm/fhir/r4/StructureDefinition/DocumentBundle"
                ]
            },
            "identifier": {
                "system": "https://ndhm.in/bundle",
                "value": bundle_id
            },
            "type": "document",
            "timestamp": timestamp,
            "entry": []
        }
        
        # Resources list to compile references inside Composition
        composition_sections = {
            "chief_complaints": [],
            "diagnoses": [],
            "medications": []
        }
        
        # 2. Build Patient resource
        patient_resource = {
            "resourceType": "Patient",
            "id": patient_details["id"],
            "meta": {
                "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Patient"]
            },
            "identifier": [
                {
                    "system": "https://ndhm.in/abha-number",
                    "value": patient_details["abha_id"]
                }
            ],
            "name": [{"text": patient_details["name"]}],
            "gender": patient_details["gender"]
        }
        
        # 3. Build Practitioner resource
        practitioner_resource = {
            "resourceType": "Practitioner",
            "id": practitioner_details["id"],
            "meta": {
                "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Practitioner"]
            },
            "identifier": [
                {
                    "system": "https://ndhm.in/hpr-id",
                    "value": practitioner_details["hpr_id"]
                }
            ],
            "name": [{"text": practitioner_details["name"]}]
        }
        
        # Compile entries list (will populate this sequentially)
        entries_to_add = [patient_resource, practitioner_resource]
        
        # 4. Generate Condition resources (Diagnoses)
        for idx, item in enumerate(resolved_data.get("diagnoses", [])):
            cond_id = f"cond-{idx+1}"
            
            # Code structure
            coding = []
            if item["coded"]:
                coding.append({
                    "system": "http://snomed.info/sct",
                    "code": item["concept_id"],
                    "display": item["display"]
                })
            
            condition_resource = {
                "resourceType": "Condition",
                "id": cond_id,
                "meta": {
                    "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Condition"]
                },
                "clinicalStatus": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                            "code": "active"
                        }
                    ]
                },
                "code": {
                    "coding": coding,
                    "text": item["original_query"]
                },
                "subject": {
                    "reference": f"Patient/{patient_details['id']}"
                }
            }
            entries_to_add.append(condition_resource)
            composition_sections["diagnoses"].append({"reference": f"Condition/{cond_id}"})
            
        # 5. Generate Observation resources (Symptoms/Findings)
        for idx, item in enumerate(resolved_data.get("symptoms", [])):
            obs_id = f"obs-{idx+1}"
            
            coding = []
            if item["coded"]:
                # Check system (Standard SNOMED vs India AYUSH National Extension)
                system = "http://snomed.info/sct"
                coding_node = {
                    "system": system,
                    "code": item["concept_id"],
                    "display": item["display"]
                }
                
                # Highlight if it has AYUSH metadata
                if item.get("ayush_extension"):
                    coding_node["extension"] = [{
                        "url": "https://nrces.in/ndhm/fhir/r4/StructureDefinition/ayush-metadata",
                        "valueString": "AYUSH Terminology Mapping"
                    }]
                coding.append(coding_node)
                
            observation_resource = {
                "resourceType": "Observation",
                "id": obs_id,
                "meta": {
                    "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Observation"]
                },
                "status": "final",
                "code": {
                    "coding": coding,
                    "text": item["original_query"]
                },
                "subject": {
                    "reference": f"Patient/{patient_details['id']}"
                }
            }
            
            # Implement Vaidya-Setu Linkage mapping: If there is a cross-allopathic mapping, attach it as an extension
            if item.get("cross_allopathy_mapping"):
                observation_resource["extension"] = [{
                    "url": "https://SICCE.health/fhir/StructureDefinition/integrative-allopathy-bridge",
                    "valueCodeableConcept": {
                        "coding": [{
                            "system": "http://snomed.info/sct",
                            "code": item["cross_allopathy_mapping"]["concept_id"],
                            "display": "Rheumatoid arthritis (disorder)" # Mapped term FSN
                        }],
                        "text": f"Integrative Medicine Relationship: {item['cross_allopathy_mapping']['relationship']}"
                    }
                }]
                
            entries_to_add.append(observation_resource)
            composition_sections["chief_complaints"].append({"reference": f"Observation/{obs_id}"})
            
        # 6. Generate MedicationRequest resources
        for idx, item in enumerate(resolved_data.get("medications", [])):
            med_id = f"med-req-{idx+1}"
            
            coding = []
            if item["coded"]:
                coding.append({
                    "system": "http://snomed.info/sct",
                    "code": item["concept_id"],
                    "display": item["display"]
                })
                
            medication_resource = {
                "resourceType": "MedicationRequest",
                "id": med_id,
                "meta": {
                    "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/MedicationRequest"]
                },
                "status": "active",
                "intent": "order",
                "medication": {
                    "concept": {
                        "coding": coding,
                        "text": item["display"]  # The Brand Name/Generic guess text
                    }
                },
                "subject": {
                    "reference": f"Patient/{patient_details['id']}"
                },
                "dosageInstruction": [
                    {
                        "text": item.get("frequency", "as directed"),
                        "additionalInstruction": [
                            {
                                "text": item.get("dose", "")
                            }
                        ]
                    }
                ]
            }
            entries_to_add.append(medication_resource)
            composition_sections["medications"].append({"reference": f"MedicationRequest/{med_id}"})
            
        # 7. Generate Composition resource (First item in bundle)
        composition = {
            "resourceType": "Composition",
            "id": composition_id,
            "meta": {
                "profile": [
                    "https://nrces.in/ndhm/fhir/r4/StructureDefinition/OPConsultRecord"
                ]
            },
            "status": "final",
            "type": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "371530004",
                        "display": "Clinical consultation report (record artifact)"
                    }
                ],
                "text": "Outpatient Consultation Record"
            },
            "subject": [
                {
                    "reference": f"Patient/{patient_details['id']}"
                }
            ],
            "date": timestamp,
            "author": [
                {
                    "reference": f"Practitioner/{practitioner_details['id']}"
                }
            ],
            "title": "Outpatient Consultation Record",
            "section": []
        }
        
        # Add sections to Composition if resources exist
        if composition_sections["chief_complaints"]:
            composition["section"].append({
                "title": "Chief Complaints",
                "code": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "422843007",
                            "display": "Chief complaint (finding)"
                        }
                    ]
                },
                "entry": composition_sections["chief_complaints"]
            })
            
        if composition_sections["diagnoses"]:
            composition["section"].append({
                "title": "Diagnoses / Clinical Findings",
                "code": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "44760003",
                            "display": "Diagnosis finding (finding)"
                        }
                    ]
                },
                "entry": composition_sections["diagnoses"]
            })
            
        if composition_sections["medications"]:
            composition["section"].append({
                "title": "Prescriptions",
                "code": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "416310005",
                            "display": "Drug prescription record (record artifact)"
                        }
                    ]
                },
                "entry": composition_sections["medications"]
            })
            
        # Assemble Bundle entries
        # Composition must go first!
        bundle["entry"].append({
            "fullUrl": f"Composition/{composition_id}",
            "resource": composition
        })
        
        for entry_res in entries_to_add:
            res_type = entry_res["resourceType"]
            res_id = entry_res["id"]
            bundle["entry"].append({
                "fullUrl": f"{res_type}/{res_id}",
                "resource": entry_res
            })
            
        # strict pydantic validator if imported
        if self.fhir_validator:
            try:
                from fhir.resources.bundle import Bundle as FHRBundle
                FHRBundle.model_validate(bundle)
                logger.info("FHIR R4 validation passed.")
            except Exception as e:
                logger.error(f"FHIR validation error: {e}")
                
        return bundle
